// ============================================================
// MCP Demo - Streamable HTTP 模式客户端
// ============================================================
//
// 说明：
//   客户端通过 StreamableHTTPClientTransport 连接到服务端。
//   所有通信通过单个 POST /mcp 端点完成。
//
// 与 SSE 客户端的关键区别：
//   - 无需 SSE 长连接
//   - 无需 sessionId 管理
//   - 更简单的重连逻辑（无状态）
//   - 可选请求 SSE 流（通过 Accept header）

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const STREAM_SERVER_URL = "http://localhost:3200";

async function main() {
  console.log("=".repeat(50));
  console.log("MCP Streamable HTTP 模式客户端演示");
  console.log("=".repeat(50));
  console.log();

  // 1. 创建 Streamable HTTP transport
  const transport = new StreamableHTTPClientTransport(
    new URL(`${STREAM_SERVER_URL}/mcp`)
  );

  // 2. 创建 MCP Client
  const client = new Client(
    { name: "mcp-demo-stream-client", version: "1.0.0" },
    { capabilities: {} }
  );

  try {
    // 3. 连接（HTTP POST 握手）
    await client.connect(transport);
    console.log("✓ 已通过 Streamable HTTP 连接到服务端");

    // 4. 调用工具 —— API 完全一致
    console.log("\n--- 获取工具列表 ---");
    const { tools } = await client.listTools();
    console.log(`可用工具数: ${tools.length}`);
    for (const tool of tools) {
      console.log(`  · ${tool.name}: ${tool.description}`);
    }

    console.log("\n--- 调用 add ---");
    const addResult = await client.callTool({
      name: "add",
      arguments: { a: 100, b: 200 },
    });
    console.log("结果:", (addResult.content as { type: string; text: string }[])[0]?.text);

    console.log("\n--- 调用 greet (英文) ---");
    const greetResult = await client.callTool({
      name: "greet",
      arguments: { name: "MCP", language: "en" },
    });
    console.log("结果:", (greetResult.content as { type: string; text: string }[])[0]?.text);

    console.log("\n--- 调用 get_time (东京) ---");
    const timeResult = await client.callTool({
      name: "get_time",
      arguments: { timezone: "Asia/Tokyo" },
    });
    console.log("结果:", (timeResult.content as { type: string; text: string }[])[0]?.text);

    await client.close();
    console.log("\n✓ 已关闭连接");
  } catch (error) {
    console.error("✗ 错误:", error);
    if (String(error).includes("ECONNREFUSED")) {
      console.error("\n提示：请先启动 Stream 服务端：npm run dev:stream-server");
    }
    process.exit(1);
  }
}

main();
