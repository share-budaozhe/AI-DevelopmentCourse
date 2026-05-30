# LangChain 学习 Demo -- 项目概览

## 项目目标

本项目通过 5 个递进的 Demo，覆盖 LangChain 框架的核心应用场景。
每个 Demo 都是可独立运行的 Python 脚本，配有详细的知识点说明、启发性问题和参考答案。

## 架构总览

```
用户输入
    |
    v
+---------+    +-----------+    +-----------+
| Prompt   | -> | LLM       | -> | Output    |
| Template |    | (OpenAI/  |    | Parser    |
|          |    | DeepSeek) |    |           |
+---------+    +-----------+    +-----------+
    |                |
    v                v
+---------+    +-----------+
| Memory  |    | Tools     |
|         |    | (Agent)   |
+---------+    +-----------+
    |                |
    v                v
+-----------------------------+
| Retrieval (Vector Store)    |
| Document -> Split -> Embed  |
+-----------------------------+
```

## 学习路径

| 阶段 | Demo | 核心知识 | 前置要求 |
|------|------|----------|----------|
| 入门 | 01 基础 | Model I/O, Prompt, Parser | 无 |
| 进阶 | 02 Chains | LCEL, Runnable 组合 | Demo 01 |
| 进阶 | 03 RAG | 文档检索、向量存储 | Demo 01 |
| 高级 | 04 Agents | Tools, ReAct, 自主决策 | Demo 01, 02 |
| 高级 | 05 Memory | 对话历史、会话管理 | Demo 01, 02 |

## 技术栈

- **框架**: LangChain 1.x + LangGraph
- **LLM 后端**: OpenAI (GPT-4o-mini) / DeepSeek (deepseek-chat)
- **向量数据库**: ChromaDB
- **Embedding**: OpenAI text-embedding-3-small
- **配置管理**: python-dotenv

## 如何切换 LLM 后端

编辑 `.env` 文件:
```bash
# 使用 DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-你的key

# 或使用 OpenAI (默认)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-你的key
```

注意: DeepSeek 目前不提供 Embedding API，因此 Demo 03 (RAG) 中的向量化仍需 OpenAI API。
