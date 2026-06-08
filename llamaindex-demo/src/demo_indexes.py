"""
═══════════════════════════════════════════════════════════════
  📇 LlamaIndex 学习教程 — src/demo_indexes.py
  实验 2：索引类型深入对比
═══════════════════════════════════════════════════════════════

核心知识点：
- VectorStoreIndex：最常用，基于向量相似度的索引
- SummaryIndex：简单摘要索引，用于概括性查询
- KeywordTableIndex：基于关键词的索引
- 每种索引的适用场景和内部原理
"""
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex, SummaryIndex, Document,
    Settings, MockEmbedding,
)
from sample_data import DEMO_DOCUMENTS, load_all_documents


# ═══════════════════════════════════════════════════════════════
# 设置：使用 Mock Embedding（无需 API 密钥即可演示）
# ═══════════════════════════════════════════════════════════════

def setup_mock():
    """配置 Mock 环境，使演示无需真实 API 密钥。

    学习要点：
    1. Settings 是 LlamaIndex 的全局配置入口
    2. MockEmbedding 为每个文本生成固定的假向量（用于演示结构）
    3. 在生产环境中，需要替换为真实的嵌入模型
    """
    Settings.embed_model = MockEmbedding(embed_dim=384)
    # 注意：LLM 调用（如 query）仍需真实 API 密钥
    # 但索引创建和结构演示不需要


# ═══════════════════════════════════════════════════════════════
# 实验函数
# ═══════════════════════════════════════════════════════════════

def experiment_vector_store_index():
    """🔬 实验 2.1：VectorStoreIndex（向量存储索引）

    知识点：
    - 原理：将每个节点转为向量嵌入，存入向量数据库
    - 检索：查询时也转为向量，用余弦相似度找最相关的 Top-K 节点
    - 这是 RAG 系统最核心的索引类型
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 2.1：VectorStoreIndex（向量索引）")
    print(f"{'='*60}")

    setup_mock()
    docs = DEMO_DOCUMENTS[:4]  # 取前 4 个文档演示
    print(f"\n  创建索引，包含 {len(docs)} 个文档...")

    index = VectorStoreIndex.from_documents(docs)
    print(f"  索引创建完成！")

    # 查看索引内部结构
    print(f"\n  索引内部结构：")
    print(f"    类型: {type(index).__name__}")
    print(f"    索引ID: {index.index_id}")
    print(f"    文档数: {len(index.docstore.docs)}")

    # 展示节点
    print(f"\n  索引中的节点：")
    for node_id, node in list(index.docstore.docs.items())[:3]:
        print(f"    [{node_id[:8]}...] {node.text[:60]}...")

    print(f"\n  💡 关键理解：")
    print(f"    VectorStoreIndex 在后台做了这些事：")
    print(f"    1. 把每个节点用嵌入模型转为向量")
    print(f"    2. 将向量存入向量存储（默认是内存中）")
    print(f"    3. 查询时用同样的嵌入模型把问题转为向量")
    print(f"    4. 用余弦相似度找到最相近的 Top-K 节点")

    return index


def experiment_summary_index():
    """🔬 实验 2.2：SummaryIndex（摘要索引）

    知识点：
    - 原理：维护节点的顺序列表，不建向量
    - 检索：按顺序遍历所有节点（适合需要全局信息的查询）
    - 适用场景：文档摘要、全文理解、少量文档的场景
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 2.2：SummaryIndex（摘要/列表索引）")
    print(f"{'='*60}")

    docs = DEMO_DOCUMENTS[:3]
    index = SummaryIndex.from_documents(docs)

    print(f"\n  索引内部结构：")
    print(f"    类型: {type(index).__name__}")
    print(f"    节点数: {len(index.index_struct.nodes)}")

    print(f"\n  💡 关键理解：")
    print(f"    SummaryIndex 与 VectorStoreIndex 的核心区别：")
    print(f"    - VectorStoreIndex: 语义检索（找""相似""的内容）")
    print(f"    - SummaryIndex: 顺序扫描（看""所有""的内容）")
    print(f"    SummaryIndex 不建向量库，所以创建快、内存少，")
    print(f"    但检索时可能需要处理更多节点。")
    print(f"    适合做""总结这篇文章讲了什么""这类需要全局视角的查询。")

    return index


def experiment_index_comparison():
    """🔬 实验 2.3：索引类型对比总结"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 2.3：索引类型对比")
    print(f"{'='*60}")

    comparison = """
    ┌──────────────────────┬────────────────────┬────────────────────┐
    │ 特性                  │ VectorStoreIndex   │ SummaryIndex       │
    ├──────────────────────┼────────────────────┼────────────────────┤
    │ 检索方式              │ 语义向量相似度     │ 顺序遍历节点       │
    │ 需要嵌入模型          │ ✅ 是              │ ❌ 否              │
    │ 查询速度              │ 快（近似搜索）     │ 慢（全量扫描）     │
    │ 内存占用              │ 较高（向量存储）   │ 低（只存文本）     │
    │ 适用场景              │ 精准问答、事实查找 │ 摘要、全局理解     │
    │ 典型用法              │ "Python 是谁创建的"│ "这些文档讲了什么" │
    └──────────────────────┴────────────────────┴────────────────────┘

    还有更多索引类型（进阶）：
    - KeywordTableIndex：基于关键词匹配
    - KnowledgeGraphIndex：基于知识图谱
    - TreeIndex：树形结构索引
    - 复合索引（ComposableGraph）：组合多个索引
    """
    print(comparison)


def run():
    """运行实验 2：索引类型深入对比。"""
    experiment_vector_store_index()
    experiment_summary_index()
    experiment_index_comparison()
    print(f"\n  ✅ 实验 2 完成\n")


if __name__ == "__main__":
    run()
