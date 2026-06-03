# ============================================================
# MCP Demo - Streamable HTTP 模式客户端
# ============================================================
#
# 说明：
#   客户端通过 streamable_http_client 连接到服务端。
#   所有通信通过单个 POST /mcp 端点完成。
#
# 与 SSE 客户端的关键区别：
#   - 无需 SSE 长连接
#   - 无需 sessionId 管理
#   - 更简单的重连逻辑（无状态）
#   - 可选请求 SSE 流（通过 Accept header）

import asyncio

from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

STREAM_SERVER_URL = "http://localhost:3200"


async def main():
    print("=" * 50)
    print("MCP Streamable HTTP 模式客户端演示")
    print("=" * 50)
    print()

    try:
        # 1. 创建 Streamable HTTP transport
        async with streamablehttp_client(f"{STREAM_SERVER_URL}/mcp") as (
            read_stream,
            write_stream,
            _,  # get_session_id
        ):
            # 2. 创建 MCP Client Session
            async with ClientSession(read_stream, write_stream) as client:
                # 3. 初始化（HTTP POST 握手）
                await client.initialize()
                print("✓ 已通过 Streamable HTTP 连接到服务端")

                # 4. 调用工具 —— API 完全一致
                print("\n--- 获取工具列表 ---")
                tools_result = await client.list_tools()
                tools = tools_result.tools
                print(f"可用工具数: {len(tools)}")
                for tool in tools:
                    print(f"  · {tool.name}: {tool.description}")

                print("\n--- 调用 add ---")
                add_result = await client.call_tool("add", {"a": 100, "b": 200})
                for content in add_result.content:
                    print(f"结果: {content.text}")

                print("\n--- 调用 greet (英文) ---")
                greet_result = await client.call_tool("greet", {"name": "MCP", "language": "en"})
                for content in greet_result.content:
                    print(f"结果: {content.text}")

                print("\n--- 调用 get_time (东京) ---")
                time_result = await client.call_tool("get_time", {"timezone": "Asia/Tokyo"})
                for content in time_result.content:
                    print(f"结果: {content.text}")

        print("\n✓ 已关闭连接")

    except Exception as error:
        import traceback
        msg = str(error)
        print(f"✗ 错误: {msg}")
        # 若是 ExceptionGroup，展开子异常
        if hasattr(error, 'exceptions'):
            for sub in error.exceptions:  # type: ignore[attr-defined]
                print(f"  子异常: {sub}")
        if "ConnectionRefusedError" in msg or "connect" in msg.lower():
            print("\n提示：请先启动 Stream 服务端：python -m src.stream.server")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
