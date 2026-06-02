# Streamable HTTP (Stream) 模式详解

## 一、传输原理

Streamable HTTP 是 MCP 协议**最新的传输方式**（2025 年引入），旨在替代 SSE 成为推荐的 HTTP 传输模式。
核心思想：**单端点 + 无状态 + 可选流式推送**。

```
Client ──── POST /mcp ────→ Server
  Body: {"jsonrpc":"2.0","method":"tools/call",...}
  Header: Accept: application/json  (普通请求)

Client ←─── 200 OK ──────── Server
  Body: {"jsonrpc":"2.0","id":1,"result":{...}}

                 或

Client ──── POST /mcp ────→ Server
  Header: Accept: text/event-stream  (请求 SSE 流)

Client ←─── 200 OK (SSE 流) ── Server
  event: message
  data: {"jsonrpc":"2.0","id":1,"result":{...}}
  event: message
  data: {"jsonrpc":"2.0","method":"notifications/progress",...}
```

### 与 SSE 模式的关键区别

```
SSE 模式:
  GET /sse  ──→ (建立长连接)
  POST /mcp ──→ (发送消息)
  问题: 两个端点，需要 sessionId 关联

Streamable HTTP:
  POST /mcp ──→ (发送消息 + 可选 SSE 流)
  优势: 单端点，无需 sessionId
```

## 二、代码解读

### 服务端 (`src/stream/server.py`)

```python
async def handle_mcp(request: Request):
    """POST /mcp —— 处理所有 JSON-RPC 通信"""
    body = await request.json()

    # 1. 为每个请求创建独立的 Server + Transport —— 无状态设计
    server = Server("mcp-demo-stream-server")

    # 2. 注册 handler（与 stdio/SSE 完全相同）
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

    # 3. 创建 StreamableHTTP transport（无状态，不需要 sessionId 生成器）
    transport = StreamableHTTPServerTransport()

    # 4. 连接并处理请求
    async with transport.connect() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-demo-stream-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
    # 请求结束时 transport 和 server 一起被 GC 回收

# Starlette 路由
app = Starlette(
    routes=[
        Route("/mcp", endpoint=handle_mcp, methods=["POST"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
    ]
)
```

### 客户端 (`src/stream/client.py`)

```python
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client("http://localhost:3200/mcp") as (
    read_stream,
    write_stream,
):
    async with ClientSession(read_stream, write_stream) as client:
        # 仅需一个 URL —— 不需要 SSE 端点
        await client.initialize()
        tools_result = await client.list_tools()
        add_result = await client.call_tool("add", {"a": 100, "b": 200})
```

## 三、无状态 vs 有状态

### 有状态（SSE 模式）

```
请求1 → Server (session=abc) → 状态保持在内存
请求2 → Server (session=abc) → 需要路由到同一实例

问题: 水平扩展需要 sticky session
```

### 无状态（Streamable HTTP 模式）

```
请求1 → Server 实例A → 独立处理，无状态保留
请求2 → Server 实例B → 独立处理，无状态保留

优势: 任意负载均衡，天然水平扩展
```

**但注意**：如果需要服务端推送通知（如进度更新），则需要有状态。
此时 `StreamableHTTPServerTransport` 可传入 `session_id` 参数来启用会话管理。

## 四、"Stream" 的三层含义

```
Layer 1: HTTP 传输层流
  Transfer-Encoding: chunked
  → 大响应可以分块发送，无需缓冲完整响应

Layer 2: SSE 应用层流
  Accept: text/event-stream
  → 客户端请求 SSE 格式的流式响应
  → 服务端可推送多条消息（如进度通知）

Layer 3: MCP 协议层流
  工具调用返回多个 content 项
  → 服务端逐步返回结果片段
```

## 五、关键知识点

### Accept Header 协商

```
Accept: application/json       → 普通 JSON-RPC 响应（一次性）
Accept: text/event-stream      → SSE 流式响应（可持续推送）
```

客户端可通过 `Accept` header 告知服务端期望的响应格式。

### 向后兼容

Streamable HTTP 服务端**向后兼容** SSE 客户端：
- SSE 客户端连接时发送 `Accept: text/event-stream`
- 服务端自动切换到 SSE 模式

### 部署优势

```yaml
# SSE 模式部署
负载均衡器:
  - sticky session: enabled  ← 必须
  - 健康检查: GET /health

# Streamable HTTP 部署
负载均衡器:
  - sticky session: disabled ← 不需要
  - 健康检查: GET /health
```

### 重连策略

```python
# 无状态模式下的重连非常简单
import asyncio

async def call_with_retry(client_session, tool_name, args, retries=3):
    for i in range(retries):
        try:
            return await client_session.call_tool(tool_name, args)
        except Exception:
            if i == retries - 1:
                raise
            await asyncio.sleep(2 ** i)
# 无需重建 session，直接重试即可
```

## 六、迁移指南：SSE → Streamable HTTP

| 改动项 | SSE | Streamable HTTP |
|--------|-----|-----------------|
| 服务端 Transport | `SseServerTransport` | `StreamableHTTPServerTransport` |
| 客户端 Transport | `sse_client` | `streamablehttp_client` |
| 端点 | GET /sse + POST /mcp | POST /mcp |
| Session 管理 | `connect_sse()` 内部管理 | 不需要 |
| 代码行数 | ~60 行 | ~45 行 |

**迁移步骤**：
1. 替换服务端 Transport 类（`SseServerTransport` → `StreamableHTTPServerTransport`）
2. 删除 GET /sse 端点和 `connect_sse` 的上下文管理器
3. 每个 POST 请求内创建新的 Server + Transport
4. 替换客户端 Transport（`sse_client` → `streamablehttp_client`）
5. 更新 URL（去掉 `/sse`，指向 `/mcp`）
