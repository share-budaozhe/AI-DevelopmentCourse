"""
═══════════════════════════════════════════════════════════════
  📂 Milvus 学习教程 — src/demo_partition.py
  实验 6：分区管理

  知识点：
  - Partition：Collection 的逻辑子集
  - 为什么要分区：加速查询、数据隔离、生命周期管理
  - 创建/删除/清空分区
  - 分区搜索
"""
import numpy as np
from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType, utility,
)
from config import auto_connect, disconnect
from data_loader import generate_product_vectors


COLLECTION_NAME = "demo_partition_test"


def experiment_partition():
    """🔬 实验 6.1：分区完整流程

    模拟：电商平台按类目分区存储商品向量
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 6.1：分区基础")
    print(f"{'='*60}")

    auto_connect()
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="price", dtype=DataType.FLOAT),
    ]
    schema = CollectionSchema(fields, description="分区测试")
    col = Collection(name=COLLECTION_NAME, schema=schema)

    # 创建分区
    partitions = ["electronics", "books", "clothing"]
    for pname in partitions:
        col.create_partition(pname)
    print(f"\n  ✅ 创建 {len(partitions)} 个分区: {partitions}")

    # 模拟数据并按类别插入不同分区
    data = generate_product_vectors(300, dim=128)
    electronics_data = [d for d in data if "电子" in d["category"]]
    books_data = [d for d in data if "图书" in d["category"]]
    clothing_data = [d for d in data if "服装" in d["category"]]

    def insert_to_partition(col, partition_name, data_list):
        if not data_list:
            return
        ids = [d["id"] for d in data_list]
        vecs = [d["vector"].tolist() for d in data_list]
        cats = [d["category"] for d in data_list]
        prices = [d["price"] for d in data_list]
        partition = col.partition(partition_name)

        # 将数据分批插入
        for i in range(0, len(ids), 100):
            batch_ids = ids[i:i+100]
            partition.insert([
                batch_ids,
                vecs[i:i+100],
                cats[i:i+100],
                prices[i:i+100],
            ])

    insert_to_partition(col, "electronics", electronics_data)
    insert_to_partition(col, "books", books_data)
    insert_to_partition(col, "clothing", clothing_data)
    col.flush()

    # 查看分区统计
    print(f"\n  📊 分区统计:")
    for p in col.partitions:
        print(f"    {p.name}: {p.num_entities} 条")
    print(f"    _default: {col.num_entities} 条（总计）")

    # 创建索引
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 64},
    }
    col.create_index(field_name="vector", index_params=index_params)
    col.load()

    # ── 搜索：只在电子分区中搜 ──
    query_vec = [np.random.randn(128).astype(np.float32).tolist()]
    search_params = {"nprobe": 8}

    results = col.search(
        data=query_vec, anns_field="vector",
        param=search_params, limit=5,
        expr="category like '电子%'",  # 也可以用分区过滤
        output_fields=["category", "price"],
    )
    print(f"\n  🔍 只在电子产品中搜索:")
    for hit in results[0]:
        print(f"    [{hit.id}] {hit.entity['category']} | ￥{hit.entity['price']} | score={hit.distance:.4f}")

    # 释放并清理
    col.release()
    utility.drop_collection(COLLECTION_NAME)


def experiment_partition_best_practices():
    """🔬 实验 6.2：分区最佳实践"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 6.2：分区设计原则")
    print(f"{'='*60}")

    practices = """
  分区使用场景：

  1. 按时间分区
     - 日志/事件数据：按天/月分区
     - 好处：快速删除过期数据（drop_partition）
     - 示例：partition_202601, partition_202602

  2. 按类别分区
     - 电商：按商品类目
     - 文档库：按文档类型（API 文档 / 教程 / FAQ）
     - 好处：缩小搜索范围，提升速度

  3. 按用户/租户分区
     - SaaS 多租户隔离
     - 好处：数据安全隔离

  分区注意事项：
  ⚠️ 分区数量限制：默认 4096 个
  ⚠️ 同一 Collection 的所有分区共享索引
  ⚠️ 跨分区搜索需要指定所有分区名（或用 _default 搜全库）
  ⚠️ 插入时必须指定目标分区（否则进入 _default）

  分区 vs 标量过滤：
  ┌──────────┬──────────────────┬────────────────────┐
  │ 方式      │ 原理              │ 适用               │
  ├──────────┼──────────────────┼────────────────────┤
  │ 分区      │ 物理隔离数据块    │ 大类别、时间分区    │
  │ 过滤 expr │ 搜索后过滤结果    │ 精细条件、动态过滤  │
  └──────────┴──────────────────┴────────────────────┘

  建议：粗粒度用分区，细粒度用过滤。
  例如：类目用分区（电子/图书/服装），价格用过滤。
"""
    print(practices)


def run():
    """运行实验 6：分区管理。"""
    experiment_partition()
    experiment_partition_best_practices()
    disconnect()
    print(f"\n  ✅ 实验 6 完成\n")


if __name__ == "__main__":
    run()
