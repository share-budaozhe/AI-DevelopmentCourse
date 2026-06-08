"""
═══════════════════════════════════════════════════════════════
  🔍 LlamaIndex 学习教程 — src/demo_retrievers.py
  实验 3：检索器深入实验
═══════════════════════════════════════════════════════════════

核心知识点：
- Retriever：从索引中查找相关节点的组件
- similarity_top_k：控制返回多少个结果
- 不同检索模式的对比
- 检索器可以独立于查询引擎使用
"""
from llama_index.core import (
    VectorStoreIndex, Settings, MockEmbedding,
)
from sample_data import DEMO_DOCUMENTS


def setup():
    Settings.embed_model = MockEmbedding(embed_dim=384)


def experiment_retriever_basics():
    """🔬 实验 3.1：检索器基础

    知识点：
    - 从索引获取 retriever
    - retriever.retrieve() 返回的是 NodeWithScore 列表
    - NodeWithScore 包含节点文本和相似度分数
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 3.1：检索器基础")
    print(f"{'='*60}")

    setup()
    index = VectorStoreIndex.from_documents(DEMO_DOCUMENTS)
    retriever = index.as_retriever()

    print(f"\n  检索器类型: {type(retriever).__name__}")

    # 模拟检索（Mock embedding 下分数无意义，但结构演示有效）
    query = "什么是 Python？"
    print(f"\n  查询: {query}")
    nodes = retriever.retrieve(query)

    print(f"\n  检索结果 ({len(nodes)} 条):")
    for i, node in enumerate(nodes):
        print(f"\n  📌 结果 {i}:")
        print(f"     分数: {node.score:.4f}")
        print(f"     文本: {node.text[:80]}...")
        print(f"     元数据: {node.metadata}")


def experiment_top_k():
    """🔬 实验 3.2：Top-K 参数的影响

    知识点：
    - similarity_top_k 控制返回的数量
    - 值太小可能遗漏相关信息
    - 值太大可能引入噪声
    - 典型值：3-10
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 3.2：Top-K 参数实验")
    print(f"{'='*60}")

    setup()
    index = VectorStoreIndex.from_documents(DEMO_DOCUMENTS)

    for k in [1, 3, 5]:
        retriever = index.as_retriever(similarity_top_k=k)
        nodes = retriever.retrieve("AI 框架")
        print(f"\n  similarity_top_k = {k} → {len(nodes)} 个结果")
        for node in nodes:
            print(f"    - [{node.score:.4f}] {node.text[:50]}...")


def experiment_retriever_configs():
    """🔬 实验 3.3：检索器高级配置

    知识点：
    - similarity_cutoff：只返回相似度高于阈值的节点
    - 检索器可以配置为返回更多候选，再由后处理过滤
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 3.3：检索器高级配置")
    print(f"{'='*60}")

    print(f"""
  检索器常用配置参数：

  ┌──────────────────────┬──────────────────────────────────────┐
  │ similarity_top_k      │ 返回多少个最相似的节点（默认 2）      │
  │ similarity_cutoff     │ 最低相似度阈值（低于此值的结果丢弃）  │
  │ vector_store_query_mode │ 查询模式（default/sparse/hybrid）  │
  └──────────────────────┴──────────────────────────────────────┘

  检索器模式（VectorIndexRetriever）：
  - default：标准向量检索
  - sparse：稀疏检索（关键词匹配）
  - hybrid：向量 + 关键词混合检索
  - auto_merge：自动合并子节点

  💡 生产环境建议：
  1. Top-K 设为 5-10，给后续处理留有余地
  2. 使用 NodePostprocessor（如 SimilarityPostprocessor）过滤低分节点
  3. 结合 reranker 重新排序检索结果，提升精度
""")


def run():
    """运行实验 3：检索器深入实验。"""
    experiment_retriever_basics()
    experiment_top_k()
    experiment_retriever_configs()
    print(f"\n  ✅ 实验 3 完成\n")


if __name__ == "__main__":
    run()
