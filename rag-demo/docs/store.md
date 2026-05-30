# Store — 向量存储与检索模块

## 文件位置

[src/store.py](../src/store.py)

## 在 RAG 中的角色

`VectorStore` 是 RAG 系统的**记忆中枢**。它负责存储所有经过向量化的文档块，并提供高速的**相似度检索**能力——给定一个查询向量，快速找出最相似的 Top-K 个文档块。

```
构建阶段（离线）:                   查询阶段（在线）:
  Embedder 输出的向量                  Embedder 输出的查询向量
       │                                     │
       ▼                                     ▼
  VectorStore.add()                   VectorStore.search()
       │                                     │
       ▼                                     ▼
  持久化到磁盘                       返回 Top-K 最相似文档块
  (vector_store.json)
```

---

## 为什么不用数据库？

本模块使用**纯 NumPy + JSON** 实现，而非 ChromaDB / Milvus / FAISS 等专业向量数据库。这是一个刻意的设计选择：

| 方案 | 优点 | 缺点 |
|---|---|---|
| 纯 NumPy（本项目） | 零依赖、可读性高、适合学习和原型 | 不支持百万级数据、无并发 |
| FAISS (Meta) | 十亿级向量、GPU 加速 | C++ 依赖、安装复杂 |
| ChromaDB | 轻量级、API 友好 | 额外进程/依赖 |
| Milvus | 分布式、生产级 | 运维成本高 |

---

## 类结构

```
VectorStore
├── ids: List[str]              # 每个块的唯一标识 ["chunk_0", "chunk_1", ...]
├── documents: List[str]        # 原始文本内容
├── metadatas: List[dict]       # 元数据 [{source, chunk_index}, ...]
├── embeddings: np.ndarray      # 向量矩阵 (N, dim)
├── persist_path: str           # 持久化文件路径
│
├── add(ids, embeddings, ...)   # 批量添加文档向量
├── search(query_emb, top_k)    # 余弦相似度检索 Top-K
├── count()                     # 返回文档块总数
├── clear()                     # 清空所有数据
├── _save()                     # 持久化到 JSON
└── _load()                     # 从 JSON 恢复
```

---

## 核心方法详解

### `add()` — 批量添加（第 28-48 行）

```python
def add(self, ids, embeddings, documents, metadatas=None):
    self.ids.extend(ids)
    self.documents.extend(documents)
    self.metadatas.extend(metadatas)

    if self.embeddings is None:
        self.embeddings = embeddings                     # 首次添加，直接赋值
    else:
        self.embeddings = np.vstack([self.embeddings, embeddings])  # 追加行
    self._save()
```

**知识点：`np.vstack` vs `np.concatenate`**

```python
# np.vstack 是垂直堆叠的语法糖：
np.vstack([A, B])  ≡  np.concatenate([A, B], axis=0)

# 示例
A = np.array([[1, 2, 3]])      # shape (1, 3)
B = np.array([[4, 5, 6]])      # shape (1, 3)
np.vstack([A, B])               # shape (2, 3) → [[1,2,3], [4,5,6]]
```

每次 `add()` 后自动调用 `_save()`，保证数据**即时持久化**。

### `search()` — 相似度检索（第 50-80 行）

这是整个 RAG 系统的**检索核心**。

```python
def search(self, query_embedding, top_k=5):
    # 余弦相似度
    similarities = np.dot(self.embeddings, query_embedding)

    # Top-K 选择
    if len(similarities) <= top_k:
        top_indices = np.argsort(similarities)[::-1]              # 全部排序
    else:
        top_indices = np.argpartition(similarities, -top_k)[-top_k:]  # 部分排序
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

    # 组装结果
    hits = []
    for idx in top_indices:
        hits.append({
            "id": self.ids[idx],
            "text": self.documents[idx],
            "metadata": self.metadatas[idx],
            "score": round(float(similarities[idx]), 4),
        })
    return hits
```

#### 知识点 1：为什么点积 = 余弦相似度？

```
余弦相似度: cos(θ) = (A · B) / (|A| × |B|)

当 A 和 B 都经过 L2 归一化（|A| = |B| = 1）:
cos(θ) = A · B / (1 × 1) = A · B = np.dot(A, B)
```

这也是为什么 `Embedder._tfidf_vector()` 中要做 L2 归一化的关键原因 —— 它让检索时只需一次 `np.dot()` 就完成了相似度计算，将时间复杂度从 O(dim) 降为 O(dim)，但去掉了除法操作。

#### 知识点 2：`np.argsort` vs `np.argpartition` —— Top-K 性能优化

```python
# 场景 A：数据量小（≤ top_k）—— 直接全排序
top_indices = np.argsort(similarities)[::-1]

# 场景 B：数据量大（> top_k）—— 使用分区算法
top_indices = np.argpartition(similarities, -top_k)[-top_k:]
top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
```

**为什么这样做？** 这是经典的 **Top-K 查询优化**：

| 算法 | 时间复杂度 | 原理 |
|---|---|---|
| `argsort`（全排序） | O(N log N) | 对所有元素排序 |
| `argpartition`（部分排序） | O(N) | 只保证第 K 大的元素在正确位置，其余分两堆 |

```
假设 10,000 个文档向量，取 Top-5：

argsort:      排序 10,000 个 → O(10000 × log(10000)) ≈ O(133,000)
argpartition: 分成 "Top-5候选" 和 "其余" 两堆 → O(10000)
               然后只对 5 个候选排序 → O(5 × log(5))

性能差距：约 13 倍
```

`argpartition(a, -k)` 将数组分成两部分：[-k:] 包含最大的 k 个元素（但不保证它们的内部顺序），所以最后还需要对这 k 个做一次小范围 argsort。

### `_save()` / `_load()` — 持久化机制（第 95-113 行）

```python
def _save(self):
    data = {
        "ids": self.ids,
        "documents": self.documents,
        "metadatas": self.metadatas,
        "embeddings": self.embeddings.tolist() if self.embeddings is not None else [],
    }
    with open(self.persist_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

**知识点：`ndarray.tolist()` 的必要性**

NumPy 数组不能直接 JSON 序列化：

```python
json.dumps({"vec": np.array([1, 2, 3])})
# ❌ TypeError: Object of type ndarray is not JSON serializable

json.dumps({"vec": np.array([1, 2, 3]).tolist()})
# ✅ '{"vec": [1, 2, 3]}'
```

**`ensure_ascii=False`**：保证中文字符直接写入 JSON，而非转义为 `\uXXXX` 形式，保持文件可读性。

---

## JSON 持久化格式

存储到 `vector_store.json` 的数据结构如下：

```json
{
  "ids": ["chunk_0", "chunk_1", "chunk_2", "..."],
  "documents": [
    "机器学习是人工智能的一个分支...",
    "Python是一种高级编程语言...",
    "..."
  ],
  "metadatas": [
    {"source": "machine_learning.txt", "chunk_index": 0},
    {"source": "python_intro.txt", "chunk_index": 0},
    "..."
  ],
  "embeddings": [
    [0.023, 0.0, 0.0, 0.145, ...],
    [0.0, 0.089, 0.0, 0.0, ...],
    "..."
  ]
}
```

**注意**：这是全量序列化，没有任何索引结构。当文档量达到数万级别时，这个 JSON 文件会变得巨大，每次加载都全量读入内存——这正是专业向量数据库需要解决的问题之一。

---

## 数据流全景

```
┌─────────────────────────────────────────────────────┐
│                    VectorStore                       │
│                                                     │
│  内存: embeddings (N, dim)  ← NumPy 矩阵             │
│        documents [N]         ← 文本列表               │
│        metadatas [N]         ← 元数据列表             │
│                                                     │
│  search(query_vec, top_k=5)                         │
│    │                                                │
│    ├─ similarities = dot(embeddings, query_vec)     │
│    │    shape: (N,) → 每个文档的相似度分数            │
│    │                                                │
│    ├─ argpartition → Top-K 索引                     │
│    │                                                │
│    └─ 组装: [{id, text, metadata, score}, ...]      │
│                                                     │
│  持久化: vector_store.json                           │
│    _save() ← add() 自动触发                         │
│    _load() ← __init__() 自动触发                    │
└─────────────────────────────────────────────────────┘
```

---

## 知识扩展：专业向量数据库的核心技术

本模块是最简实现，生产级向量数据库还解决以下问题：

| 问题 | 本模块 | 生产方案 |
|---|---|---|
| **近似检索** | 精确（暴力遍历全部向量） | ANN 算法（HNSW、IVF、PQ），牺牲微小精度换巨大速度 |
| **索引结构** | 无（线性扫描） | 图索引（HNSW）、倒排索引（IVF）、量化（PQ） |
| **维度灾难** | 高维下余弦相似度退化 | 降维、稀疏表示、混合检索 |
| **增量更新** | 全量重写 JSON | B-tree / LSM-tree 变体 |
| **并发** | 不支持（单线程） | MVCC、读写锁 |
| **分布式** | 不支持 | 分片（sharding）+ 副本（replication） |
| **过滤** | 无 | 标量过滤 + 向量过滤的混合查询 |

**HNSW（Hierarchical Navigable Small World）** 是当前最主流的 ANN 索引算法之一，ChromaDB、Weaviate 内部都使用它。核心思想是构建多层图结构，查询时从顶层跳跃到目标区域，再逐层细化——类似于"先看地图找到大致方向，再临近时仔细辨认"。
