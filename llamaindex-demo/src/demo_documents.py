"""
═══════════════════════════════════════════════════════════════
  📄 LlamaIndex 学习教程 — src/demo_documents.py
  实验 1：文档加载与节点解析
═══════════════════════════════════════════════════════════════

核心知识点：
- Document：LlamaIndex 的数据容器
- SimpleDirectoryReader：加载本地文件
- SentenceSplitter：将文档切分为节点（Node）
- chunk_size 和 chunk_overlap 的影响
"""
from pathlib import Path
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter
from sample_data import DEMO_DOCUMENTS


def experiment_load_documents():
    """🔬 实验 1.1：加载文档

    知识点：
    - Document 对象的 text 和 metadata 属性
    - 如何从文件目录批量加载
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 1.1：加载文档")
    print(f"{'='*60}")

    # 方式 1：直接创建 Document 对象
    print("\n  方式 1：直接创建 Document 对象")
    doc = Document(
        text="这是一段示例文本，用于演示 LlamaIndex 的 Document 对象。",
        metadata={"source": "demo", "author": "学习者"},
    )
    print(f"    文本: {doc.text[:50]}...")
    print(f"    元数据: {doc.metadata}")
    print(f"    文档ID: {doc.doc_id}")

    # 方式 2：从目录加载
    print("\n  方式 2：使用 SimpleDirectoryReader 从目录加载")
    data_dir = Path(__file__).parent.parent / "data" / "sample_docs"
    if data_dir.exists():
        docs = SimpleDirectoryReader(input_dir=str(data_dir)).load_data()
        print(f"    加载了 {len(docs)} 个文档")
        for d in docs:
            print(f"    - [{d.metadata.get('file_name', '?')}] {d.text[:50]}...")
    else:
        print(f"    ⚠️ 目录不存在: {data_dir}")

    # 方式 3：使用内置示例文档
    print(f"\n  方式 3：使用内置示例文档")
    print(f"    共 {len(DEMO_DOCUMENTS)} 个内置文档")


def experiment_node_parsing():
    """🔬 实验 1.2：节点解析（文本切割）

    知识点：
    - 为什么需要切分：LLM 有上下文窗口限制
    - chunk_size：每个节点的最大字符数
    - chunk_overlap：相邻节点的重叠字符数（保持语义连贯）
    - 不同切分策略的对比
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 1.2：节点解析 - 文本切割策略")
    print(f"{'='*60}")

    # 使用较长的文档来演示
    long_text = (
        "第一节：Python 基础。Python 是一种解释型语言，语法简洁。"
        "它支持多种编程范式，包括面向对象、函数式和过程式编程。"
        "Python 的一大特点是强制缩进，这让代码天然具有良好的可读性。"
        "第二节：Python 进阶。Python 拥有丰富的标准库和第三方库。"
        "在数据科学领域，NumPy、Pandas、Matplotlib 是最常用的三个库。"
        "在 Web 开发领域，Django 和 Flask 是两个主流框架。"
        "第三节：Python 生态。Python 的包管理器 pip 让安装第三方库变得简单。"
        "虚拟环境（venv/conda）帮助管理不同项目的依赖隔离。"
        "Jupyter Notebook 是数据科学家最爱的交互式编程环境。"
    )

    doc = Document(text=long_text)

    # 测试不同的 chunk_size
    configs = [
        ("小 chunks (100字)", 100, 20),
        ("中 chunks (200字)", 200, 50),
        ("大 chunks (500字)", 500, 100),
    ]

    for label, size, overlap in configs:
        parser = SentenceSplitter(chunk_size=size, chunk_overlap=overlap)
        nodes = parser.get_nodes_from_documents([doc])
        print(f"\n  📐 {label}:")
        print(f"     chunk_size={size}, overlap={overlap} → {len(nodes)} 个节点")
        for i, node in enumerate(nodes):
            print(f"     节点{i}: [{len(node.text)}字] {node.text[:60]}...")

    # 对比：TokenTextSplitter
    print(f"\n  📐 TokenTextSplitter (按 token 切分):")
    token_parser = TokenTextSplitter(chunk_size=50, chunk_overlap=10)
    token_nodes = token_parser.get_nodes_from_documents([doc])
    print(f"     {len(token_nodes)} 个节点")
    for node in token_nodes[:3]:
        print(f"     [{len(node.text)}字] {node.text[:60]}...")


def experiment_metadata():
    """🔬 实验 1.3：文档元数据

    知识点：
    - 元数据用于过滤和检索
    - 可以通过 metadata 进行精确匹配或范围过滤
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 1.3：文档元数据")
    print(f"{'='*60}")

    print("\n  元数据的作用：")
    print("    1. 分类：标记文档类型、来源、日期")
    print("    2. 过滤：检索时只搜索特定类别的文档")
    print("    3. 溯源：回答时显示信息来源")

    print("\n  示例 - 按类别分类的文档组：")
    categories = {}
    for doc in DEMO_DOCUMENTS:
        cat = doc.metadata.get("category", "未分类")
        categories.setdefault(cat, []).append(doc.metadata.get("title", "?"))
    for cat, titles in categories.items():
        print(f"    [{cat}] {', '.join(titles)}")


def run():
    """运行实验 1：文档加载与节点解析。"""
    experiment_load_documents()
    experiment_node_parsing()
    experiment_metadata()
    print(f"\n  ✅ 实验 1 完成\n")


if __name__ == "__main__":
    run()
