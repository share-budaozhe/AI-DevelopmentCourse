# 📇 LlamaIndex 学习 — 索引类型与原理

## 什么是索引？

索引是 LlamaIndex 的核心数据结构，它把「文档」组织成「可被高效检索」的形式。
类比：书籍的目录让你快速找到某一章，数据库的 B+Tree 让你快速找到某条记录，
LlamaIndex 的索引让你快速找到跟问题最相关的文本片段。

## VectorStoreIndex（向量索引）

### 原理
1. 将每个 Node 用嵌入模型转为向量（一串浮点数）
2. 存入向量数据库
3. 查询时：把问题也转为向量 → 用余弦相似度找最相似的 Top-K

### 内部流程
```
文档 → NodeParser 切分 → 嵌入模型 → 向量 → 向量库
                                          ↓
查询 → 嵌入模型 → 查询向量 → 余弦相似度 → Top-K 节点 → LLM 生成
```

### 代码
```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("什么是 RAG？")
```

### 适用场景
- ✅ 事实性问答（"Python 是谁创建的？"）
- ✅ 精准信息检索
- ✅ 需要语义理解的搜索
- ❌ 全局摘要（"所有文档讲了什么？"）—— 不擅长

---

## SummaryIndex（摘要索引）

### 原理
维护一个节点的顺序列表。检索时按顺序遍历所有节点。

### 代码
```python
from llama_index.core import SummaryIndex

index = SummaryIndex.from_documents(documents)
query_engine = index.as_query_engine(response_mode="tree_summarize")
```

### 适用场景
- ✅ 文档摘要
- ✅ "全面了解某主题"
- ✅ 少量文档（< 100 个节点）
- ❌ 海量文档 → 全量扫描太慢

---

## 索引对比

| 特性 | VectorStoreIndex | SummaryIndex |
|------|----------------|-------------|
| 检索原理 | 向量相似度 | 顺序扫描 |
| 需要嵌入 | ✅ | ❌ |
| 查询速度 | 快（ANN） | 慢（全扫描） |
| 精准度 | 高 | 中 |
| 适用文档量 | 无限 | < 10000 节点 |
| 典型用例 | 客服机器人 | 报告摘要 |

---

## 其他索引类型（进阶）

- **KeywordTableIndex**：基于关键词 → 节点的映射表
- **KnowledgeGraphIndex**：实体 → 关系 → 实体的知识图谱
- **TreeIndex**：树形层次结构
- **ComposableGraph**：组合多个索引的「索引之索引」

---

## 选择指南

```
问自己：用户通常怎么查询？

"XX 是什么？" → VectorStoreIndex
"总结一下"   → SummaryIndex  
"包含 XX 关键词的有哪些？" → KeywordTableIndex
"A 和 B 有什么关系？" → KnowledgeGraphIndex
"既要精准又要全局" → ComposableGraph（组合多个索引）
```
