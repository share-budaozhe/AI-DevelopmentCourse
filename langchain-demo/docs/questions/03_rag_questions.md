# Demo 03 启发性问题 -- RAG

## 基础理解

1. `RecursiveCharacterTextSplitter` 的 `chunk_size` 和 `chunk_overlap`
   分别如何影响检索质量? 过大或过小会有什么后果?

2. 向量数据库 (Chroma) 和传统数据库 (MySQL/PostgreSQL) 的核心区别是什么?
   为什么 RAG 场景下需要向量数据库?

3. Embedding 模型 `text-embedding-3-small` 的维度是多少?
   维度和检索精度、速度的关系是什么?

## 深入思考

4. 检索到的 Top-K 文档中可能包含与问题无关的内容 (噪声)。
   除了增加 K 值，还有哪些策略可以提高检索精度?

5. RAG 中的 "Lost in the Middle" 问题是什么?
   在构建 Prompt 时如何缓解?

6. 如果需要支持多语言检索 (中文查询找英文文档)，
   Embedding 模型需要具备什么特性? `text-embedding-3-small` 是否支持?

## 实战挑战

7. 当前的 RAG Prompt 将所有文档片段拼接在一起。如果文档总量超过 LLM 的
   context window，会发生什么? 设计一个处理方案。

8. 如何评估一个 RAG 系统的质量? 设计 3-5 个评估指标和对应的测试方法。

9. 如果每 10 分钟就有一批新文档需要索引，如何设计增量更新的策略?
