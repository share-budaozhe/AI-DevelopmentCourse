// ============================================================
// MCP Demo - stdio 模式服务端
// ============================================================
//
// 传输原理：
//   stdio (标准输入/输出) 是最简单、最可靠的 MCP 传输方式。
//   服务端作为子进程启动，通过 stdin 读取 JSON-RPC 消息，
//   通过 stdout 写入 JSON-RPC 响应。
//
// 通信流程：
//   1. 客户端 spawn 服务端进程
//   2. 客户端通过服务端的 stdin 发送 JSON-RPC 请求（每行一个 JSON）
//   3. 服务端处理后通过 stdout 返回 JSON-RPC 响应（每行一个 JSON）
//   4. 服务端也可主动通过 stdout 发送通知（如 logging）
//
// 优点：
//   - 无需网络端口，无防火墙问题
//   - 进程生命周期由客户端管理，天然隔离
//   - 实现简单，调试方便
//   - 适合本地工具、CLI 集成
//
// 缺点：
//   - 仅限本地通信
//   - 不支持多客户端
//   - 服务端崩溃需要客户端重新启动
//
// 安全注意事项：
//   - stdio 模式的信任边界是"本地进程"
//   - 服务端运行在客户端用户的权限下
//   - 不应在 stdio 模式下暴露敏感操作给不受信任的客户端

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { DEMO_TOOLS, dispatchTool } from "../common/tools.js";

// 1. 创建 MCP Server 实例
const server = new Server(
  { name: "mcp-demo-stdio", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// 2. 注册 tools/list 处理器 —— 客户端调用此方法获取可用工具列表
server.setRequestHandler(ListToolsRequestSchema, async () => {
  console.error("[stdio-server] tools/list 被调用"); // stderr 用于日志，不影响通信
  return { tools: DEMO_TOOLS };
});

// 3. 注册 tools/call 处理器 —— 客户端调用此方法执行具体工具
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  console.error(`[stdio-server] tools/call: ${name}(${JSON.stringify(args)})`);
  try {
    return dispatchTool(name, args ?? {});
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return { content: [{ type: "text", text: `错误: ${msg}` }], isError: true };
  }
});

// 4. 使用 StdioServerTransport 启动服务
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[stdio-server] MCP stdio 服务已启动，等待消息...");
  console.error("[stdio-server] PID:", process.pid);
}

main().catch((err) => {
  console.error("[stdio-server] 启动失败:", err);
  process.exit(1);
});
