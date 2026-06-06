"""
═══════════════════════════════════════════════════════════════
  📚 LlamaIndex 学习教程 — src/sample_data.py
  提供模拟数据和工具函数，用于本地学习和实验
═══════════════════════════════════════════════════════════════

学习要点：
- LlamaIndex 的 Document 对象结构
- 如何创建和使用模拟文档进行本地实验
- 无需 API 密钥即可理解数据流
"""
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# 示例文档（中文 + 英文混合）
# ═══════════════════════════════════════════════════════════════

DEMO_DOCUMENTS = [
    Document(
        text=(
            "Python 是一种解释型、面向对象的高级编程语言。"
            "它由 Guido van Rossum 于 1991 年首次发布。"
            "Python 的设计哲学强调代码的可读性，使用显著的缩进来表示代码块。"
            "Python 广泛用于 Web 开发、数据科学、人工智能和自动化脚本。"
        ),
        metadata={"title": "Python 简介", "category": "编程语言"},
    ),
    Document(
        text=(
            "LlamaIndex 是一个数据框架，用于将 LLM 与外部数据连接起来。"
            "它提供了数据连接器（读取各种格式）、索引结构（组织和检索数据）"
            "以及查询接口（用自然语言查询数据）这三大核心组件。"
            "LlamaIndex 由 Jerry Liu 创建，最初名为 GPT Index。"
        ),
        metadata={"title": "LlamaIndex 简介", "category": "AI 框架"},
    ),
    Document(
        text=(
            "LangChain 是一个用于构建 LLM 驱动应用的框架。"
            "它提供了 Chains（链式调用）、Agents（自主代理）、"
            "Tools（工具集成）、Memory（对话记忆）等核心抽象。"
            "LangChain 支持 Python 和 JavaScript/TypeScript 两种语言。"
            "它由 Harrison Chase 于 2022 年创建。"
        ),
        metadata={"title": "LangChain 简介", "category": "AI 框架"},
    ),
    Document(
        text=(
            "Transformer 架构由 Vaswani 等人在 2017 年的论文 "
            "'Attention Is All You Need' 中提出。它完全基于注意力机制，"
            "摒弃了传统的循环和卷积结构。Transformer 是现代大语言模型"
            "（如 GPT、BERT、LLaMA）的基础架构。"
            "自注意力机制让模型能够并行处理整个序列，大幅提升了训练效率。"
        ),
        metadata={"title": "Transformer 架构", "category": "深度学习"},
    ),
    Document(
        text=(
            "RAG（检索增强生成）是一种结合信息检索和文本生成的架构。"
            "它的工作流程是：先将知识库文档转为向量索引，"
            "用户提问时检索最相关的文档片段，然后将这些片段与问题一起"
            "提供给 LLM 生成准确、有依据的回答。"
            "RAG 能有效减少 LLM 的幻觉问题，提供可溯源的答案。"
        ),
        metadata={"title": "RAG 架构", "category": "AI 技术"},
    ),
    Document(
        text=(
            "向量数据库是一种专门存储和检索向量嵌入的数据库系统。"
            "常见的向量数据库包括 Pinecone、Weaviate、Milvus、Qdrant 和 Chroma。"
            "LlamaIndex 内置了对多种向量数据库的支持。"
            "向量数据库的核心操作是近似最近邻搜索（ANN），"
            "能在海量向量中快速找到最相似的 Top-K 个结果。"
        ),
        metadata={"title": "向量数据库", "category": "基础设施"},
    ),
]


# ═══════════════════════════════════════════════════════════════
# 从文件加载文档
# ═══════════════════════════════════════════════════════════════

def load_sample_docs() -> list[Document]:
    """从 data/sample_docs 目录加载示例文档。

    学习要点：LlamaIndex 的 SimpleDirectoryReader 是最简单的数据加载器。
    """
    from llama_index.core import SimpleDirectoryReader

    data_dir = Path(__file__).parent.parent / "data" / "sample_docs"
    if data_dir.exists():
        reader = SimpleDirectoryReader(input_dir=str(data_dir))
        docs = reader.load_data()
        print(f"[sample_data] 从 {data_dir} 加载了 {len(docs)} 个文档")
        return docs
    return []


def load_all_documents() -> list[Document]:
    """加载所有可用文档（内置 + 文件）。"""
    docs = list(DEMO_DOCUMENTS)
    docs.extend(load_sample_docs())
    print(f"[sample_data] 共 {len(docs)} 个文档可用")
    return docs


def demo_parse_nodes(documents: list[Document] | None = None):
    """演示：文档 → 节点的解析过程。

    学习要点：
    1. SentenceSplitter 是最常用的节点解析器
    2. chunk_size 控制每个节点的大小（字符数）
    3. chunk_overlap 控制相邻节点的重叠量（保留上下文）
    4. 节点是 LlamaIndex 中的最小检索单元
    """
    if documents is None:
        documents = load_all_documents()

    parser = SentenceSplitter(chunk_size=200, chunk_overlap=50)
    nodes = parser.get_nodes_from_documents(documents)

    print(f"\n{'='*60}")
    print(f"  📄 节点解析演示")
    print(f"{'='*60}")
    print(f"  解析器: SentenceSplitter(chunk_size=200, chunk_overlap=50)")
    print(f"  输入文档: {len(documents)} 个")
    print(f"  输出节点: {len(nodes)} 个")
    print(f"  平均节点长度: {sum(len(n.text) for n in nodes) // max(len(nodes), 1)} 字符")

    # 展示前 3 个节点的元数据
    for i, node in enumerate(nodes[:3]):
        print(f"\n  📌 节点 {i}:")
        print(f"     文本: {node.text[:100]}...")
        print(f"     元数据: {node.metadata}")

    return nodes
