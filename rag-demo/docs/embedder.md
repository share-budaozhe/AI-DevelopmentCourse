# Embedder — TF-IDF 嵌入向量生成模块

## 文件位置

[src/embedder.py](../src/embedder.py)

## 在 RAG 中的角色

`Embedder` 是 RAG 流水线中**文本 → 向量**的关键转换器。它将自然语言文档转换为机器可计算的数值向量，使得"两段文本有多相似"这个问题可以通过**向量距离**来精确衡量。

```
文档文本 ──→ [Embedder] ──→ 数值向量 (如 [0.12, 0.0, 0.34, ...])
查询文本 ──→ [Embedder] ──→ 数值向量
                                    │
                            └── 向量距离 = 语义相似度 ──┘
```

---

## 核心算法：TF-IDF 详解

本模块使用 **TF-IDF（Term Frequency - Inverse Document Frequency）** 算法，它是一种基于词频统计的文本向量化方法，属于经典的**稀疏向量表示**（相对于深度学习中的稠密 Embedding）。

### 公式

```
TF-IDF(t, d, D) = TF(t, d) × IDF(t, D)

其中：
  t = 某个词（term）
  d = 某篇文档（document）
  D = 整个文档集合（corpus）
```

### 第一层：TF（词频，Term Frequency）

```
TF(t, d) = 词 t 在文档 d 中出现的次数 / 文档 d 的总词数
```

**直觉**：一篇文章中反复出现"机器学习"，那么这篇文章大概率与机器学习相关。

**为什么要除以总词数？**—— 防止长文档在比较中天然占优势。一篇 10000 词的文章出现 5 次"算法" vs 一篇 100 词的文章出现 5 次"算法"，显然后者与"算法"更相关。

**代码位置**：`_tfidf_vector()` 第 67-72 行

```python
for token in tokens:
    if token in self.vocabulary:
        vec[self.vocabulary[token]] += 1
vec = vec / len(tokens)   # 长度归一化
```

### 第二层：IDF（逆文档频率，Inverse Document Frequency）

```
IDF(t, D) = log( |D| / DF(t) )

其中：
  |D|  = 语料库中文档总数
  DF(t) = 包含词 t 的文档数（Document Frequency）
```

**直觉**：
| 词 | 出现的文档 | DF | IDF 含义 |
|---|---|---|---|
| "的" | 几乎每篇 | → 总文档数 | IDF ≈ log(1) = 0 → **权重极低** |
| "量子计算" | 只有 2 篇 | → 2 | IDF ≈ log(总文档数/2) → **权重很高** |

- 高频常见词（"的"、"是"、"the"）→ IDF 趋近于 0 → 被自动忽略
- 低频专业词（"量子纠缠"）→ IDF 高 → 一旦出现就极具区分力

**代码位置**：`fit()` 第 48-56 行

```python
# 统计每个词的文档频率（每篇文档只计一次）
df = np.zeros(vocab_size)
for tokens in tokenized_docs:
    unique_tokens = set(tokens)    # ⬅ 关键：去重！一篇文档中出现多次也只算 1
    for token in unique_tokens:
        if token in self.vocabulary:
            df[self.vocabulary[token]] += 1

# 平滑版 IDF：log((N+1)/(df+1)) + 1
self.idf = np.log((doc_count + 1) / (df + 1)) + 1
```

**知识点：IDF 平滑（Smoothing）**

为什么不用原始公式 `log(N/df)` 而是 `log((N+1)/(df+1)) + 1`？

1. **`df+1` 防止除零**：词表中的词可能在语料中从未出现（如用户查询中的新词），此时 df=0，分母为 0 会崩溃
2. **`N+1` 防止 log(0)**：如果 df=N（所有文档都包含该词），log(N/N)=log(1)=0，加了 +1 保证下界不为负
3. **`+1` 保证 IDF ≥ 1**：避免 IDF < 1 时过度压低 TF 权重

### 第三层：L2 归一化

**代码位置**：`_tfidf_vector()` 第 77-80 行

```python
norm = np.linalg.norm(vec)   # 计算向量长度（欧几里得范数）
if norm > 0:
    vec = vec / norm           # 缩放为单位长度
```

**为什么需要 L2 归一化？**

1. **余弦相似度 = 点积**：两个单位向量的点积就等于它们的余弦相似度，省去每次计算余弦的除法开销
2. **消除长度偏差**：长文档天然包含更多词，向量分量更大。归一化后所有文档在同一起跑线上比较
3. **计算加速**：后续 `VectorStore.search()` 中直接用 `np.dot()` 计算相似度，前提就是向量已归一化

```
点积:  A · B = |A| × |B| × cos(θ)
当 |A| = |B| = 1 时:  A · B = cos(θ)   ← 即两个向量的夹角的余弦值
```

---

## 类结构解析

```
Embedder
├── vocabulary: Dict[str, int]    # 词 → 索引映射（如 {"机器学习": 0, "python": 1, ...}）
├── idf: np.ndarray               # 每个词的 IDF 值（长度 = 词表大小）
├── _fitted: bool                 # 是否已完成 fit
│
├── fit(documents) → self         # 学习：构建词表 + 计算 IDF
├── embed(texts) → np.ndarray     # 转换：文本列表 → 向量矩阵 (N, dim)
├── embed_query(query) → np.ndarray  # 转换：单个查询 → 向量 (dim,)
├── _tokenize(text) → List[str]   # 分词：中文单字 + 英文单词
├── _tfidf_vector(tokens) → np.ndarray  # 核心：TF-IDF + L2归一化
└── dimension: int                # 属性：向量维度（= 词表大小）
```

### `_tokenize()` — 分词器（第 26-31 行）

```python
def _tokenize(self, text: str) -> List[str]:
    tokens = re.findall(r'[一-鿿]|[a-zA-Z]+|\d+', text.lower())
    return tokens
```

**知识点**：这是一个极简分词器，支持中英混合文本：

| 正则片段 | 匹配内容 | 示例 |
|---|---|---|
| `[一-鿿]` | 单个中文字符（Unicode 中日韩统一表意文字） | "机"、"器"、"学"、"习" |
| `[a-zA-Z]+` | 连续英文字母 | "python"、"numpy" |
| `\d+` | 连续数字 | "2024"、"42" |

- **中文**：按**单字**切分（"机器学习" → "机" / "器" / "学" / "习"），这是最简单的做法；生产级系统应使用 jieba 等分词库
- **英文**：按**单词**切分（自动 `.lower()` 统一大小写）

### `fit()` — 学习阶段（第 33-58 行）

接收整个文档语料，做两件事：

1. **构建词表**：遍历所有文档，收集不重复的词汇，按字母排序后分配索引
2. **计算 IDF**：统计每个词出现在多少篇文档中，套用平滑公式得出 IDF 向量

这相当于"让模型先看一遍所有文档，了解每个词的稀有程度"。

### `embed()` — 转换阶段（第 84-98 行）

将文本直接转为 TF-IDF 向量矩阵。如果还没 `fit()`，则自动以输入文本为语料完成 fit。

### `embed_query()` — 查询转换（第 100-102 行）

本质是 `embed()` 的单条包装，专用于将用户查询转为向量。

---

## TF-IDF 的优劣

| 维度 | 评价 |
|---|---|
| **速度** | ⚡ 极快，无需 GPU，纯 CPU 毫秒级 |
| **可解释性** | ⭐ 优秀，可以直接看到每个词对相似度的贡献 |
| **依赖** | ✅ 零外部依赖，仅需 NumPy |
| **语义理解** | ❌ 无法识别同义词（"好听" vs "悦耳" 向量完全不同） |
| **词序** | ❌ 忽略词序（"狗咬人" vs "人咬狗" 向量完全相同） |
| **OOV（未登录词）** | ❌ 查询中出现训练时未见过的词会被直接丢弃 |
| **维度膨胀** | ❌ 词表多大向量就多长（但可通过稀疏存储缓解） |
| **适用场景** | 中小规模文档库、关键词匹配、快速原型 |

---

## 知识扩展：从 TF-IDF 到稠密 Embedding

| 特性 | TF-IDF（本模块） | 稠密 Embedding（如 BGE、OpenAI） |
|---|---|---|
| 向量类型 | 稀疏（大部分分量为 0） | 稠密（所有分量非零） |
| 维度 | = 词表大小（可达数万） | 固定（如 768、1536） |
| 语义捕获 | 仅词频统计 | 深度学习语义理解 |
| 训练方式 | 纯统计，无训练 | 预训练 + 微调 |
| 同义词处理 | ❌ | ✅（"悦耳" ≈ "好听"） |
| 多语言 | 需分词适配 | 多语言模型原生支持 |
| 生产建议 | 关键词检索 / 第一路召回 | 语义检索 / 主召回 |

现代 RAG 系统常用的策略是**混合检索**：TF-IDF/BM25 做关键词召回 + 稠密 Embedding 做语义召回，两者互补。
