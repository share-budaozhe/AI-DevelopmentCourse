# RAG Demo — 模块详解文档

本目录包含 RAG Demo 项目中每个核心模块的详细技术解释。

## 文档索引

| 模块 | 文件 | 在 RAG 中的角色 |
|---|---|---|
| **Embedder** | [embedder.md](embedder.md) | 文本 → 向量（TF-IDF 算法详解） |
| **Loader** | [loader.md](loader.md) | 文档读取 → 清洗 → 分块（Chunking 策略） |
| **Store** | [store.md](store.md) | 向量存储与相似度检索（Top-K 算法） |
| **Retriever** | [retriever.md](retriever.md) | 检索编排 + 后处理 + 上下文格式化 |
| **Generator** | [generator.md](generator.md) | LLM 答案生成 + 本地降级模式 |

## RAG 流水线全景

```
                    ┌─────────────────────┐
                    │    Loader           │
                    │  文档加载 + 分块     │
                    │  (loader.py)        │
                    └─────────┬───────────┘
                              │ List[Chunk]
                              ▼
                    ┌─────────────────────┐
                    │    Embedder         │
                    │  TF-IDF 向量化      │
                    │  (embedder.py)      │
                    └─────────┬───────────┘
                              │ np.ndarray (N, dim)
                              ▼
                    ┌─────────────────────┐
                    │    Store            │
                    │  向量存储 + 检索     │
                    │  (store.py)         │
                    └─────────┬───────────┘
                              │ ↑
                              │ │ add() / search()
                              ▼ │
                    ┌─────────────────────┐
                    │    Retriever        │
                    │  检索编排 + 格式化   │
                    │  (retriever.py)     │
                    └─────────┬───────────┘
                              │ str (上下文)
                              ▼
                    ┌─────────────────────┐
                    │    Generator        │
                    │  LLM 答案生成       │
                    │  (generator.py)     │
                    └─────────┬───────────┘
                              │
                              ▼
                         最终回答
```

## 阅读顺序建议

1. [**Loader**](loader.md) — 理解文档如何进入系统，什么是分块（Chunking）
2. [**Embedder**](embedder.md) — 理解 TF-IDF 原理，文本如何变成向量
3. [**Store**](store.md) — 理解向量如何存储，相似度检索怎么做
4. [**Retriever**](retriever.md) — 理解检索流程编排、过滤和格式化
5. [**Generator**](generator.md) — 理解 LLM 如何基于检索结果生成答案

每个文档都包含：
- 模块在 RAG 中的角色定位
- 类结构和方法详解（含代码引用）
- 关键知识点的深度解释
- 知识扩展：从当前实现到生产级方案
