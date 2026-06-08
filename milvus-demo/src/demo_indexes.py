"""
═══════════════════════════════════════════════════════════════
  📐 Milvus 学习教程 — src/demo_indexes.py
  实验 3：索引类型深入对比

  知识点：
  - 索引是什么：加速向量检索的数据结构
  - 常用索引类型：FLAT / IVF_FLAT / IVF_SQ8 / HNSW / SCANN
  - 索引参数调优（nlist, M, efConstruction）
  - 不同索引的适用场景和取舍
"""
import time
import numpy as np
from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType, utility, IndexType,
)
from config import auto_connect, disconnect
from data_loader import generate_product_vectors


COLLECTION_NAME = "demo_index_test"


def _setup_collection() -> Collection:
    """创建测试 Collection。"""
    auto_connect()
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields, description="索引测试集合")
    collection = Collection(name=COLLECTION_NAME, schema=schema)

    # 插入 2000 条测试数据
    data = generate_product_vectors(2000, dim=128)
    ids = [d["id"] for d in data]
    vectors = [d["vector"].tolist() for d in data]

    collection.insert([ids, vectors])
    collection.flush()
    return collection


def experiment_index_types():
    """🔬 实验 3.1：索引类型对比

    每种索引都是「速度 vs 精度」的权衡。
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 3.1：索引类型全面对比")
    print(f"{'='*60}")

    indexes = """
  Milvus 支持的索引类型：

  ┌──────────────┬──────────────────────────────────────────────┐
  │ FLAT         │ 暴力搜索，精度 = 100%，最慢                    │
  │              │ 适用：数据 < 10K，要求绝对精确                   │
  ├──────────────┼──────────────────────────────────────────────┤
  │ IVF_FLAT     │ 倒排索引 + 暴力，精度 ≈ 95%，速度快            │
  │              │ 原理：先聚类(nlist 个簇)，只搜最近的 nprobe 个簇 │
  │              │ 参数：nlist=簇数, nprobe=搜索簇数               │
  │              │ 适用：最通用的索引，数据量 10K-10M              │
  ├──────────────┼──────────────────────────────────────────────┤
  │ IVF_SQ8      │ IVF_FLAT + 8位量化，精度 ≈ 90%，内存减半       │
  │              │ 适用：内存受限场景                              │
  ├──────────────┼──────────────────────────────────────────────┤
  │ IVF_PQ       │ IVF + 乘积量化，精度 ≈ 80%，内存极省            │
  │              │ 适用：十亿级数据                                │
  ├──────────────┼──────────────────────────────────────────────┤
  │ HNSW         │ 基于图的分层导航，精度 ≈ 98%，内存大            │
  │              │ 原理：构建多层图，每层存储近邻关系               │
  │              │ 参数：M=邻居数, efConstruction=构建搜索宽度     │
  │              │ 适用：高性能、高精度场景                        │
  ├──────────────┼──────────────────────────────────────────────┤
  │ SCANN        │ Google 的向量压缩索引，精度可调，内存优化       │
  │              │ 适用：大规模生产环境                           │
  └──────────────┴──────────────────────────────────────────────┘

  选择速查：
  < 10K 数据   → FLAT（精度优先，反正数据少）
  10K - 1M     → IVF_FLAT（平衡之选）
  1M - 100M    → HNSW 或 IVF_SQ8（看内存 vs 精度）
  > 100M       → IVF_PQ 或 SCANN（必须省内存）

  💡 经验法则：nlist = 4 × sqrt(数据量)
    例如 100K 数据 → nlist ≈ 4 × 316 ≈ 1264
"""
    print(indexes)


def experiment_create_index():
    """🔬 实验 3.2：创建索引并测试"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 3.2：索引创建与搜索对比")
    print(f"{'='*60}")

    collection = _setup_collection()
    print(f"\n  测试数据: {collection.num_entities} 条")

    # 生成查询向量
    query_vec = np.random.randn(1, 128).astype(np.float32).tolist()

    # ── FLAT（不建索引，暴力搜索）──
    index_params_flat = {
        "metric_type": "COSINE",
        "index_type": "FLAT",
    }
    collection.create_index(field_name="vector", index_params=index_params_flat)
    collection.load()

    t0 = time.time()
    results = collection.search(
        data=query_vec,
        anns_field="vector",
        param={},
        limit=10,
    )
    t_flat = time.time() - t0
    print(f"\n  FLAT:    {(t_flat*1000):.1f}ms | 结果数: {len(results[0])}")
    collection.release()

    # ── IVF_FLAT ──
    index_params_ivf = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.drop_index()
    collection.create_index(field_name="vector", index_params=index_params_ivf)
    collection.load()

    search_params_ivf = {"nprobe": 16}
    t0 = time.time()
    results = collection.search(
        data=query_vec,
        anns_field="vector",
        param=search_params_ivf,
        limit=10,
    )
    t_ivf = time.time() - t0
    print(f"  IVF_FLAT: {(t_ivf*1000):.1f}ms | 结果数: {len(results[0])} | nprobe=16")

    # ── 对比 ──
    speedup = t_flat / max(t_ivf, 0.001)
    print(f"\n  ⚡ IVF_FLAT 比 FLAT 快约 {speedup:.1f}x")

    collection.release()
    utility.drop_collection(COLLECTION_NAME)


def experiment_index_params():
    """🔬 实验 3.3：索引参数调优指南"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 3.3：索引参数调优")
    print(f"{'='*60}")

    tuning = """
  IVF_FLAT 调参：

  nlist（聚类数）
  - 越大 → 建索引越慢，搜索越快，精度越低
  - 推荐值: 4 × sqrt(N)
  - 10K 数据: nlist=1024
  - 1M 数据:  nlist=4096
  - 10M 数据: nlist=16384

  nprobe（搜索时探测的簇数）
  - 越大 → 精度越高，搜索越慢
  - 通常设为 nlist 的 1/10 ~ 1/4
  - 平衡点: nprobe=16~64

  ═══════════════════════════════════════════════

  HNSW 调参：

  M（每个节点的最大邻居数）
  - 越大 → 精度高，内存大，建索引慢
  - 推荐: 4~64，通常 16
  - 高精度: M=32~64

  efConstruction（构建时搜索宽度）
  - 越大 → 索引质量越好，构建越慢
  - 推荐: 8~512，通常 200

  ef（搜索时搜索宽度，运行时参数）
  - 越大 → 精度高，搜索慢
  - 通常: top_k ~ 32768
  - 推荐: ef=64~512

  ═══════════════════════════════════════════════

  💡 调参口诀：
  - 先定索引类型（数据量决定）
  - 搜索太快但精度低 → 增大 nprobe/ef
  - 搜索太慢但精度够 → 减小 nprobe/ef
  - 建索引太久 → 减小 nlist/M
  - 内存不够 → 换 IVF_SQ8 或 IVF_PQ
"""
    print(tuning)


def run():
    """运行实验 3：索引类型深入对比。"""
    experiment_index_types()
    experiment_create_index()
    experiment_index_params()
    disconnect()
    print(f"\n  ✅ 实验 3 完成\n")


if __name__ == "__main__":
    run()
