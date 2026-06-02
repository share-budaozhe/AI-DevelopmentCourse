# ============================================================
# MCP Demo - stdio 模式客户端
# ============================================================
#
# 说明：
#   客户端通过 subprocess 启动服务端子进程，
#   通过 stdin/stdout 与服务端进行 JSON-RPC 通信。
#
# 关键实现细节：
#   - 使用 stdio_client + ClientSession 组合
#   - transport 自动管理子进程的 spawn 和 stdio 管道
#   - 所有通信都是行分隔的 JSON（NDJSON 格式）
#   - 客户端负责进程生命周期（启动/关闭）

import asyncio

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

SERVER_SCRIPT = "src/stdio/server.py"


async def main():
    print("=" * 50)
    print("MCP stdio 模式客户端演示")
    print("=" * 50)
    print()

    # 1. 创建 stdio transport —— 指定服务端启动命令
    #    transport 内部会执行: python src/stdio/server.py
    server_params = {
        "command": "python",
        "args": [SERVER_SCRIPT],
    }

    try:
        # 2. 建立连接（启动子进程 + MCP 握手）
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                # 3. 初始化
                await client.initialize()
                print("✓ 已连接到 stdio 服务端")

                # 4. 调用 tools/list —— 获取可用工具列表
                print("\n--- 获取工具列表 (tools/list) ---")
                tools_result = await client.list_tools()
                tools = tools_result.tools
                print(f"可用工具数: {len(tools)}")
                for tool in tools:
                    print(f"  · {tool.name}: {tool.description}")

                # 5. 逐个调用工具
                print("\n--- 调用 add ---")
                add_result = await client.call_tool("add", {"a": 10, "b": 20})
                for content in add_result.content:
                    print(f"结果: {content.text}")

                print("\n--- 调用 greet ---")
                greet_result = await client.call_tool("greet", {"name": "世界", "language": "zh"})
                for content in greet_result.content:
                    print(f"结果: {content.text}")

                print("\n--- 调用 greet (英文) ---")
                greet_en = await client.call_tool("greet", {"name": "World", "language": "en"})
                for content in greet_en.content:
                    print(f"结果: {content.text}")

                print("\n--- 调用 get_time ---")
                time_result = await client.call_tool("get_time", {"timezone": "Asia/Shanghai"})
                for content in time_result.content:
                    print(f"结果: {content.text}")

        print("\n✓ 已关闭连接")
    except Exception as error:
        msg = str(error)
        print(f"✗ 错误: {msg}")
        if "ConnectionRefusedError" in msg:
            print("\n提示：请确保已安装 Python 且 mcp 包可用")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
