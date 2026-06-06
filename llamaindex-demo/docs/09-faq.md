# ❓ LlamaIndex 常见问题汇总

## API 与配置

### Q: 可以用 DeepSeek 吗？
可以。DeepSeek API 完全兼容 OpenAI 格式。在 `.env` 中设置：
```
DEEPSEEK_API_KEY=sk-your-key
USE_LOCAL_EMBEDDING=true
```
LLM 走 DeepSeek（≈￥1/百万 token），嵌入走本地模型（免费）。

### Q: 不配置任何 API 密钥能用吗？
可以用 Mock 模式。实验 1/2/3/7/8 完全不受影响——索引创建、结构演示、
持久化等功能全部可用。只有实验 4/5/6 的实际 LLM 查询无法运行。

### Q: 怎么切换嵌入模型？
`.env` 中设置：
- `USE_LOCAL_EMBEDDING=true` → BAAI/bge-small-zh-v1.5（免费）
- 不设置 → MockEmbedding（演示用，零成本）
- 或代码中：`Settings.embed_model = OpenAIEmbedding(...)`

### Q: DeepSeek 和 OpenAI 费用差多少？
| 模型 | 输入 | 输出 | 百万 token 总成本 |
|------|------|------|-------------------|
| DeepSeek | ￥1 | ￥2 | ≈￥1.5 |
| GPT-4o-mini | $0.15 | $0.60 | ≈$0.4 |
| GPT-4o | $2.50 | $10 | ≈$6 |

DeepSeek 约为 GPT-4o-mini 的 1/3 价格，且质量接近 GPT-4。

---

## 基础概念

### Q: LlamaIndex 和 LangChain 到底什么关系？
LlamaIndex 专注于「数据索引与检索」，LangChain 是「LLM 应用编排框架」。
两者的定位不同，但可以组合使用。

### Q: 什么是 RAG？
RAG = Retrieval-Augmented Generation（检索增强生成）。
先把知识库索引化，用户提问时检索相关内容，再把内容提供给 LLM 生成答案。
核心价值：让 LLM 基于「真实文档」回答，减少幻觉。

### Q: 为什么需要索引？
LLM 的上下文有限（且 token 很贵）。你不可能把所有文档塞进 prompt 里。
索引让你在海量数据中快速找到「最相关的几段」，只把这部分发给 LLM。

### Q: Node 和 Document 有什么区别？
Document 是原始输入（如一个 PDF 文件）。Node 是 Document 被切分后的小片段。
Node 是检索的最小单元。一个 Document 通常会产生多个 Node。

---

## 实战问题

### Q: chunk_size 设多少合适？
取决于文档类型和使用场景：
- 技术文档/FAQ：256-512 tokens（追求精准匹配）
- 长文章/报告：512-1024 tokens（保留更多上下文）
- 极短答案（如定义）：128-256 tokens
- 建议从 512 开始，根据检索效果调整

### Q: chunk_overlap 设多少？
通常设为 chunk_size 的 10-20%。重叠能避免句子被从中间切断，保持语义连贯。

### Q: similarity_top_k 设多少？
- 简单事实查询：3-5
- 需要综合信息的查询：5-10
- k 越大 → context 越长 → token 消耗越多 → 回答越全面
- 建议从 5 开始

### Q: 可以用本地模型吗？
可以。LlamaIndex 支持 Ollama、HuggingFace 等本地模型。
本项目已内置 BAAI/bge-small-zh-v1.5（嵌入）和 DeepSeek（LLM）的支持。

### Q: 生产环境需要什么？
至少需要：
1. 嵌入模型（本地 BGE / OpenAI）
2. LLM（DeepSeek / GPT-4 / 本地模型）
3. 向量数据库（从 Chroma 开始即可）

---

## 进阶问题

### Q: 混合检索（Hybrid Search）是什么？
向量检索 + 关键词检索（BM25）的组合。
向量擅长语义理解，关键词擅长精确匹配。
两者结合能同时捕捉「意思相近」和「表述精确」的结果。

### Q: Reranker 是什么？
在检索之后、生成之前，用专门的模型对检索结果重新排序。
检索用轻量级嵌入（快），rerank 用重量级模型（准）。
这是提升 RAG 精度的常见手段。

### Q: 如何处理检索不到的情况？
1. 降低 similarity_cutoff 阈值
2. 改用混合检索
3. 改进文档切分策略
4. 增加文档覆盖范围
5. 使用查询重写（Query Rewriting）

### Q: 可以增量更新索引吗？
可以。LlamaIndex 支持：
- `insert()`：插入新文档
- `delete()`：删除文档
- `refresh()`：刷新嵌入
- IngestionPipeline 的增量模式

## 成本优化

### Q: 如何最大限度降低 RAG 成本？
1. **LLM**：用 DeepSeek（$0.14/百万 token）替代 GPT-4o（$2.5/百万 token）
2. **嵌入**：用本地 BGE 模型替代 OpenAI 嵌入（嵌入费用直接归零）
3. **缓存**：持久化索引避免反复嵌入
4. **精简**：减少 similarity_top_k，用 compact 模式
5. **评估**：定期检查检索质量，避免无效的 LLM 调用
