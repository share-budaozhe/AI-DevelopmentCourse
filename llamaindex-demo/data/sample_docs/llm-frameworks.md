# LangChain vs LlamaIndex：两大 LLM 框架对比

## 定位差异

LangChain 是一个通用的 LLM 应用开发框架，目标是成为"LLM 应用的瑞士军刀"。
它提供了链（Chain）、代理（Agent）、工具（Tool）、记忆（Memory）等抽象，
让你可以把 LLM、工具、数据源灵活组合。

LlamaIndex 则专注于"数据与 LLM 之间的桥梁"。它的核心使命是：
把各种格式的数据（PDF、网页、数据库、API）索引化，让 LLM 能够高效检索和推理。

## 核心概念对比

| 概念 | LangChain | LlamaIndex |
|------|-----------|------------|
| 数据加载 | Document Loaders | Data Connectors (Reader) |
| 文本分割 | Text Splitters | Node Parser |
| 向量存储 | VectorStore | VectorStoreIndex |
| 检索 | Retriever | Retriever |
| 问答 | RetrievalQA Chain | QueryEngine |
| 对话 | ConversationChain | ChatEngine |
| 代理 | Agent + Tools | Agent + Tools |

## 什么时候用哪个？

- 用 LangChain：需要复杂的链式调用、多步骤工作流、与各种外部 API 集成
- 用 LlamaIndex：需要构建 RAG 系统、文档问答、知识库检索
- 两者可以结合：在 LangChain 的 Agent 中使用 LlamaIndex 的 QueryEngine 作为工具

## 学习建议

建议先学 LlamaIndex 理解 RAG 的核心原理，再学 LangChain 掌握复杂编排。
因为 LlamaIndex 的抽象层次更清晰：文档 → 节点 → 索引 → 检索引擎 → 查询引擎。
理解了这个流程，RAG 就掌握了大半。
