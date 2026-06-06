# 📄 LlamaIndex 学习 — 文档与节点详解

## Document（文档）

`Document` 是 LlamaIndex 中最基本的数据容器。它表示一段完整的内容，
通常对应一个文件、一条数据库记录或一个 API 响应。

### Document 的结构

```python
from llama_index.core import Document

doc = Document(
    text="这是文档的正文内容...",
    metadata={
        "source": "wiki",
        "author": "张三",
        "date": "2024-01-15",
    },
    doc_id="unique-doc-001",  # 可选，自动生成
)
```

### 元数据（Metadata）的最佳实践

- 始终记录 `source`（来源文件/URL）
- 添加 `date` 用于时效性判断
- 附加 `category` 或 `tags` 用于过滤
- 元数据会在检索结果中返回，用于溯源

### 加载方式

| 方式 | 适用场景 |
|------|---------|
| `Document(text=...)` | 从变量/数据库创建 |
| `SimpleDirectoryReader` | 从本地文件目录加载 |
| 专用 Reader | PDF、网页、数据库、API 等 |
| LlamaHub | 社区贡献的 100+ 数据连接器 |

---

## Node（节点）

Node 是 Document 被切分后的检索最小单元。

### 为什么需要切分（Chunking）？

1. **LLM 上下文限制**：不能把整本书塞进 prompt
2. **检索精度**：小块 → 更精准的语义匹配（大海捞针 vs 游泳池捞针）
3. **成本控制**：更少的 token 输送给 LLM

### 切分策略

#### SentenceSplitter（推荐）
按句子边界切分，保持语义完整：
```python
from llama_index.core.node_parser import SentenceSplitter

parser = SentenceSplitter(
    chunk_size=512,      # 每个节点最多 512 字符
    chunk_overlap=64,    # 相邻节点重叠 64 字符
)
nodes = parser.get_nodes_from_documents(documents)
```

#### TokenTextSplitter
按 token 数切分（适合精确控制 token 用量）：
```python
from llama_index.core.node_parser import TokenTextSplitter

parser = TokenTextSplitter(
    chunk_size=256,      # 每个节点最多 256 tokens
    chunk_overlap=32,
)
```

### 切分参数指南

| 参数 | 建议值 | 说明 |
|------|--------|------|
| chunk_size | 256-1024 | 太小 → 丢失上下文；太大 → 检索不精 |
| chunk_overlap | 10-20% | 保留上下文连续性 |

---

## 代码示例

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

# 加载
documents = SimpleDirectoryReader("./my_docs").load_data()

# 切分
parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)
nodes = parser.get_nodes_from_documents(documents)

# 查看
print(f"文档数: {len(documents)}")
print(f"节点数: {len(nodes)}")
for node in nodes[:3]:
    print(f"[{len(node.text)}字] {node.text[:100]}...")
    print(f"  元数据: {node.metadata}")
```
