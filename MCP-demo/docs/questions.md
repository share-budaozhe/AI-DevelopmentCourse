# 启发性问题

## 🏗️ 架构与设计

### Q1: 为什么 MCP 选择 JSON-RPC 2.0 而不是 REST 或 gRPC？
> 提示：思考 AI 调用的特点 —— 工具调用是"函数调用"语义，不是"资源操作"语义。

### Q2: stdio 模式如何保证消息边界？如果 JSON 内容本身包含换行符怎么办？
> 提示：思考 NDJSON 的序列化策略。

### Q3: SSE 模式为什么需要两个端点（GET /sse + POST /mcp）？能否合并为一个？
> 提示：SSE 规范的限制是什么？Streamable HTTP 如何解决的？

### Q4: 如果 SSE 连接断开，正在执行的工具调用会怎样？如何设计可靠的重连机制？
> 提示：工具调用可能是长时间运行的操作。

### Q5: 为什么 Streamable HTTP 被称为"无状态"？如果服务端需要推送进度通知，无状态还能工作吗？
> 提示：思考 sessionId 在有状态 vs 无状态模式下的角色。

## 🔌 传输层

### Q6: 在什么场景下你应该选择 stdio 而不是 SSE/Streamable HTTP？
> 提示：考虑部署环境、安全要求、性能需求。

### Q7: 客户端如何发现 MCP Server 提供了哪些工具？
> 提示：查看 MCP 协议的方法列表。

### Q8: 为什么 SSE 模式中 `res.on("close")` 的清理逻辑至关重要？漏写会导致什么问题？
> 提示：思考 transport Map 的内存泄漏。

### Q9: 三种传输模式中，哪一种最适合 Serverless（如 AWS Lambda）部署？为什么？
> 提示：Serverless 的本质是"短生命周期 + 无状态"。

### Q10: Streamable HTTP 模式下，客户端的 `Accept` header 设置为 `text/event-stream` vs `application/json` 有什么区别？
> 提示：一个可以持续推送，一个是一次性响应。

## 🛡️ 安全与错误处理

### Q11: MCP 工具调用中，为什么推荐返回 `{ isError: true }` 而不是抛出异常？
> 提示：思考异常对连接状态的影响。

### Q12: 如果一个 MCP Server 提供了"执行任意 Shell 命令"的工具，有哪些安全风险？如何缓解？
> 提示：考虑命令注入、权限控制、审计日志。

### Q13: 如何防止恶意客户端通过超大参数或恶意构造的 inputSchema 攻击 MCP Server？
> 提示：Zod Schema 验证能做什么？还需要什么？

## 🚀 进阶思考

### Q14: 如果要让多个 MCP Client 共享同一个 MCP Server 的状态（如共享数据库连接池），应该如何设计？
> 提示：考虑 stdio 模式天然不支持多客户端，HTTP 模式如何处理？

### Q15: MCP 协议当前不支持"流式工具调用结果"（即工具边执行边返回中间结果）。如果你来设计这个扩展，会如何修改协议？
> 提示：思考 JSON-RPC 通知 + content 分片的可能性。

### Q16: 设计一个 MCP Server 的认证方案，要考虑三种不同传输模式各自的特点。
> 提示：stdio 模式依赖 OS 进程权限；HTTP 模式可加 Bearer Token。

### Q17: 如果工具调用需要数分钟（如大数据分析），客户端应如何设计超时和取消机制？
> 提示：JSON-RPC 没有内置取消语义；考虑 notifications/cancelled。

### Q18: 对比 MCP 和 OpenAI Function Calling / Plugin 系统，MCP 的核心优势是什么？
> 提示：思考"开放协议" vs "厂商绑定"的区别。
