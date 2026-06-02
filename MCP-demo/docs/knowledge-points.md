# MCP 知识点汇总

## 📚 基础概念

| # | 知识点 | 说明 |
|---|--------|------|
| 1 | **MCP 是什么** | Model Context Protocol —— AI 模型与外部工具/数据交互的标准化协议 |
| 2 | **三层能力** | Tools（可调用函数）、Resources（可读取数据）、Prompts（提示模板） |
| 3 | **JSON-RPC 2.0** | MCP 的消息协议基础，所有通信都遵循 request/response/notification 模式 |
| 4 | **NDJSON** | stdio 模式使用的行分隔 JSON 格式，每行一个完整的 JSON 对象 |
| 5 | **协议版本** | 当前稳定版本 `"2024-11-05"`，通过 initialize 握手协商 |

## 🔌 传输层

| # | 知识点 | 说明 |
|---|--------|------|
| 6 | **stdio 模式** | 进程 stdin/stdout 通信，最基础、最可靠，仅限本地 |
| 7 | **SSE 模式** | 基于 HTTP 的 Server-Sent Events，双端点设计（GET /sse + POST /mcp） |
| 8 | **Streamable HTTP** | MCP 最新传输方式（2025），单端点 POST，无状态设计，推荐首选 |
| 9 | **Session 管理** | SSE 需要 sessionId 关联请求和连接；Streamable HTTP 默认无状态 |
| 10 | **Accept Header 协商** | Streamable HTTP 客户端可通过 Accept header 请求 JSON 或 SSE 响应格式 |

## 🏗️ 架构模式

| # | 知识点 | 说明 |
|---|--------|------|
| 11 | **Host-Client-Server 三角** | Host(LLM应用) → Client(协议客户端) → Server(工具提供者) |
| 12 | **能力协商** | initialize 阶段双方交换 capabilities，声明各自支持的功能 |
| 13 | **请求-响应匹配** | JSON-RPC 通过 `id` 字段将请求和响应配对 |
| 14 | **通知 (Notification)** | 无 `id` 字段的消息，不期待响应，用于事件推送 |
| 15 | **inputSchema 驱动** | MCP 使用 JSON Schema 定义工具参数类型，Python 通过 type annotations 提供类型安全 |

## 🔧 工具实现

| # | 知识点 | 说明 |
|---|--------|------|
| 16 | **Tool 定义三要素** | name（唯一标识）、description（LLM理解用途）、inputSchema（参数schema） |
| 17 | **工具错误处理** | 捕获异常并返回错误内容的 `TextContent`，而非抛出异常（避免连接断开） |
| 18 | **content 数组** | 工具返回值是 content 数组，支持多类型（text、image、resource 等） |
| 19 | **handler 注册** | 使用装饰器 `@server.list_tools()` / `@server.call_tool()` 注册处理器 |
| 20 | **最小权限原则** | 每个工具只暴露必要的能力，避免"万能工具" |

## 🛡️ 安全

| # | 知识点 | 说明 |
|---|--------|------|
| 21 | **信任边界** | stdio=本地进程、SSE/Stream=网络端点，安全策略因模式而异 |
| 22 | **输入验证** | 永远不要信任客户端参数，使用 inputSchema 验证 + 业务校验 |
| 23 | **命令注入防护** | 避免字符串拼接构建命令；使用参数化调用 + `shell=False` |
| 24 | **敏感数据** | 不要将敏感参数打印到日志；工具返回值注意脱敏 |
| 25 | **CORS / HTTPS** | 生产环境 SSE/Stream 服务应启用 HTTPS 和适当的 CORS 策略 |

## 🚀 性能与运维

| # | 知识点 | 说明 |
|---|--------|------|
| 26 | **stdio 开销** | 进程间通信，极低延迟，适合高频调用 |
| 27 | **SSE 连接复用** | 长连接避免重复握手，但需要管理连接池 |
| 28 | **水平扩展** | Streamable HTTP 天然支持，SSE 需要 sticky session |
| 29 | **连接泄漏** | 使用 `async with` 上下文管理器自动清理 transport |
| 30 | **优雅关闭** | 服务端应处理 SIGTERM，关闭活跃连接后再退出 |

## 🐍 Python SDK 要点

| # | 知识点 | 说明 |
|---|--------|------|
| 31 | **asyncio 异步** | Python MCP SDK 全面基于 asyncio，所有 handler 都是 async 函数 |
| 32 | **装饰器注册** | Python SDK 使用装饰器 `@server.list_tools()` 注册 handler，风格 Pythonic |
| 33 | **类型注解** | 使用 `dict | None`（PEP 604）和 `list[types.TextContent]` 提供类型提示 |
| 34 | **上下文管理器** | `async with` 自动管理 transport 生命周期，确保资源清理 |
| 35 | **启动方式** | 客户端用 `python src/stdio/server.py`，HTTP 模式用 `uvicorn` ASGI 服务器 |
