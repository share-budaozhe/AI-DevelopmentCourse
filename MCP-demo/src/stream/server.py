# ============================================================
# MCP Demo - Streamable HTTP (Stream) 模式服务端
# ============================================================
#
# 传输原理：
#   Streamable HTTP 是 MCP 协议最新的传输方式（2025年引入），
#   旨在替代 SSE 模式。它使用单个 HTTP 端点进行双向通信，
#   支持请求-响应模式和服务器→客户端流式推送。
#
#   核心思想：
#     - 单个 POST 端点处理所有 JSON-RPC 通信
#     - 可选：客户端可通过 Accept: text/event-stream 请求 SSE 流
#     - 服务端可主动通过 SSE 流推送通知
#     - 无状态设计，每个请求独立（不需要 session 追踪）
#
# 与 SSE 的对比：
#   ┌──────────┬─────────────────────┬───────────────────────────┐
#   │ 特性     │ SSE (旧)            │ Streamable HTTP (新)       │
#   ├──────────┼─────────────────────┼───────────────────────────┤
#   │ 端点数   │ 2 (GET /sse, POST)  │ 1 (POST /mcp)             │
#   │ 会话管理 │ 必需 (sessionId)    │ 可选                       │
#   │ 重连     │ 需重建 session      │ 无状态，自然恢复           │
#   │ 方向     │ 服务端→客户端单向流 │ 双向（请求+可选流）        │
#   │ 复杂度   │ 较高                │ 较低                       │
#   └──────────┴─────────────────────┴───────────────────────────┘
#
# 优点：
#   - 单端点设计，部署简单
#   - 无状态，水平扩展方便
#   - 向后兼容 SSE 客户端（Accept header）
#   - 减少连接数
#
# 缺点：
#   - 较新，生态支持不如 SSE 成熟
#   - 需要客户端支持新协议

import logging

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.streamable_http import StreamableHTTPServerTransport
import mcp.types as types

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from common.tools import DEMO_TOOLS, dispatch_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream-server")


# ---------- POST /mcp —— 唯一的 MCP 通信端点 ----------

# Transport 必须在模块级别创建并复用，不能每个请求新建。
transport = StreamableHTTPServerTransport(mcp_session_id=None)

server = Server("mcp-demo-stream-server")


@server.list_tools()
async def handle_list_tools() -> types.ListToolsResult:
    logger.info("[stream-server] tools/list 被调用")
    return types.ListToolsResult(tools=DEMO_TOOLS)


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    logger.info(f"[stream-server] tools/call: {name}({arguments})")
    try:
        return dispatch_tool(name, arguments or {})
    except Exception as error:
        msg = str(error)
        return [types.TextContent(type="text", text=f"错误: {msg}")]


async def handle_mcp(request: Request):
    """POST /mcp —— 将 HTTP 请求桥接到 MCP transport"""
    await transport.handle_request(request.scope, request.receive, request._send)


# ---------- 生命周期：保持 connect() 跨越整个服务运行期 ----------
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    """服务启动时连接 transport，关闭时清理"""
    import asyncio

    async with transport.connect() as (read_stream, write_stream):
        server_task = asyncio.create_task(
            server.run(
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
        )
        logger.info("[stream-server] Transport 已连接，server 后台运行中")
        try:
            yield
        finally:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

# ---------- 健康检查 ----------
async def health_check(request: Request):
    return JSONResponse({
        "status": "ok",
        "mode": "streamable-http",
        "mcpEndpoint": "POST /mcp",
    })


# ---------- Starlette 应用 ----------
app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/mcp", endpoint=handle_mcp, methods=["POST"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
    ]
)

# ---------- 启动 ----------
def main():
    PORT = 3200
    logger.info(f"[stream-server] MCP Streamable HTTP 服务已启动: http://localhost:{PORT}")
    logger.info(f"[stream-server] MCP 端点:   POST http://localhost:{PORT}/mcp")
    logger.info(f"[stream-server] 健康检查:   GET  http://localhost:{PORT}/health")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
