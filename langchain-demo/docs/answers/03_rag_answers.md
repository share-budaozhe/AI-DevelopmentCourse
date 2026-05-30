# Demo 03 参考答案 -- RAG

## 1. chunk_size 和 chunk_overlap 的影响

**chunk_size 过大**: 单个块包含过多信息，检索精度下降，LLM context 也可能浪费
**chunk_size 过小**: 语义断裂，关键信息被切散，检索到的片段不够完整

**chunk_overlap 过大**: 冗余存储，存储成本增加，检索结果重复
**chunk_overlap 过小**: 边界信息丢失，关键内容可能恰好在分界处被切断

经验值:
- 一般文档: chunk_size=500, overlap=50
- 代码文档: chunk_size=1000, overlap=200 (函数边界很重要)
- QA 对: chunk_size=200, overlap=20

## 2. 向量数据库 vs 传统数据库

| 维度 | 传统数据库 | 向量数据库 |
|------|-----------|-----------|
| 查询方式 | 精确匹配 (WHERE name='...') | 相似度搜索 (语义相近) |
| 索引结构 | B-Tree, Hash | HNSW, IVF |
| 结果 | 精确结果 | Top-K 近似结果 |
| 典型场景 | OLTP, 报表 | 语义搜索, 推荐, RAG |

RAG 需要 "找出与用户问题语义最相似的文档片段"，
这不是精确匹配能解决的，所以需要向量数据库。

## 3. text-embedding-3-small 维度

`text-embedding-3-small`: 默认 1536 维，可通过 `dimensions` 参数降低 (如 512 维)

维度与性能的关系:
- 高维度: 精度更高，但存储和检索更慢
- 低维度: 速度更快，存储更省，但可能牺牲一些精度
- 1536 -> 512 维: 存储减少 67%，检索速度翻倍，MTEB 基准下精度仅下降约 2%

## 4. 提高检索精度

- **重排序 (Re-Ranking)**: 检索 Top-20 后用 Cross-Encoder 精排到 Top-3
- **HyDE**: 先用 LLM 生成假设性答案，用答案做向量检索
- **多路召回**: 关键词 (BM25) + 向量 (Dense) 双路召回 + 融合排序
- **元数据过滤**: 按日期/类别/来源预过滤
- **Query 改写**: 用 LLM 将用户问题改写为更精确的检索查询

## 5. "Lost in the Middle" 问题

LLM 对 Prompt 开头和结尾的内容关注度最高，中间部分容易被忽略。
在 RAG 中，将最相关的文档放在开头和结尾可缓解此问题。

缓解策略:
- 将高相关性文档放在 Prompt 的开头和结尾
- 每个文档片段加上清晰的分隔标记
- 限制检索数量 (k <= 5)，避免中间文档过多

## 6. 多语言检索

`text-embedding-3-small` 支持多语言，中文查询可以检索到英文文档。
但精度不如单语言场景。提升多语言效果的方法:
- 使用 `text-embedding-3-large` (更高维度，多语言效果更好)
- 使用专用的多语言模型 (如 `multilingual-e5-large`)
- 先将查询翻译为目标语言再检索

## 7. Context Window 溢出

当检索到的文档总量超过 LLM 的 context window (如 128K tokens):

方案 A: Map-Reduce
```python
# 将文档分批，每批独立生成答案，再合并
```

方案 B: Refine
```python
# 逐批处理，每批基于前一批的答案进行补充
```

方案 C: 限制检索量
```python
# 控制 k 值，确保总 token 数 < context window 的 80%
```

## 8. RAG 质量评估

指标:
1. **忠实度 (Faithfulness)**: 回答是否基于检索到的文档 (而非幻觉)
2. **答案相关性 (Answer Relevance)**: 回答是否直接回应了问题
3. **上下文相关性 (Context Relevance)**: 检索到的文档是否与问题相关
4. **上下文召回率 (Context Recall)**: 是否检索到了所有必要信息
5. **端到端延迟**: 从提问到得到回答的时间

工具: RAGAS 框架自动评估, 或人工标注 + BLEU/ROUGE 分数

## 9. 增量更新策略

```python
# 方案: 新增文档时追加向量，定期重建索引
def incremental_update(new_files):
    loader = DirectoryLoader(new_files, ...)
    new_docs = loader.load()
    splits = splitter.split_documents(new_docs)
    vectorstore.add_documents(splits)
    # 可选: 记录文档指纹，避免重复索引
```
