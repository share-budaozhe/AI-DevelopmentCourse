# MCP 协议概述

## 一、什么是 MCP？

**MCP (Model Context Protocol)** 是一种开放协议，由 Anthropic 提出，旨在标准化 AI 模型与外部工具、数据源之间的通信方式。它类似于 AI 世界的 "USB-C 接口" —— 提供统一的协议让大语言模型（LLM）连接各种外部能力。

### 核心类比

| 概念 | USB-C | MCP |
|------|-------|-----|
| 连接双方 | 设备 ↔ 外设 | LLM ↔ 工具/数据 |
| 标准化 | 统一物理接口 | 统一 JSON-RPC 协议 |
| 即插即用 | 插上就能用 | 配置即能用 |
| 多厂商 | 苹果/三星/小米通用 | OpenAI/Anthropic/Google 通用 |

## 二、MCP 架构

```
┌──────────────────────────────────────────────────┐
│                   MCP Host                       │
│  ┌──────────────┐         ┌──────────────────┐   │
│  │  LLM (Claude  │ ────── │  MCP Client      │   │
│  │  GPT, etc.)  │         │  (协议客户端)     │   │
│  └──────────────┘         └────────┬─────────┘   │
└────────────────────────────────────┼─────────────┘
                                     │ JSON-RPC 2.0
                          ┌──────────┼──────────┐
                          │ stdio │ SSE │ Stream │
                          └──────────┼──────────┘
                                     │
┌────────────────────────────────────┼─────────────┐
│                          ┌────────▼─────────┐   │
│                          │  MCP Server      │   │
│                          │  (协议服务端)     │   │
│                          └────────┬─────────┘   │
│                   ┌──────────────┼──────────┐   │
│              ┌────▼───┐    ┌────▼───┐  ┌───▼──┐│
│              │ Tools  │    │Resources│  │Prompts││
│              └────────┘    └────────┘  └──────┘│
│                   MCP Server                    │
└─────────────────────────────────────────────────┘
```

### 三个核心角色

1. **MCP Host**：AI 应用本身（如 Claude Desktop、VS Code 插件）
2. **MCP Client**：Host 内部的协议客户端，管理与 Server 的连接
3. **MCP Server**：提供工具/资源/提示的外部程序

### 三层能力模型

| 层级 | 名称 | 说明 | 示例 |
|------|------|------|------|
| **Tools** | 工具 | LLM 可调用的函数 | 查数据库、发邮件、算数学 |
| **Resources** | 资源 | LLM 可读取的数据 | 文件内容、API 响应、知识库 |
| **Prompts** | 提示 | 预定义的提示模板 | "代码审查检查清单"、"翻译助手" |

## 三、MCP 协议分层

```
Layer 5: 能力层  → Tools / Resources / Prompts
Layer 4: 方法层  → tools/list, tools/call, resources/read ...
Layer 3: 消息层  → JSON-RPC 2.0 (request/response/notification)
Layer 2: 传输层  → stdio / SSE / Streamable HTTP
Layer 1: 连接层  → 进程管道 / HTTP / WebSocket
```

### 生命周期

```
Client                          Server
  │                                │
  │──── initialize ──────────────→│  ① 能力协商
  │←─── {capabilities} ──────────│
  │                                │
  │──── initialized (notification)─→│  ② 就绪通知
  │                                │
  │──── tools/list ──────────────→│  ③ 发现能力
  │←─── [{name, schema}...] ─────│
  │                                │
  │──── tools/call ──────────────→│  ④ 调用工具
  │←─── {content: [...]} ────────│
  │                                │
  │──── ping ────────────────────→│  ⑤ 心跳（可选）
  │←─── {} ──────────────────────│
```

## 四、传输模式对比

| 维度 | stdio | SSE | Streamable HTTP |
|------|-------|-----|-----------------|
| **通信范围** | 仅本地 | 本地+远程 | 本地+远程 |
| **底层协议** | 进程 stdin/stdout | HTTP + SSE | HTTP |
| **端点数量** | 无（管道） | 2 个 | 1 个 |
| **会话管理** | 进程生命周期 | 需 sessionId | 可选/无状态 |
| **多客户端** | ❌ | ✅ | ✅ |
| **服务端推送** | ✅ (stdout) | ✅ (SSE event) | ✅ (可选 SSE) |
| **部署复杂度** | 最低 | 中等 | 最低 |
| **防火墙友好** | N/A | ✅ | ✅ |
| **水平扩展** | ❌ | 需要 sticky session | ✅ 天然支持 |
| **推荐场景** | 本地工具 | Web 集成 | **推荐首选** |

## 五、实现细节

### JSON-RPC 2.0 消息格式

```json
// 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": { "name": "add", "arguments": { "a": 1, "b": 2 } }
}

// 响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "content": [{ "type": "text", "text": "3" }] }
}

// 通知（无 id，不期待响应）
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

### 初始化握手

Initialize 是 MCP 连接建立的第一步，双方交换能力声明：

```
Client → Server: {
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},      // 客户端能力
    "clientInfo": { "name": "...", "version": "..." }
  }
}

Server → Client: {
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {        // 服务端能力
      "tools": {}            // 支持工具
    },
    "serverInfo": { "name": "...", "version": "..." }
  }
}

Client → Server: { "method": "notifications/initialized" }
```

## 六、注意事项

### 安全

1. **stdio 模式**：服务端运行在用户权限下，信任边界是"本地进程"
2. **SSE/Stream 模式**：暴露 HTTP 端点，需要：
   - 启用 HTTPS（生产环境）
   - 添加认证（OAuth / API Key）
   - 限制 CORS 来源
   - 输入验证（永远不要信任客户端参数）
3. **工具安全**：
   - 避免命令注入
   - 限制工具的能力范围（最小权限原则）
   - 对敏感操作添加确认机制
4. **数据安全**：
   - 不要在日志中打印敏感参数
   - 注意工具返回的数据可能被 LLM 记录

### 错误处理

```python
# 服务端应捕获异常，返回错误内容（不抛异常以免断开连接）
try:
    return dispatch_tool(name, args or {})
except Exception as error:
    msg = str(error)
    return [types.TextContent(type="text", text=f"错误: {msg}")]
```

### 性能

1. **stdio**：进程间通信开销极小，适合高频调用
2. **SSE**：长连接复用，但需管理 session 开销
3. **Streamable HTTP**：无状态，每次请求独立；适合无服务器架构

### 版本兼容

- 协议版本：`"2024-11-05"`（当前稳定版本）
- SDK 遵循语义化版本，大版本变更可能有不兼容
- 永远在 initialize 中协商协议版本

## 七、调试技巧

```bash
# stdio 模式 —— 直接启动（日志输出到 stderr）
python src/stdio/server.py

# SSE 模式 —— 启动服务端
python src/sse/server.py

# Stream 模式 —— 启动服务端
python src/stream/server.py

# SSE/Stream 模式 —— 使用 curl 测试端点
curl http://localhost:3100/health
curl http://localhost:3100/sse       # 观察 SSE 事件流
curl -X POST http://localhost:3200/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# 查看 JSON-RPC 消息（日志通过 Python logging 输出到 stderr）
```
