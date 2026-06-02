# stdio 模式详解

## 一、传输原理

stdio（标准输入/输出）是 MCP 最基础的传输方式。服务端作为**子进程**启动，
客户端通过进程的 **stdin 发送** JSON-RPC 消息，通过 **stdout 接收** JSON-RPC 响应。

```
┌──────────────────┐                    ┌──────────────────┐
│   MCP Client     │                    │   MCP Server     │
│                  │    subprocess      │                  │
│  stdio_client    │─── (server.py) ───→│  StdioServer     │
│                  │                    │                  │
│                  │  ─── stdin ──────→ │                  │
│                  │  ←── stdout ────── │                  │
│                  │  ←── stderr (log)  │                  │
└──────────────────┘                    └──────────────────┘
```

### 数据格式

所有消息采用 **NDJSON**（Newline-Delimited JSON）格式：每行一个完整的 JSON 对象。

```
→ {"jsonrpc":"2.0","id":1,"method":"tools/list"}
← {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
→ {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{...}}
← {"jsonrpc":"2.0","id":2,"result":{"content":[...]}}
```

**关键约定**：
- **stdin/stdout**：JSON-RPC 通信（每行一个 JSON）
- **stderr**：服务端日志（不受协议约束，人类可读）

## 二、代码解读

### 服务端 (`src/stdio/server.py`)

```python
# 1. 创建 Server 实例 —— 声明服务端身份和能力
server = Server("mcp-demo-stdio")

# 2. 注册请求处理器 —— 每个 MCP 方法对应一个 handler（装饰器风格）
@server.list_tools()
async def handle_list_tools() -> types.ListToolsResult:
    return types.ListToolsResult(tools=DEMO_TOOLS)

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    try:
        return dispatch_tool(name, arguments or {})
    except Exception as error:
        msg = str(error)
        return [types.TextContent(type="text", text=f"错误: {msg}")]

# 3. 使用 StdioServerTransport 启动服务
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-demo-stdio",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
```

**设计要点**：
- `@server.list_tools()` 和 `@server.call_tool()` 装饰器是 Pythonic 的 handler 注册方式
- `stdio_server()` 封装了 stdin/stdout 的读写，开发者无需关心底层管道
- stderr 日志使用 Python `logging` 模块（因为 stdout 被协议占用）

### 客户端 (`src/stdio/client.py`)

```python
# 1. 创建 stdio transport —— 指定如何启动服务端
server_params = {
    "command": "python",
    "args": ["src/stdio/server.py"],
}

# 2. 建立连接（启动子进程 + MCP 握手）
async with stdio_client(server_params) as (read_stream, write_stream):
    async with ClientSession(read_stream, write_stream) as client:
        # 3. 初始化
        await client.initialize()

        # 4. API 调用 —— 高层封装
        tools_result = await client.list_tools()
        add_result = await client.call_tool("add", {"a": 10, "b": 20})
```

## 三、进程生命周期

```
ClientSession(stdio_client(...))
    │
    ├─ subprocess: python server.py     // 创建子进程
    │
    ├─ 等待服务端启动                      // 通过 stdio 管道就绪
    │
    ├─ 发送 initialize 请求               // MCP 握手
    │   ← 接收 capabilities 响应
    ├─ 发送 initialized 通知
    │
    ├─ 正常工作...  (tools/list, tools/call, ...)
    │
    └─ async with 退出
        └─ 关闭管道 → 子进程终止
```

## 四、关键知识点

### 消息边界

NDJSON 使用 `\n` 作为消息分隔符。JSON 内容中不能包含未转义的换行符。
这由 SDK 的序列化层保证 —— 所有 JSON 都通过 `json.dumps` 压缩为单行。

### 错误传播

```python
# 正确做法：返回错误内容（不要抛异常，连接不断开）
try:
    return dispatch_tool(name, args or {})
except Exception as error:
    msg = str(error)
    return [types.TextContent(type="text", text=f"错误: {msg}")]

# 错误做法：抛出未捕获异常 → 进程可能退出
raise ValueError("boom")
```

### 并发处理

stdio 是**全双工**的（可同时读写），但 JSON-RPC 按 id 匹配请求和响应。
服务端可以并发处理多个请求，只要保证 `id` 对应正确即可。

### 退出信号

- 客户端 `async with` 退出 → 关闭管道 → 服务端感知管道关闭 → 优雅退出
- 服务端 `sys.exit(0)` → 客户端感知子进程退出 → 关闭连接
- 异常退出 → 客户端收到 `ConnectionError` → 可决定是否重启
