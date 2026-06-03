# ============================================================
# MCP Demo - SSE 模式服务端
# ============================================================
#
# 传输原理：
#   SSE (Server-Sent Events) 基于 HTTP 长连接，服务端向客户端单向推送事件流。
#   MCP 的 SSE 传输使用两个 HTTP 端点：
#     GET  /sse   —— SSE 事件流（服务端 → 客户端）
#     POST /mcp   —— JSON-RPC 消息（客户端 → 服务端）
#
# 通信流程：
#   1. 客户端建立 GET /sse 的 SSE 长连接
#   2. 服务端通过 SSE 推送 endpoint 事件，告知消息端点的 URL（POST /mcp）
#   3. 客户端通过 POST /mcp 发送 JSON-RPC 请求
#   4. 服务端通过 SSE 事件流推送 JSON-RPC 响应
#
# 架构表示：
#   客户端 ── GET /sse  ──→ 服务端 (SSE 流, 服务端→客户端)
#   客户端 ── POST /mcp ──→ 服务端 (JSON-RPC 请求)
#   客户端 ←── SSE event ── 服务端 (JSON-RPC 响应)
#
# 优点：
#   - 支持远程通信（HTTP）
#   - 可被多个客户端连接（每个客户端独立的 session）
#   - 可穿越防火墙/代理（标准 HTTP）
#   - 天然支持服务端主动推送通知
#
# 缺点：
#   - 需要管理 session 和连接状态
#   - SSE 是单向的（还需 POST 端点做上行）
#   - 需要 HTTP 服务器基础设施
#   - 连接断开需要客户端重连

import logging

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
import mcp.types as types

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from common.tools import DEMO_TOOLS, dispatch_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sse-server")

# 创建 SSE transport（"/mcp" 是客户端 POST 消息的路径）
sse_transport = SseServerTransport("/mcp")


# ---------- SSE 连接处理 ----------
async def handle_sse(request: Request):
    """GET /sse —— SSE 事件流端点"""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        # 为每个连接创建独立的 MCP Server 实例
        server = Server("mcp-demo-sse-server")

        @server.list_tools()
        async def handle_list_tools() -> types.ListToolsResult:
            logger.info("[sse-server] tools/list 被调用")
            return types.ListToolsResult(tools=DEMO_TOOLS)

        @server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent]:
            logger.info(f"[sse-server] tools/call: {name}({arguments})")
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


# ---------- 健康检查 ----------
async def health_check(request: Request):
    return JSONResponse({"status": "ok", "mode": "sse"})


# ---------- Starlette 应用 ----------
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
        Mount("/mcp", app=sse_transport.handle_post_message),
    ]
)

# ---------- 启动 ----------
def main():
    PORT = 3100
    logger.info(f"[sse-server] MCP SSE 服务已启动: http://localhost:{PORT}")
    logger.info(f"[sse-server] SSE 端点:   GET  http://localhost:{PORT}/sse")
    logger.info(f"[sse-server] 消息端点:   POST http://localhost:{PORT}/mcp")
    logger.info(f"[sse-server] 健康检查:   GET  http://localhost:{PORT}/health")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
