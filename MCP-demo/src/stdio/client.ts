// ============================================================
// MCP Demo - stdio 模式客户端
// ============================================================
//
// 说明：
//   客户端通过 child_process.spawn 启动服务端子进程，
//   通过 stdin/stdout 与服务端进行 JSON-RPC 通信。
//
// 关键实现细节：
//   - 使用 Client + StdioClientTransport 组合
//   - transport 自动管理子进程的 spawn 和 stdio 管道
//   - 所有通信都是行分隔的 JSON（NDJSON 格式）
//   - 客户端负责进程生命周期（启动/关闭）

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  console.log("=".repeat(50));
  console.log("MCP stdio 模式客户端演示");
  console.log("=".repeat(50));
  console.log();

  // 1. 创建 transport —— 指定服务端启动命令
  //    transport 内部会执行: node --import tsx src/stdio/server.ts
  const transport = new StdioClientTransport({
    command: "node",
    args: ["--import", "tsx", "src/stdio/server.ts"],
  });

  // 2. 创建 MCP Client 实例
  const client = new Client(
    { name: "mcp-demo-stdio-client", version: "1.0.0" },
    { capabilities: {} }
  );

  try {
    // 3. 连接到服务端（启动子进程 + 握手）
    await client.connect(transport);
    console.log("✓ 已连接到 stdio 服务端");

    // 4. 调用 tools/list —— 获取可用工具列表
    console.log("\n--- 获取工具列表 (tools/list) ---");
    const { tools } = await client.listTools();
    console.log(`可用工具数: ${tools.length}`);
    for (const tool of tools) {
      console.log(`  · ${tool.name}: ${tool.description}`);
    }

    // 5. 逐个调用工具
    console.log("\n--- 调用 add ---");
    const addResult = await client.callTool({
      name: "add",
      arguments: { a: 10, b: 20 },
    });
    console.log("结果:", (addResult.content as { type: string; text: string }[])[0]?.text);
    // 检查是否为错误响应
    // SDK 中 isError 在 CallToolResult 上可用
    // 类型断言以访问 isError
    const addContent = addResult.content as { type: string; text: string }[];
    if ((addResult as { isError?: boolean }).isError) {
      console.log("  (错误响应)");
    }

    console.log("\n--- 调用 greet ---");
    const greetResult = await client.callTool({
      name: "greet",
      arguments: { name: "世界", language: "zh" },
    });
    console.log("结果:", (greetResult.content as { type: string; text: string }[])[0]?.text);

    console.log("\n--- 调用 greet (英文) ---");
    const greetEnResult = await client.callTool({
      name: "greet",
      arguments: { name: "World", language: "en" },
    });
    console.log("结果:", (greetEnResult.content as { type: string; text: string }[])[0]?.text);

    console.log("\n--- 调用 get_time ---");
    const timeResult = await client.callTool({
      name: "get_time",
      arguments: { timezone: "Asia/Shanghai" },
    });
    console.log("结果:", (timeResult.content as { type: string; text: string }[])[0]?.text);

    // 6. 关闭连接（同时会终止子进程）
    await client.close();
    console.log("\n✓ 已关闭连接");
  } catch (error) {
    console.error("✗ 错误:", error);
    process.exit(1);
  }
}

main();
