# 📚 LlamaIndex 学习教程 — 项目总览

## 项目目标

这是一个「从零开始」的 LlamaIndex 学习项目。通过 8 个精心设计的实验，
你将掌握 RAG（检索增强生成）的完整知识体系。

## 🆕 三种运行模式

| 模式 | LLM | 嵌入 | 月成本 | 配置 |
|------|-----|------|--------|------|
| **DeepSeek + 本地嵌入** | deepseek-chat | BGE/HuggingFace | ≈￥5 | `DEEPSEEK_API_KEY` |
| **OpenAI** | gpt-4o-mini | OpenAI 嵌入 | ≈$5 | `OPENAI_API_KEY` |
| **Mock（零成本）** | 无 | MockEmbedding | ￥0 | 无需配置 |

项目通过 `src/config.py` 自动检测 `.env` 文件，选择最佳模式。
90% 的学习内容在 Mock 模式下即可完成。

## 核心理念

**LlamaIndex 是一个「数据与 LLM 之间的桥梁」**。

```
你的数据（PDF/网页/数据库...）
        │
        ▼
  LlamaIndex（加载 → 解析 → 索引 → 检索）
        │
        ▼
     LLM（DeepSeek / OpenAI / 本地模型）
```

## 核心概念速览

### 1. Document（文档）
LlamaIndex 的基本数据单元。一个 Document 包含：
- `text`：文本内容
- `metadata`：元数据（来源、作者、日期等）

### 2. Node（节点）
文档被切分后的片段。每个 Node 是检索的最小单元。
- 为什么要切分？→ LLM 上下文窗口有限，检索精度需要细粒度
- 怎么切？→ SentenceSplitter（按句子边界切，保留语义完整性）

### 3. Index（索引）
组织节点的数据结构。不同类型的索引有不同的检索方式：
- **VectorStoreIndex**：向量相似度检索（最常用）
- **SummaryIndex**：顺序列表检索（适合摘要）

### 4. Retriever（检索器）
从索引中查找相关节点的组件。
- `similarity_top_k`：返回多少个最相似节点
- `similarity_cutoff`：最低相似度阈值

### 5. QueryEngine（查询引擎）
端到端的问答接口：检索 → 合成 → 回答。
- `response_mode`：合成策略（compact/refine/tree_summarize）

### 6. ChatEngine（对话引擎）
带记忆的多轮对话接口。
- `CondenseQuestionChatEngine`：压缩历史+检索

### 7. Agent（智能体）
能自主选择工具、规划步骤来回答问题的智能体。
- `FunctionTool`：包装普通函数
- `QueryEngineTool`：包装查询引擎

### 8. Storage（存储）
索引的持久化和加载。
- 默认：文件系统
- 生产：向量数据库（Chroma/Qdrant/Pinecone/Milvus）

## 学习路线图

```
实验 1: 文档与节点     ← 起点：理解数据怎么进来
    ↓
实验 2: 索引类型       ← 核心：数据怎么组织
    ↓
实验 3: 检索器        ← 关键：怎么找到相关内容
    ↓
实验 4: 查询引擎      ← 目标：怎么生成答案（需要 API）
    ↓
实验 5: 对话引擎      ← 进阶：多轮对话（需要 API）
    ↓
实验 6: Agent         ← 高级：自主决策（需要 API）
    ↓
实验 7: 存储          ← 实战：持久化和生产
    ↓
实验 8: 进阶特性      ← 精通：管线、混合检索等
```

## 费用参考

| 组件 | DeepSeek 方案 | OpenAI 方案 |
|------|-------------|------------|
| LLM（每次查询） | ≈￥0.001 | ≈$0.0005 |
| 嵌入（每篇文档） | 免费（本地） | ≈$0.0001 |
| 完整做一遍 8 个实验 | ≈￥0.5 | ≈$1 |

## 适合谁？

- 正在学习 RAG 和 LLM 应用开发的初学者
- 准备技术面试的求职者（理解 RAG 原理）
- 需要快速上手 LlamaIndex 的工程师
- 对 AI + 数据检索感兴趣的学习者

## 前提知识

- Python 基础（函数、类、类型提示）
- LLM 基础概念（了解 GPT/ChatGPT 即可）
- 不需要：向量数据库经验、机器学习背景
