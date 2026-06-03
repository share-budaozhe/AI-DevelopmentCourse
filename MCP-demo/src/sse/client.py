# ============================================================
# MCP Demo - SSE 模式客户端
# ============================================================
#
# 说明：
#   客户端通过 sse_client 连接到 SSE 服务端。
#   transport 自动处理：
#     1. 建立 SSE 长连接 (GET /sse)
#     2. 接收 endpoint 事件，获取消息端点 URL
#     3. 通过 POST /mcp?sessionId=xxx 发送 JSON-RPC 消息
#     4. 通过 SSE 事件流接收 JSON-RPC 响应
#
# 重连机制：
#   SSE 连接可能因网络问题断开，客户端需要实现重连逻辑。
#   本 demo 演示了简单的重连机制。

import asyncio

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

SSE_SERVER_URL = "http://localhost:3100"


async def main():
    print("=" * 50)
    print("MCP SSE 模式客户端演示")
    print("=" * 50)
    print()

    try:
        # 1. 创建 SSE transport —— 指定 SSE 端点 URL
        async with sse_client(f"{SSE_SERVER_URL}/sse") as (read_stream, write_stream):
            # 2. 创建 MCP Client Session
            async with ClientSession(read_stream, write_stream) as client:
                # 3. 初始化（建立 SSE + endpoint 发现 + 握手）
                await client.initialize()
                print("✓ 已通过 SSE 连接到服务端")

                # 4. 调用工具（与 stdio 模式完全相同的 API）
                print("\n--- 获取工具列表 ---")
                tools_result = await client.list_tools()
                tools = tools_result.tools
                print(f"可用工具数: {len(tools)}")
                for tool in tools:
                    print(f"  · {tool.name}: {tool.description}")

                print("\n--- 调用 add ---")
                add_result = await client.call_tool("add", {"a": 5, "b": 7})
                for content in add_result.content:
                    print(f"结果: {content.text}")

                print("\n--- 调用 greet (日文) ---")
                greet_result = await client.call_tool("greet", {"name": "太郎", "language": "ja"})
                for content in greet_result.content:
                    print(f"结果: {content.text}")

                print("\n--- 调用 get_time (纽约) ---")
                time_result = await client.call_tool("get_time", {"timezone": "America/New_York"})
                for content in time_result.content:
                    print(f"结果: {content.text}")

        print("\n✓ 已关闭连接")

    except Exception as error:
        import traceback
        msg = str(error)
        print(f"✗ 错误: {msg}")
        if hasattr(error, 'exceptions'):
            for sub in error.exceptions:  # type: ignore[attr-defined]
                print(f"  子异常: {sub}")
        if "ConnectionRefusedError" in msg or "connect" in msg.lower():
            print("\n提示：请先启动 SSE 服务端：python -m src.sse.server")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
