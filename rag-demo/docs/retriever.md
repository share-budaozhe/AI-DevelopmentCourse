# Retriever — 检索模块

## 文件位置

[src/retriever.py](../src/retriever.py)

## 在 RAG 中的角色

`Retriever` 是 RAG 流水线中**连接检索与生成的桥梁**。它封装了向量检索的全部过程，并负责将原始检索结果**后处理、格式化**为 LLM 可直接消费的上下文文本。

```
用户查询 "什么是监督学习？"
         │
         ▼
   Retriever.retrieve(query)
         │
         ├── 1. embedder.embed_query(query)    → 查询向量
         ├── 2. store.search(query_vec, top_k) → Top-K 原始结果
         ├── 3. 相似度过滤 (min_score)         → 筛除低质量结果
         └── 4. 封装为 SearchResult            → 结构化输出
         │
         ▼
   Retriever.format_context(results)
         │
         └── 拼接为 LLM 上下文文本
         │
         ▼
   送入 Generator 生成答案
```

---

## 类结构

```
SearchResult (dataclass)     — 单条检索结果的数据结构
    ├── text: str            — 文档块文本
    ├── source: str          — 来源文件名
    ├── score: float         — 相似度分数
    └── chunk_id: str        — 块唯一标识

Retriever                    — 检索器
    ├── store                — 向量存储
    ├── embedder             — 嵌入模型
    ├── top_k: int           — 返回结果数上限
    ├── min_score: float     — 最低相似度阈值
    │
    ├── retrieve(query) → List[SearchResult]   — 执行检索
    └── format_context(results) → str           — 格式化为 LLM 上下文
```

---

## 核心方法详解

### `retrieve()` — 检索主流程（第 35-58 行）

```python
def retrieve(self, query: str) -> List[SearchResult]:
    # 1. 查询向量化
    query_vec = self.embedder.embed_query(query)

    # 2. 向量检索
    hits = self.store.search(
        query_embedding=query_vec.tolist(),
        top_k=self.top_k,
    )

    # 3. 后处理：相似度过滤
    results = []
    for hit in hits:
        if hit["score"] < self.min_score:
            continue                            # ← 低于阈值，丢弃
        results.append(SearchResult(
            text=hit["text"],
            source=hit["metadata"].get("source", "未知"),
            score=hit["score"],
            chunk_id=hit["id"],
        ))
    return results
```

#### 知识点 1：为什么需要 `min_score` 过滤？

即使是最相关的 Top-K 结果，有些可能仍然**完全无关**。

```
假设知识库里只有"机器学习"和"Python"两个领域的文档
查询："如何做红烧肉？"
    ↓
向量检索无论如何都会返回 5 个结果（因为 Top-K=5）
但所有结果的相似度分数可能在 0.01 ~ 0.05 之间（极低）
    ↓
如果不加过滤，这些无关内容会混入 LLM 的上下文
LLM 可能基于无关内容"强行编造"答案 → 幻觉（Hallucination）
```

设置 `min_score=0.1`（示例）可以筛掉这些低质量结果，让 `format_context` 返回 `"（未找到相关文档）"`，LLM 就能诚实地说"我不知道"，而非瞎编。

#### 知识点 2：`tolist()` 的必要性

```python
query_vec = self.embedder.embed_query(query)  # 返回 np.ndarray
hits = self.store.search(
    query_embedding=query_vec.tolist(),        # 转为 Python list
    ...
)
```

这是因为某些实现/扩展中，JSON 序列化或跨进程传递需要原生 Python 类型，NumPy 数组类型（如 `np.float64`）可能不被接受。

### `format_context()` — 上下文组装（第 60-70 行）

```python
def format_context(self, results: List[SearchResult]) -> str:
    if not results:
        return "（未找到相关文档）"

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"【文档{i}】(来源: {r.source}, 相关度: {r.score:.2f})\n{r.text}"
        )
    return "\n\n".join(parts)
```

**输出示例**：

```
【文档1】(来源: machine_learning.txt, 相关度: 0.85)
监督学习是机器学习的主要类型之一，使用带标签的训练数据进行学习...

【文档2】(来源: rag_explained.txt, 相关度: 0.62)
RAG通过检索外部知识库中的相关文档来增强LLM的回答质量...

【文档3】(来源: python_intro.txt, 相关度: 0.31)
Scikit-learn是Python的机器学习算法库，提供统一的API接口...
```

**格式设计要点**：
- `【文档N】` 标记让 LLM 能区分不同来源
- `来源: xxx` 让 LLM 能标注引用出处
- `相关度: 0.85` 让 LLM 知道哪个文档更可信（可据此加权引用）
- `\n\n` 分隔让 LLM 能清晰区分文档边界

---

## 在 RAG 流水线中的定位

```
                    ┌──────────────────────┐
                    │     Retriever        │
                    │                      │
   embedder ──────→ │  embed_query()       │  将查询转为向量
   store ─────────→ │  store.search()      │  执行相似度检索
                    │  min_score 过滤      │  筛除低质量结果
                    │  format_context()    │  拼接为 LLM 上下文
                    │                      │
                    └──────┬───────────────┘
                           │
                           ▼
                     Generator.generate()
```

Retriever 不关心：
- 文档是如何加载和分块的（那是 Loader 的事）
- 向量是如何生成的（那是 Embedder 的事）
- 答案是如何生成的（那是 Generator 的事）

Retriever 只关心：
- **检索**：拿到查询，找到相关文档
- **过滤**：筛掉不够好的结果
- **格式化**：让结果以最佳形态呈现给 LLM

这就是**单一职责原则**（Single Responsibility Principle）的体现——每个模块只做一件事，做好。

---

## SearchResult 数据结构（第 11-18 行）

```python
@dataclass
class SearchResult:
    text: str           # 文档块的文本内容
    source: str         # 来源文件名（如 "machine_learning.txt"）
    score: float        # 相似度分数（余弦相似度，0~1）
    chunk_id: str       # 块ID（如 "chunk_3"），用于溯源
```

每一个 `SearchResult` 都是检索流水线的**最终输出单元**。后续 Generator 拿到这些结果后，只需要遍历它们来构建回答。

---

## 知识扩展：检索后处理技术

本模块实现了最基础的 `min_score` 过滤，生产级 RAG 系统通常还有更多后处理步骤：

| 技术 | 原理 | 解决的问题 |
|---|---|---|
| **相似度过滤**（本项目） | 丢弃 score < 阈值的 | 避免无关内容混入上下文 |
| **MMR（最大边际相关性）** | 选结果时同时优化相关性和多样性 | 避免 Top-K 都是同一主题的重复内容 |
| **Re-ranking** | 用更强的交叉编码器模型重新打分 | 向量相似度 ≠ 语义相关性，re-rank 更准 |
| **上下文压缩** | 用 LLM 先"压缩"检索结果再回答 | 节省上下文窗口，去除冗余 |
| **多路召回 + 融合** | TF-IDF/BM25 + Embedding 双路检索，加权合并 | 取长补短，提高召回率 |
| **时间衰减** | 较旧的文档降低权重 | 优先使用最新信息 |

### MMR（Maximal Marginal Relevance）简介

```
普通 Top-K：选相似度最高的 5 个
  结果：[A1, A2, A3, A4, A5]  ← 5个结果都在讲"监督学习"，同质化严重

MMR Top-K：平衡相关性和多样性
  结果：[A1, B1, C1, D1, E1]  ← 分别讲"监督学习"、"无监督"、"强化学习"、"评估"、"过拟合"
         └─ 高相关 ─┘└────────── 高多样性 ──────────┘
```

MMR 的贪心选择公式：

```
MMR = argmax[ λ × Similarity(D_i, Q) - (1-λ) × max Similarity(D_i, D_j∈已选) ]
              └──── 相关性 ────┘        └──────── 多样性惩罚 ────────┘
```

λ=1 时退化为普通 Top-K；λ=0.5 时相关性和多样性权重各半。
