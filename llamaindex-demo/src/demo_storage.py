"""
═══════════════════════════════════════════════════════════════
  💾 LlamaIndex 学习教程 — src/demo_storage.py
  实验 7：索引持久化与存储
═══════════════════════════════════════════════════════════════

核心知识点：
- storage_context：控制索引的存储方式
- persist()：将索引保存到磁盘
- load_index_from_storage()：从磁盘加载索引
- 存储后端：文件系统、向量数据库、对象存储
"""
import os
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex, Settings, MockEmbedding,
    StorageContext, load_index_from_storage,
)
from sample_data import DEMO_DOCUMENTS


def setup():
    Settings.embed_model = MockEmbedding(embed_dim=384)


def experiment_persist():
    """🔬 实验 7.1：索引持久化

    知识点：
    - persist() 将索引保存到目录
    - 保存的内容包括：文档、向量、索引结构元数据
    - 下次可以直接加载，不需要重新创建索引
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 7.1：索引持久化")
    print(f"{'='*60}")

    setup()

    # 创建索引
    index = VectorStoreIndex.from_documents(DEMO_DOCUMENTS)
    print(f"\n  创建索引: {len(DEMO_DOCUMENTS)} 个文档")

    # 持久化
    persist_dir = Path(__file__).parent.parent / "data" / "index_storage"
    persist_dir.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(persist_dir))

    print(f"  保存到: {persist_dir}")

    # 查看保存的文件
    files = list(persist_dir.glob("*"))
    print(f"\n  持久化的文件:")
    for f in files:
        size_kb = f.stat().st_size / 1024
        print(f"    {f.name} ({size_kb:.1f} KB)")

    print(f"\n  💡 持久化保存了什么？")
    print(f"    - docstore.json：文档存储（原始文本）")
    print(f"    - index_store.json：索引结构元数据")
    print(f"    - vector_store.json：向量嵌入数据")
    print(f"    - graph_store.json：知识图谱数据（如果有）")


def experiment_reload():
    """🔬 实验 7.2：从磁盘重新加载索引

    知识点：
    - load_index_from_storage() 重建索引
    - 需要相同的 StorageContext 配置
    - 加载速度远快于重建（不需要重新嵌入）
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 7.2：重新加载索引")
    print(f"{'='*60}")

    setup()
    persist_dir = Path(__file__).parent.parent / "data" / "index_storage"

    if not persist_dir.exists():
        print(f"\n  ⚠️ 请先运行实验 7.1 创建持久化索引")
        return

    print(f"\n  从 {persist_dir} 加载索引...")

    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
    loaded_index = load_index_from_storage(storage_context)

    print(f"  加载完成！")
    print(f"    文档数: {len(loaded_index.docstore.docs)}")
    print(f"    索引ID: {loaded_index.index_id}")

    print(f"\n  ⚡ 性能对比（概念）：")
    print(f"    首次创建: 需要调用嵌入模型 → 慢 + API 费用")
    print(f"    加载已有索引: 直接读取文件 → 快 + 零费用")
    print(f"    对于大型文档库（如 10000+ 页），这个差异非常显著！")


def experiment_storage_backends():
    """🔬 实验 7.3：存储后端概览

    知识点：
    - 默认使用文件系统
    - 可以切换为向量数据库（生产环境）
    - 不同后端的适用场景
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 7.3：存储后端对比")
    print(f"{'='*60}")

    backends_table = """
  LlamaIndex 支持的存储后端：

  ┌─────────────────┬──────────────────────────┬────────────────────┐
  │ 后端             │ 适用场景                  │ 特点               │
  ├─────────────────┼──────────────────────────┼────────────────────┤
  │ 文件系统 (默认)  │ 开发测试、小规模          │ 无需额外服务       │
  │ 内存             │ 临时实验                  │ 速度最快           │
  │ Chroma           │ 中小规模生产              │ 轻量、开源         │
  │ Qdrant           │ 高性能生产                │ Rust 实现、过滤强  │
  │ Pinecone         │ 大规模生产、托管服务      │ 全托管、弹性扩展   │
  │ Milvus           │ 超大规模、企业级          │ 分布式、十亿级     │
  │ Weaviate         │ 混合搜索、生产              │ 自带向量+关键词    │
  │ PostgreSQL+pgvector│ 已有 PG 基础设施        │ 一站式             │
  └─────────────────┴──────────────────────────┴────────────────────┘

  💡 选择建议：
  - 学习实验 → 文件系统/内存（默认）
  - 小项目上线 → Chroma（免费、简单）
  - 公司项目 → Qdrant 或 PostgreSQL+pgvector（已有基础设施）
  - 大规模 → Pinecone 或 Milvus（专业向量数据库）
"""
    print(backends_table)


def run():
    """运行实验 7：索引持久化与存储。"""
    experiment_persist()
    experiment_reload()
    experiment_storage_backends()
    print(f"\n  ✅ 实验 7 完成\n")


if __name__ == "__main__":
    run()
