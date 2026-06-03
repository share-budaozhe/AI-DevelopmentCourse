# 测试与试运行指南

本文档说明如何在本地部署 MCP Demo 的三种传输模式，并以 **Codex CLI** 作为 MCP Host 进行端到端测试。

---

## 一、环境准备

### 1.1 依赖安装

```bash
# Node.js 依赖
npm install

# Python 依赖（推荐使用虚拟环境）
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e .
```

### 1.2 版本要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Node.js | 18+ | 运行 TypeScript 服务端/客户端 |
| Python | 3.10+ | 运行 Python 版服务端/客户端 |
| Codex CLI | 最新版 | MCP Host，用于端到端测试 |

### 1.3 先确认 Codex CLI 已可用

```bash
codex --version
```

如果未安装，参考 [Codex CLI 文档](https://github.com/openai/codex) 安装。

---

## 二、快速冒烟测试（不依赖 Codex）

在接入 Codex 之前，先用自带的客户端确认各模式服务端能正常工作。

### 2.1 stdio 模式

```bash
# 客户端自动 spawn 子进程，无需手动启动服务端
npm run dev:stdio-client
```

预期输出：

```
==================================================
MCP stdio 模式客户端演示
==================================================
✓ 已连接到 stdio 服务端
--- 获取工具列表 (tools/list) ---
可用工具数: 3
  · add: 两个数相加
  · greet: 发送问候
  · get_time: 获取当前服务器时间
--- 调用 add ---
结果: 10 + 20 = 30
...
✓ 已关闭连接
```

### 2.2 SSE 模式

```bash
# 终端 A：启动 SSE 服务端
npm run dev:sse-server
# 输出：[sse-server] MCP SSE 服务已启动: http://localhost:3100

# 终端 B：运行 SSE 客户端
npm run dev:sse-client
```

### 2.3 Streamable HTTP 模式

```bash
# 终端 A：启动 Stream 服务端
npm run dev:stream-server
# 输出：[stream-server] MCP Streamable HTTP 服务已启动: http://localhost:3200

# 终端 B：运行 Stream 客户端
npm run dev:stream-client
```

> **提示**：也可用 `curl` 快速验证服务端是否启动成功：
> ```bash
> curl http://localhost:3100/health   # SSE 模式
> curl http://localhost:3200/health   # Stream 模式
> ```

---

## 三、Codex 集成测试

Codex CLI 作为 MCP Host，通过配置 `mcp_servers` 来连接 MCP Server。配置后，Codex 内的 LLM 即可发现并调用 Demo 提供的 `add`、`greet`、`get_time` 三个工具。

### 3.1 配置方式

在项目根目录创建 `.codex/config.toml`（项目级配置），或在 `~/.codex/config.toml`（全局配置）中添加 MCP Server 定义。

> **推荐**：使用项目级配置 `.codex/config.toml`，便于和项目代码一起管理。

### 3.2 stdio 模式 —— 最简集成

`.codex/config.toml`：

```toml
[mcp_servers.mcp-demo-stdio]
command = "npx"
args = ["tsx", "src/stdio/server.ts"]
```

说明：
- `command`：启动服务端的命令。这里用 `npx tsx` 直接运行 TypeScript 源码。
- `args`：传给 `tsx` 的服务端入口文件。
- Codex 启动时会自动 spawn 该子进程，通过 stdin/stdout 通信。进程随 Codex 退出而终止。

**验证步骤**：

1. 确保已执行 `npm install`
2. 在项目根目录创建 `.codex/config.toml`，填入上述配置
3. 在项目目录下启动 Codex CLI：
   ```bash
   codex
   ```
4. 在 Codex 交互界面中尝试：
   ```
   > 帮我算一下 123 + 456 等于多少？用 add 工具。
   > 用中文问候"小明"，用 greet 工具。
   > 查询一下现在的北京时间，用 get_time 工具。
   ```
5. 观察 Codex 是否正确发现并调用了工具。若成功，LLM 会通过 MCP 协议发起 `tools/list` → `tools/call` 并展示结果。

### 3.3 Streamable HTTP 模式 —— 推荐远程方案

**步骤 1**：先在终端启动 Stream 服务端（保持运行）：

```bash
npm run dev:stream-server
```

**步骤 2**：配置 `.codex/config.toml`：

```toml
[mcp_servers.mcp-demo-stream]
url = "http://localhost:3200/mcp"
```

说明：
- Streamable HTTP 使用单端点，`url` 直接指向 `/mcp`。
- 服务端需要在 Codex 启动前独立运行（不会被 Codex 管理生命周期）。
- 无状态设计，无需 session 管理，天然支持多 Codex 实例并行连接。

**验证步骤**：

1. 保持 `npm run dev:stream-server` 在终端运行
2. 在项目根目录创建/更新 `.codex/config.toml`，添加上述配置
3. 启动 Codex：
   ```bash
   codex
   ```
4. 用同样的提示词测试三个工具

### 3.4 SSE 模式 —— 有状态 HTTP 方案

**步骤 1**：先启动 SSE 服务端：

```bash
npm run dev:sse-server
```

**步骤 2**：配置 `.codex/config.toml`：

```toml
[mcp_servers.mcp-demo-sse]
url = "http://localhost:3100/sse"
```

说明：
- `url` 指向 SSE 端点 `/sse`。
- Codex 的 MCP 客户端会自动完成 SSE 连接 → 接收 endpoint 事件 → POST 消息的完整流程。
- SSE 是有状态模式，每个 Codex 实例建立独立的 SSE 长连接。

**验证步骤**：与 Stream 模式相同。

> ⚠️ 注意：SSE 模式正逐渐被 Streamable HTTP 取代。新项目推荐优先使用 Stream 模式。

---

## 四、Python 版服务端测试

Demo 同时提供 Python 实现，位于 `src/*/server.py` 和 `src/*/client.py`。

### 4.1 Python 客户端冒烟测试

```bash
# 先激活虚拟环境
.venv\Scripts\activate

# stdio 模式
python -m src.stdio.client

# SSE 模式（需先启动服务端）
python -m src.sse.server
# 另一个终端
python -m src.sse.client

# Stream 模式（需先启动服务端）
python -m src.stream.server
# 另一个终端
python -m src.stream.client
```

### 4.2 Python 服务端 + Codex

stdio 模式配置（Codex 通过 `python` 启动 Python 服务端）：

```toml
[mcp_servers.mcp-demo-py-stdio]
command = "python"
args = ["-m", "src.stdio.server"]
```

Stream/SSE 模式与 TypeScript 版配置完全相同，只需先用 Python 启动服务端：

```bash
python -m src.stream.server   # 或 src.sse.server
```

---

## 五、调试技巧

### 5.1 确认 Codex 已加载 MCP Server

启动 Codex 后，可以询问：

```
> 你有哪些可用的工具？
```

如果配置正确，应该能在工具列表中看到 `add`、`greet`、`get_time`。

### 5.2 查看服务端日志

| 模式 | 日志位置 |
|------|----------|
| stdio | 服务端 `console.error()` / `logging` 输出到 **stderr**，Codex 可能将其记录到日志文件 |
| SSE/Stream | 服务端终端直接输出到 stdout |

### 5.3 常见问题排查

**问题 1：Codex 启动后看不到 MCP 工具**

- 检查 `.codex/config.toml` 格式是否正确（TOML 语法）
- 对于 stdio 模式，确认 `npx tsx` 可用（执行 `npx tsx --version`）
- 对于 HTTP 模式，确认服务端正在运行（`curl http://localhost:3x00/health`）
- 确认 Codex 的工作目录是项目根目录

**问题 2：stdio 模式报 ECONNREFUSED**

- stdio 不需要网络端口，检查 `npx tsx src/stdio/server.ts` 是否能独立运行

**问题 3：SSE/Stream 模式连接被拒**

- 确认服务端已启动且端口未被占用
- 检查防火墙是否阻止了本地端口

**问题 4：工具调用返回错误**

- 检查服务端终端的错误日志
- 对于 stdio，错误会打印到 stderr
- 对于 HTTP，错误的 HTTP 状态码和响应体会显示在 Codex 中

### 5.4 使用 curl 直接调试 MCP 协议

```bash
# Stream 模式：直接发送 JSON-RPC 请求
curl -X POST http://localhost:3200/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}"

# 调用 add 工具
curl -X POST http://localhost:3200/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":1,\"b\":2}}}"

# SSE/Stream 模式的 health 检查
curl http://localhost:3100/health
curl http://localhost:3200/health
```

---

## 六、完整测试流程速查

```bash
# ===== 1. 安装依赖 =====
npm install
python -m venv .venv && .venv\Scripts\activate && pip install -e .

# ===== 2. 冒烟测试 =====
npm run dev:stdio-client           # stdio 自测
# (两个终端) npm run dev:sse-server | npm run dev:sse-client
# (两个终端) npm run dev:stream-server | npm run dev:stream-client

# ===== 3. 创建 .codex/config.toml（三选一或全部启用）=====
# [mcp_servers.mcp-demo-stream]
# url = "http://localhost:3200/mcp"

# ===== 4. 启动服务端（HTTP 模式需要）=====
npm run dev:stream-server

# ===== 5. 启动 Codex 并测试 =====
codex
```

---

## 七、推荐配置（生产级）

对于日常使用，推荐 **Streamable HTTP** 模式搭配以下 `.codex/config.toml`：

```toml
# MCP Demo —— Streamable HTTP（推荐）
[mcp_servers.mcp-demo]
url = "http://localhost:3200/mcp"

# 备选：stdio 模式（无需单独启动服务端）
# [mcp_servers.mcp-demo-stdio]
# command = "npx"
# args = ["tsx", "src/stdio/server.ts"]
```

日常使用时：

1. 先启动 Stream 服务端：`npm run dev:stream-server`
2. 再启动 Codex：`codex`
3. 即可在对话中调用 `add`、`greet`、`get_time` 工具
