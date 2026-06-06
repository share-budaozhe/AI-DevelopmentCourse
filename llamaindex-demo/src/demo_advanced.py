"""
═══════════════════════════════════════════════════════════════
  🚀 LlamaIndex 学习教程 — src/demo_advanced.py
  实验 8：进阶特性实验
═══════════════════════════════════════════════════════════════

核心知识点：
- NodePostprocessor：检索后的节点后处理（重排序、过滤）
- IngestionPipeline：数据摄入管线
- 递归检索：父子节点递归
- 混合检索：向量 + 关键词
- Callbacks：可观测性
"""
from llama_index.core import (
    VectorStoreIndex, Settings, MockEmbedding,
)
from llama_index.core.postprocessor import SimilarityPostprocessor
from sample_data import DEMO_DOCUMENTS


def setup():
    Settings.embed_model = MockEmbedding(embed_dim=384)


def experiment_node_postprocessor():
    """🔬 实验 8.1：节点后处理器

    知识点：
    - NodePostprocessor 在检索后、生成前运行
    - 可以过滤低分节点、去重、重排序
    - 类似搜索引擎的"二次排序"
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 8.1：NodePostprocessor（节点后处理）")
    print(f"{'='*60}")

    print(f"""
  NodePostprocessor 工作流：

  用户问题
    ↓
  Retriever（检索 Top-K 节点）
    ↓
  NodePostprocessor（过滤/重排序）  ← 我们在这里
    ↓
  ResponseSynthesizer（LLM 生成答案）
    ↓
  最终回答

  常用后处理器：

  ┌────────────────────────────┬──────────────────────────────────┐
  │ SimilarityPostprocessor    │ 过滤低于分数阈值的节点            │
  │ KeywordNodePostprocessor   │ 要求节点包含/排除特定关键词       │
  │ MetadataReplacementPostProcessor │ 用元数据替换节点文本        │
  │ LongContextReorder         │ 将相关节点重新排序（长上下文优化） │
  │ SentenceTransformerRerank  │ 用专门的 rerank 模型重新打分      │
  └────────────────────────────┴──────────────────────────────────┘
""")


def experiment_ingestion_pipeline():
    """🔬 实验 8.2：数据摄入管线

    知识点：
    - IngestionPipeline 将加载、解析、嵌入整合为一条管线
    - 支持增量更新（自动跳过已处理的文档）
    - docstore 策略：upsert、duplicates 等
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 8.2：IngestionPipeline（数据摄入管线）")
    print(f"{'='*60}")

    print(f"""
  IngestionPipeline 是 LlamaIndex 的"数据处理流水线"：

  原始文档
    ↓
  [Reader] 读取文件
    ↓
  [Transformations] 转换处理：
    - 文本清理
    - 节点解析（SentenceSplitter）
    - 元数据提取
    - 嵌入生成
    ↓
  [Docstore] 存入文档存储
    ↓
  [VectorStore] 存入向量数据库

  使用场景：
  1. 首次导入大量文档
  2. 定期增量同步新文档
  3. 文档更新后重新索引

  示例代码：
  ```python
  from llama_index.core.ingestion import IngestionPipeline
  from llama_index.core.node_parser import SentenceSplitter

  pipeline = IngestionPipeline(
      transformations=[
          SentenceSplitter(chunk_size=512, chunk_overlap=50),
          Settings.embed_model,
      ],
  )

  nodes = pipeline.run(documents=docs)
  index = VectorStoreIndex(nodes)
  ```
""")


def experiment_recursive_retrieval():
    """🔬 实验 8.3：递归检索与混合检索

    知识点：
    - 递归检索：先找父节点，再深入子节点
    - 混合检索：向量 + 关键词，互补优势
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 8.3：递归检索与混合检索")
    print(f"{'='*60}")

    print(f"""
  1. 递归检索（Recursive Retrieval）：

     文档
      ├── 父节点 (摘要级别)
      │   ├── 子节点 1 (段落级)
      │   │   └── 叶节点 (句子级)
      │   ├── 子节点 2
      │   └── ...

     检索流程：
     ① 先用问题检索父节点（粗粒度）
     ② 在匹配的父节点下，再检索子节点（细粒度）
     ③ 返回最相关的叶节点

     使用场景：文档层次结构清晰（如技术手册：章→节→段）

  2. 混合检索（Hybrid Search）：

     向量检索：基于语义相似度，擅长理解"意思相近"
     + 关键词检索 (BM25)：基于词频，擅长精确匹配

     例如查询 "Python 3.12 新特性"：
     - 向量检索找到"Python 版本更新相关内容"
     - 关键词检索精确匹配 "3.12" 这个具体版本号
     - 混合排序综合两者的分数

  LlamaIndex 支持混合检索：
  ```python
  from llama_index.core import VectorStoreIndex
  from llama_index.vector_stores.xxx import XXXVectorStore

  vector_store = XXXVectorStore(enable_hybrid=True)
  index = VectorStoreIndex.from_documents(docs, vector_store=vector_store)
  ```
""")


def experiment_callbacks():
    """🔬 实验 8.4：可观测性与调试

    知识点：
    - CallbackManager 追踪每次 LLM 调用
    - 可用于调试、监控、成本追踪
    - LlamaTrace / LangSmith 等外部可观测平台
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 8.4：可观测性与 Callbacks")
    print(f"{'='*60}")

    print(f"""
  LlamaIndex 的可观测性：

  1. 内置 Callback 系统
     - on_retrieve_start / on_retrieve_end：追踪检索
     - on_query_start / on_query_end：追踪查询
     - on_llm_start / on_llm_end：追踪 LLM 调用

  2. 全局 token 计数
     - Settings.token_counter 统计所有 LLM 调用的 token 消耗
     - 用于监控成本和优化提示

  3. 外部平台集成
     - Arize Phoenix：开源可观测平台
     - LangSmith：LangChain 生态的调试平台
     - 自定义 CallbackHandler

  设置全局 Callback：
  ```python
  from llama_index.core import Settings
  from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

  token_counter = TokenCountingHandler()
  Settings.callback_manager = CallbackManager([token_counter])

  # ... 运行查询后 ...
  print(f"嵌入 Token: {token_counter.total_embedding_token_count}")
  print(f"LLM Token: {token_counter.total_llm_token_count}")
  ```
""")


def run():
    """运行实验 8：进阶特性实验。"""
    experiment_node_postprocessor()
    experiment_ingestion_pipeline()
    experiment_recursive_retrieval()
    experiment_callbacks()
    print(f"\n  ✅ 实验 8 完成\n")


if __name__ == "__main__":
    run()
