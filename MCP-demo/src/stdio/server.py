# ============================================================
# MCP Demo - stdio 模式服务端
# ============================================================
#
# 传输原理：
#   stdio (标准输入/输出) 是最简单、最可靠的 MCP 传输方式。
#   服务端作为子进程启动，通过 stdin 读取 JSON-RPC 消息，
#   通过 stdout 写入 JSON-RPC 响应。
#
# 通信流程：
#   1. 客户端 spawn 服务端进程
#   2. 客户端通过服务端的 stdin 发送 JSON-RPC 请求（每行一个 JSON）
#   3. 服务端处理后通过 stdout 返回 JSON-RPC 响应（每行一个 JSON）
#   4. 服务端也可主动通过 stdout 发送通知（如 logging）
#
# 优点：
#   - 无需网络端口，无防火墙问题
#   - 进程生命周期由客户端管理，天然隔离
#   - 实现简单，调试方便
#   - 适合本地工具、CLI 集成
#
# 缺点：
#   - 仅限本地通信
#   - 不支持多客户端
#   - 服务端崩溃需要客户端重新启动
#
# 安全注意事项：
#   - stdio 模式的信任边界是"本地进程"
#   - 服务端运行在客户端用户的权限下
#   - 不应在 stdio 模式下暴露敏感操作给不受信任的客户端

import asyncio
import logging
import sys

from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

from common.tools import DEMO_TOOLS, dispatch_tool

# 日志输出到 stderr，避免污染 stdout 上的 JSON-RPC 通信
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("stdio-server")

# 1. 创建 MCP Server 实例
server = Server("mcp-demo-stdio")


# 2. 注册 tools/list 处理器 —— 客户端调用此方法获取可用工具列表
@server.list_tools()
async def handle_list_tools() -> types.ListToolsResult:
    logger.info("[stdio-server] tools/list 被调用")
    return types.ListToolsResult(tools=DEMO_TOOLS)


# 3. 注册 tools/call 处理器 —— 客户端调用此方法执行具体工具
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    logger.info(f"[stdio-server] tools/call: {name}({arguments})")
    try:
        return dispatch_tool(name, arguments or {})
    except Exception as error:
        msg = str(error)
        return [types.TextContent(type="text", text=f"错误: {msg}")]


# 4. 使用 StdioServerTransport 启动服务
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
    logger.info("[stdio-server] MCP stdio 服务已启动，等待消息...")
    logger.info(f"[stdio-server] PID: {__import__('os').getpid()}")
    asyncio.run(main())
