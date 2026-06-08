# 🔍 LlamaIndex 学习 — 检索器深入理解

## 什么是检索器？

检索器（Retriever）是从索引中查找与查询最相关节点的组件。
它是 RAG 流程的核心环节——**检索质量直接决定生成质量**。

## 检索流程

```
用户查询: "如何优化 Python 性能？"
    │
    ▼
[1] 查询嵌入 → 向量化查询文本
    │
    ▼
[2] 相似度计算 → 用余弦相似度比较查询向量和所有文档向量
    │
    ▼
[3] Top-K 筛选 → 取相似度最高的 K 个节点
    │
    ▼
[4] 返回 NodeWithScore 列表 → 传给 LLM 生成答案
```

## 核心参数

### similarity_top_k
控制返回多少个节点。

```python
retriever = index.as_retriever(similarity_top_k=5)
nodes = retriever.retrieve("什么是 RAG？")
# 返回 5 个最相关的节点
```

- 太小 → 可能遗漏关键信息
- 太大 → 上下文过长，token 浪费
- 推荐：3-10

### similarity_cutoff（可选）
最低相似度阈值，低于此值的结果被丢弃。

```python
retriever = index.as_retriever(
    similarity_top_k=10,
    similarity_cutoff=0.7,  # 只保留相似度 >= 0.7 的
)
```

## 检索模式

### 1. 默认模式（向量检索）
纯语义相似度，标准选择。

### 2. 混合检索（Hybrid）
向量 + 关键词（BM25）组合，互补优势：
```python
# 需要向量数据库支持（如 Qdrant）
vector_store = QdrantVectorStore(
    client=client,
    collection_name="my_docs",
    enable_hybrid=True,
)
index = VectorStoreIndex.from_documents(docs, vector_store=vector_store)
```

### 3. 递归检索（Recursive）
层次化检索，先粗后细：
```python
# 先检索父节点 → 再检索其子节点
```

## NodeWithScore 结构

```python
for node in nodes:
    print(node.score)      # 相似度分数 (0-1)
    print(node.text)       # 节点文本
    print(node.metadata)   # 元数据（来源文件等）
    print(node.node_id)    # 唯一标识
```

## 检索质量提升建议

1. **提高 top_k** → 多取一些候选，让 LLM 自己筛选
2. **使用 reranker** → 检索后用更好的模型重新排序
3. **混合检索** → 向量 + 关键词，取长补短
4. **查询重写** → 把用户的模糊问题改写成更精准的查询
5. **元数据过滤** → 根据文档类别、日期等缩小检索范围
