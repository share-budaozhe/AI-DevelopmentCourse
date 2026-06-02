// ============================================================
// MCP Demo - SSE 模式服务端
// ============================================================
//
// 传输原理：
//   SSE (Server-Sent Events) 基于 HTTP 长连接，服务端向客户端单向推送事件流。
//   MCP 的 SSE 传输使用两个 HTTP 端点：
//     GET  /sse   —— SSE 事件流（服务端 → 客户端）
//     POST /mcp   —— JSON-RPC 消息（客户端 → 服务端）
//
// 通信流程：
//   1. 客户端建立 GET /sse 的 SSE 长连接
//   2. 服务端通过 SSE 推送 endpoint 事件，告知消息端点的 URL（POST /mcp）
//   3. 客户端通过 POST /mcp 发送 JSON-RPC 请求
//   4. 服务端通过 SSE 事件流推送 JSON-RPC 响应
//
// 架构表示：
//   客户端 ── GET /sse  ──→ 服务端 (SSE 流, 服务端→客户端)
//   客户端 ── POST /mcp ──→ 服务端 (JSON-RPC 请求)
//   客户端 ←── SSE event ── 服务端 (JSON-RPC 响应)
//
// 优点：
//   - 支持远程通信（HTTP）
//   - 可被多个客户端连接（每个客户端独立的 session）
//   - 可穿越防火墙/代理（标准 HTTP）
//   - 天然支持服务端主动推送通知
//
// 缺点：
//   - 需要管理 session 和连接状态
//   - SSE 是单向的（还需 POST 端点做上行）
//   - 需要 HTTP 服务器基础设施
//   - 连接断开需要客户端重连

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import express from "express";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { DEMO_TOOLS, dispatchTool } from "../common/tools.js";

const app = express();
app.use(express.json());

// 存储活跃的 transport 实例（按 sessionId 索引）
const transports = new Map<string, SSEServerTransport>();

// ---------- GET /sse —— SSE 事件流端点 ----------
app.get("/sse", async (_req, res, next) => {
  try {
    // 1. 创建 MCP Server 实例（每个连接一个独立实例）
    const server = new Server(
      { name: "mcp-demo-sse-server", version: "1.0.0" },
      { capabilities: { tools: {} } }
    );

    // 2. 注册工具处理器
    server.setRequestHandler(ListToolsRequestSchema, async () => {
      console.log("[sse-server] tools/list 被调用");
      return { tools: DEMO_TOOLS };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      console.log(`[sse-server] tools/call: ${name}(${JSON.stringify(args)})`);
      try {
        return dispatchTool(name, args ?? {});
      } catch (error) {
        const msg = error instanceof Error ? error.message : String(error);
        return { content: [{ type: "text", text: `错误: ${msg}` }], isError: true };
      }
    });

    // 3. 创建 SSE transport —— 参数是 HTTP 消息端点路径
    //    客户端收到 endpoint 事件后会向此路径 POST JSON-RPC 消息
    const transport = new SSEServerTransport("/mcp", res);
    transports.set(transport.sessionId, transport);

    // 4. 连接关闭时清理
    res.on("close", () => {
      console.log(`[sse-server] session 关闭: ${transport.sessionId}`);
      transports.delete(transport.sessionId);
    });

    // 5. 连接到服务器（这会发送初始 SSE 事件，包括 endpoint）
    await server.connect(transport);
    console.log(`[sse-server] 新 SSE 连接: sessionId=${transport.sessionId}`);
  } catch (err) {
    next(err);
  }
});

// ---------- POST /mcp —— 客户端消息端点 ----------
app.post("/mcp", async (req, res, next) => {
  try {
    // 从 query 参数获取 sessionId
    const sessionId = req.query.sessionId as string | undefined;
    if (!sessionId) {
      res.status(400).json({ error: "缺少 sessionId 参数" });
      return;
    }

    const transport = transports.get(sessionId);
    if (!transport) {
      res.status(404).json({ error: "session 未找到或已过期" });
      return;
    }

    // 将 POST body 交给 transport 处理（JSON-RPC 消息）
    await transport.handlePostMessage(req, res, req.body);
  } catch (err) {
    next(err);
  }
});

// ---------- 健康检查 ----------
app.get("/health", (_req, res) => {
  res.json({ status: "ok", activeSessions: transports.size });
});

// ---------- 启动 HTTP 服务 ----------
const PORT = 3100;
app.listen(PORT, () => {
  console.log(`[sse-server] MCP SSE 服务已启动: http://localhost:${PORT}`);
  console.log(`[sse-server] SSE 端点:   GET  http://localhost:${PORT}/sse`);
  console.log(`[sse-server] 消息端点:   POST http://localhost:${PORT}/mcp`);
  console.log(`[sse-server] 健康检查:   GET  http://localhost:${PORT}/health`);
});
