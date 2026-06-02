// ============================================================
// MCP Demo - SSE 模式客户端
// ============================================================
//
// 说明：
//   客户端通过 SSEClientTransport 连接到 SSE 服务端。
//   transport 自动处理：
//     1. 建立 SSE 长连接 (GET /sse)
//     2. 接收 endpoint 事件，获取消息端点 URL
//     3. 通过 POST /mcp?sessionId=xxx 发送 JSON-RPC 消息
//     4. 通过 SSE 事件流接收 JSON-RPC 响应
//
// 重连机制：
//   SSE 连接可能因网络问题断开，客户端需要实现重连逻辑。
//   本 demo 演示了简单的重连机制。

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

const SSE_SERVER_URL = "http://localhost:3100";

async function main() {
  console.log("=".repeat(50));
  console.log("MCP SSE 模式客户端演示");
  console.log("=".repeat(50));
  console.log();

  // 1. 创建 SSE transport —— 指定 SSE 端点 URL
  const transport = new SSEClientTransport(
    new URL(`${SSE_SERVER_URL}/sse`)
  );

  // 2. 创建 MCP Client
  const client = new Client(
    { name: "mcp-demo-sse-client", version: "1.0.0" },
    { capabilities: {} }
  );

  try {
    // 3. 连接（建立 SSE + endpoint 发现 + 握手）
    await client.connect(transport);
    console.log("✓ 已通过 SSE 连接到服务端");

    // 4. 调用工具（与 stdio 模式完全相同的 API）
    console.log("\n--- 获取工具列表 ---");
    const { tools } = await client.listTools();
    console.log(`可用工具数: ${tools.length}`);
    for (const tool of tools) {
      console.log(`  · ${tool.name}: ${tool.description}`);
    }

    console.log("\n--- 调用 add ---");
    const addResult = await client.callTool({
      name: "add",
      arguments: { a: 5, b: 7 },
    });
    console.log("结果:", (addResult.content as { type: string; text: string }[])[0]?.text);

    console.log("\n--- 调用 greet (日文) ---");
    const greetResult = await client.callTool({
      name: "greet",
      arguments: { name: "太郎", language: "ja" },
    });
    console.log("结果:", (greetResult.content as { type: string; text: string }[])[0]?.text);

    console.log("\n--- 调用 get_time (纽约) ---");
    const timeResult = await client.callTool({
      name: "get_time",
      arguments: { timezone: "America/New_York" },
    });
    console.log("结果:", (timeResult.content as { type: string; text: string }[])[0]?.text);

    await client.close();
    console.log("\n✓ 已关闭连接");
  } catch (error) {
    console.error("✗ 错误:", error);
    if (String(error).includes("ECONNREFUSED")) {
      console.error("\n提示：请先启动 SSE 服务端：npm run dev:sse-server");
    }
    process.exit(1);
  }
}

main();
