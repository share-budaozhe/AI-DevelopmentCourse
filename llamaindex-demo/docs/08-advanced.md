# 🚀 LlamaIndex 学习 — 进阶特性与最佳实践

## NodePostprocessor（节点后处理器）

检索之后、生成之前运行的过滤器/排序器。

### 常用后处理器

```python
from llama_index.core.postprocessor import (
    SimilarityPostprocessor,
    KeywordNodePostprocessor,
)

# 过滤低分节点
postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)

# 要求包含特定关键词
keyword_pp = KeywordNodePostprocessor(
    required_keywords=["Python"],
    exclude_keywords=["deprecated"],
)

# 在查询引擎中使用
query_engine = index.as_query_engine(
    node_postprocessors=[postprocessor, keyword_pp],
)
```

---

## IngestionPipeline（数据摄入管线）

一次性完成文档加载 → 解析 → 嵌入的流水线。

```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from config import auto_setup

auto_setup()  # 使用已配置的 LLM + Embedding

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=50),
        Settings.embed_model,  # DeepSeek 模式下用本地嵌入
    ],
)

nodes = pipeline.run(documents=documents)
index = VectorStoreIndex(nodes)
```

**优势**：
- 支持缓存（增量更新时跳过已处理的文档）
- 统一管理所有转换步骤
- 便于跟踪数据流

---

## 存储与持久化

### 保存索引

```python
# 保存
index.storage_context.persist(persist_dir="./my_index")

# 再次加载
from llama_index.core import StorageContext, load_index_from_storage

storage_context = StorageContext.from_defaults(persist_dir="./my_index")
loaded_index = load_index_from_storage(storage_context)
```

### 生产环境向量数据库

```python
# Chroma 示例
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("my_docs")
vector_store = ChromaVectorStore(chroma_collection=collection)

index = VectorStoreIndex.from_documents(
    docs,
    vector_store=vector_store,
)
```

---

## Callbacks 与可观测性

```python
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

token_counter = TokenCountingHandler()
Settings.callback_manager = CallbackManager([token_counter])

# ... 运行查询 ...

print(f"嵌入 Token: {token_counter.total_embedding_token_count}")
print(f"LLM Token:  {token_counter.total_llm_token_count}")
```

---

## 嵌入模型选择

### 本教程支持的方案

| 方案 | 模型 | 费用 | 中文效果 |
|------|------|------|---------|
| **本地 HuggingFace** | BAAI/bge-small-zh-v1.5 | 免费 | ⭐⭐⭐⭐ |
| 本地 HuggingFace | all-MiniLM-L6-v2 | 免费 | ⭐⭐（英文优化） |
| OpenAI | text-embedding-3-small | 约 $0.02/百万 token | ⭐⭐⭐ |
| OpenAI | text-embedding-3-large | 约 $0.13/百万 token | ⭐⭐⭐⭐⭐ |

推荐组合：**DeepSeek（LLM）+ BGE（嵌入）** — 最优性价比。

### 切换嵌入模型

```python
# .env 中设置
USE_LOCAL_EMBEDDING=true  # 启用本地嵌入

# 或者代码中切换
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-zh-v1.5",
)
```

---

## 生产环境最佳实践

### 1. 嵌入模型选择
- 中文场景：BAAI/bge-small-zh-v1.5（开源第一梯队，免费）
- 通用场景：OpenAI text-embedding-3-small（性价比最高）
- 多语言：Cohere Embed Multilingual

### 2. LLM 选择
- 性价比推荐：DeepSeek（≈￥1/百万 token）
- 精度优先：GPT-4 / Claude 3.5 Sonnet
- 速度优先：GPT-4o-mini
- 本地部署：Llama 3 / Qwen（通过 Ollama）

### 3. 向量数据库选择
- < 10K 文档 → Chroma / 内存
- < 1M 文档 → Qdrant
- > 1M 文档 → Milvus / Pinecone

### 4. 监控指标
- 检索召回率（有多少相关文档被找出来了）
- 答案忠实度（有没有胡��乱造）
- 响应延迟（P50/P95/P99）
- Token 消耗（成本控制，DeepSeek 成本低也别忽视）

### 5. 安全注意事项
- API 密钥通过 `.env` 管理，不要提交到 Git
- 不要把所有文档都索引（注意数据权限）
- 用户输入要过滤（防止 prompt injection）
- 文档中的敏感信息要脱敏
