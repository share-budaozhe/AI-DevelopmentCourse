# MCP 协议学习 Demo

基于 `@modelcontextprotocol/sdk` 实现的 MCP 三种传输模式完整示例。

## 快速开始

```bash
npm install
```

## 三种模式

| 模式 | 服务端 | 客户端 | 特点 |
|------|--------|--------|------|
| **stdio** | `npm run dev:stdio-server` | `npm run dev:stdio-client` | 进程管道，最基础 |
| **SSE** | `npm run dev:sse-server` | `npm run dev:sse-client` | HTTP 长连接，双端点 |
| **Stream** | `npm run dev:stream-server` | `npm run dev:stream-client` | 单端点，无状态，推荐 |

## 项目结构

```
src/
├── common/
│   ├── types.ts          # JSON-RPC 2.0 类型 & MCP 协议常量
│   └── tools.ts          # 共享工具定义 & 处理器
├── stdio/
│   ├── server.ts         # stdio 服务端
│   └── client.ts         # stdio 客户端
├── sse/
│   ├── server.ts         # SSE 服务端
│   └── client.ts         # SSE 客户端
└── stream/
    ├── server.ts         # Streamable HTTP 服务端
    └── client.ts         # Streamable HTTP 客户端
docs/
├── overview.md           # MCP 协议概述（原理、架构、注意事项）
├── stdio-mode.md         # stdio 模式详解
├── sse-mode.md           # SSE 模式详解
├── stream-mode.md        # Streamable HTTP 模式详解
├── knowledge-points.md   # 30 个知识点汇总
├── questions.md          # 18 个启发性问题
├── testing.md           # 测试与试运行指南（Codex 集成）
└── answers.md            # 问题参考答案
```

## 示例工具

Demo 提供了三个示例工具，所有模式共享相同的工具实现：

- **add**: 加法运算 —— 演示数值参数
- **greet**: 多语言问候 —— 演示字符串枚举参数
- **get_time**: 时区时间查询 —— 演示可选参数 & 错误处理

## 技术栈

- TypeScript + Node.js
- `@modelcontextprotocol/sdk` (v1.29)
- Express (SSE/Stream 服务端)
- Zod (Schema 验证)
- tsx (TypeScript 执行)

## 测试指南

详细的本地部署、Codex 集成测试步骤请参阅：[docs/testing.md](docs/testing.md)
