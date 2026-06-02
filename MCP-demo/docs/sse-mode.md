# SSE 模式详解

## 一、传输原理

SSE (Server-Sent Events) 模式使用 **HTTP 长连接** 实现服务端到客户端的单向推送。
由于 SSE 是单向的，MCP 使用**双端点**设计：

```
                    GET /sse (SSE 事件流：服务端 → 客户端)
Client ──────────────────────────────────────────────→ Server
        ←─────── endpoint 事件 (告知 POST /mcp) ──────
        ←─────── JSON-RPC 响应事件 ──────────────────
        ←─────── 通知事件 ──────────────────────────

                    POST /mcp?sessionId=xxx (JSON-RPC 请求：客户端 → 服务端)
Client ──────────────────────────────────────────────→ Server
        ←─────── HTTP 202 Accepted ─────────────────
```

### 双端点设计的原因

SSE 规范只支持**服务端→客户端**方向，客户端无法通过同一连接发送数据。
因此 MCP 引入第二个端点 `POST /mcp` 用于客户端上行消息。

## 二、连接流程

```
1. Client ── GET /sse ──→ Server
   （建立 SSE 长连接，Accept: text/event-stream）

2. Server ←── SSE event: endpoint ── Client
   event: endpoint
   data: /mcp?sessionId=abc123

3. Client 记录 sessionId，保存 SSE 连接

4. Client ── POST /mcp?sessionId=abc123 ──→ Server
   Body: {"jsonrpc":"2.0","method":"initialize",...}

5. Server 通过 SSE 连接推送：
   event: message
   data: {"jsonrpc":"2.0","id":1,"result":{...}}

6. 后续请求重复 4→5 循环
```

## 三、代码解读

### 服务端 (`src/sse/server.py`)

**核心架构**：

```python
from mcp.server.sse import SseServerTransport

# 创建全局 SSE transport（"/mcp" 是客户端 POST 消息的路径）
sse_transport = SseServerTransport("/mcp")

# SSE 端点 —— 建立长连接
async def handle_sse(request: Request):
    """GET /sse —— SSE 事件流端点"""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        # 为每个连接创建独立的 MCP Server 实例
        server = Server("mcp-demo-sse-server")

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

        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-demo-sse-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

# Starlette 路由配置
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
        Mount("/mcp", app=sse_transport.handle_post_message),
    ]
)
```

**设计要点**：
- **每个连接一个 Server 实例** —— `connect_sse()` 的上下文管理器为每个 SSE 连接创建独立的 transport
- **sessionId 自动管理** —— `SseServerTransport` 内部维护 sessionId 和 transport 的映射
- **消息路由** —— POST 请求通过 `handle_post_message` 路由到对应的 transport

### 客户端 (`src/sse/client.py`)

```python
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async with sse_client("http://localhost:3100/sse") as (read_stream, write_stream):
    async with ClientSession(read_stream, write_stream) as client:
        # transport 内部自动：
        #   1. 建立 SSE 长连接到 /sse
        #   2. 监听 endpoint 事件，获取 POST 端点
        #   3. 所有 JSON-RPC 请求通过 HTTP POST 发送
        #   4. 通过 SSE 事件流接收响应

        await client.initialize()
        tools_result = await client.list_tools()
        add_result = await client.call_tool("add", {"a": 5, "b": 7})
```

## 四、关键知识点

### Session 管理的必要性

SSE 模式下，服务端需要知道"哪个 POST 请求属于哪个 SSE 连接"。
sessionId 就是这个"关联键"。

**挑战**：多实例部署时，需要 sticky session（粘性会话），确保同一 session 的请求路由到同一实例。

### SSE 重连

SSE 连接断开时，Python MCP SDK 的 `sse_client` 会抛出异常。
客户端需要实现重试逻辑：

```python
import asyncio

async def connect_with_retry(url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    return client
        except Exception:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### 连接泄漏预防

`connect_sse()` 的 `async with` 上下文管理器在连接关闭时自动清理 transport。
Starlette 的请求生命周期也确保连接断开时资源被释放。

### 弃用说明

> ⚠️ SSE 模式正逐渐被 Streamable HTTP 取代。
> 推荐新项目使用 Streamable HTTP 模式。
> 但由于大量现有 MCP Server 仍使用 SSE，理解 SSE 模式仍然重要。

## 五、SSE vs WebSocket

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| 方向 | 单向（S→C） | 双向 |
| 协议 | HTTP | 独立协议 (ws://) |
| 自动重连 | 需手动实现 | 需手动实现 |
| 二进制 | 不支持 | 支持 |
| 代理兼容 | HTTP 代理友好 | 部分代理不支持 |
| MCP 采用 | 是（旧推荐） | 否 |
