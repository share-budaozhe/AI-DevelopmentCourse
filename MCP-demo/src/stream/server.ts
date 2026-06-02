// ============================================================
// MCP Demo - Streamable HTTP (Stream) 模式服务端
// ============================================================
//
// 传输原理：
//   Streamable HTTP 是 MCP 协议最新的传输方式（2025年引入），
//   旨在替代 SSE 模式。它使用单个 HTTP 端点进行双向通信，
//   支持请求-响应模式和服务器→客户端流式推送。
//
//   核心思想：
//     - 单个 POST 端点处理所有 JSON-RPC 通信
//     - 可选：客户端可通过 Accept: text/event-stream 请求 SSE 流
//     - 服务端可主动通过 SSE 流推送通知
//     - 无状态设计，每个请求独立（不需要 session 追踪）
//
// 与 SSE 的对比：
//   ┌──────────┬─────────────────────┬───────────────────────────┐
//   │ 特性     │ SSE (旧)            │ Streamable HTTP (新)       │
//   ├──────────┼─────────────────────┼───────────────────────────┤
//   │ 端点数   │ 2 (GET /sse, POST)  │ 1 (POST /mcp)             │
//   │ 会话管理 │ 必需 (sessionId)    │ 可选                       │
//   │ 重连     │ 需重建 session      │ 无状态，自然恢复           │
//   │ 方向     │ 服务端→客户端单向流 │ 双向（请求+可选流）        │
//   │ 复杂度   │ 较高                │ 较低                       │
//   └──────────┴─────────────────────┴───────────────────────────┘
//
// 优点：
//   - 单端点设计，部署简单
//   - 无状态，水平扩展方便
//   - 向后兼容 SSE 客户端（Accept header）
//   - 减少连接数
//
// 缺点：
//   - 较新，生态支持不如 SSE 成熟
//   - 需要客户端支持新协议
//
// 关键概念 —— Stream 的"流"三层含义：
//   1. HTTP 层面的流式传输 (Transfer-Encoding: chunked)
//   2. SSE 层面的服务器推送 (text/event-stream)
//   3. MCP 层面的响应流 (服务端逐步返回工具调用结果)

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express from "express";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { DEMO_TOOLS, dispatchTool } from "../common/tools.js";

const app = express();
app.use(express.json());

// ---------- POST /mcp —— 唯一的 MCP 通信端点 ----------
app.post("/mcp", async (req, res, next) => {
  try {
    // 1. 为每个请求创建独立的 Server + Transport
    //    Streamable HTTP 是无状态的，不需要跨请求共享 transport
    const server = new Server(
      { name: "mcp-demo-stream-server", version: "1.0.0" },
      { capabilities: { tools: {} } }
    );

    // 2. 注册工具处理器
    server.setRequestHandler(ListToolsRequestSchema, async () => {
      console.log("[stream-server] tools/list 被调用");
      return { tools: DEMO_TOOLS };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      console.log(`[stream-server] tools/call: ${name}(${JSON.stringify(args)})`);
      try {
        return dispatchTool(name, args ?? {});
      } catch (error) {
        const msg = error instanceof Error ? error.message : String(error);
        return { content: [{ type: "text", text: `错误: ${msg}` }], isError: true };
      }
    });

    // 3. 创建 StreamableHTTP transport
    //    - 参数1: 响应对象
    //    - 参数2: 选项（如 sessionId 生成器、是否启用 SSE 流等）
    const transport = new StreamableHTTPServerTransport(
      {
        sessionIdGenerator: undefined, // 无状态模式
      }
    );

    // 4. 连接并处理请求
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (err) {
    next(err);
  }
});

// ---------- 健康检查 ----------
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    mode: "streamable-http",
    mcpEndpoint: "POST /mcp",
  });
});

// ---------- 启动 HTTP 服务 ----------
const PORT = 3200;
app.listen(PORT, () => {
  console.log(`[stream-server] MCP Streamable HTTP 服务已启动: http://localhost:${PORT}`);
  console.log(`[stream-server] MCP 端点:   POST http://localhost:${PORT}/mcp`);
  console.log(`[stream-server] 健康检查:   GET  http://localhost:${PORT}/health`);
});
