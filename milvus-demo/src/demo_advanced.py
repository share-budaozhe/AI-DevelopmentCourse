"""
═══════════════════════════════════════════════════════════════
  🚀 Milvus 学习教程 — src/demo_advanced.py
  实验 7：进阶特性 — 别名、一致性、动态 Schema、性能调优

  知识点：
  - Alias（Collection 别名）
  - 一致性级别
  - 动态 Schema
  - 性能监控与调优
  - 生产环境最佳实践
"""
from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType, utility,
)
from config import auto_connect, disconnect


def experiment_aliases():
    """🔬 实验 7.1：Collection 别名

    场景：线上服务用别名指向 Collection，
    索引重建时不中断服务。
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 7.1：Collection 别名")
    print(f"{'='*60}")

    auto_connect()
    col_name = "demo_products_v1"

    if utility.has_collection(col_name):
        utility.drop_collection(col_name)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields, description="v1")
    col = Collection(name=col_name, schema=schema)

    # 创建别名
    utility.create_alias(collection_name=col_name, alias="products_current")
    print(f"\n  ✅ 别名 'products_current' → '{col_name}'")

    # 查看别名
    alias_info = utility.list_aliases(collection_name=col_name)
    print(f"  别名列表: {alias_info}")

    # ⚡ 零停机切换：
    # 1. 创建 products_v2（新索引）
    # 2. 删除旧别名：utility.drop_alias("products_current")
    # 3. 指向新集合：utility.create_alias("products_v2", "products_current")
    # 4. 删除旧集合：utility.drop_collection("products_v1")
    #
    # 应用始终查询 "products_current"，不知道底层切换了！

    utility.drop_collection(col_name)


def experiment_consistency():
    """🔬 实验 7.2：一致性级别

    知识点：
    - Strong：读到最新数据（最慢）
    - Session：同一会话内看到自己的写入
    - Bounded：有界延迟（容忍一定延迟）
    - Eventually：最终一致（最快，可能读到旧数据）
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 7.2：一致性级别")
    print(f"{'='*60}")

    consistency = """
  Milvus 一致性级别（Consistency Level）：

  ┌────────────┬──────────────────────────────────────────┐
  │ STRONG     │ 保证读到最新写入的数据                      │
  │            │ 适用：金融、订单等强一致场景                 │
  │            │ 延迟：最高                                  │
  ├────────────┼──────────────────────────────────────────┤
  │ SESSION    │ 同一客户端看到自己的写入                     │
  │            │ 适用：用户自己的操作需要立即可见              │
  │            │ 延迟：中等                                  │
  ├────────────┼──────────────────────────────────────────┤
  │ BOUNDED    │ 有界延迟（默认容忍 10 秒）                   │
  │            │ 适用：大多数在线服务                        │
  │            │ 延迟：较低                                  │
  ├────────────┼──────────────────────────────────────────┤
  │ EVENTUALLY │ 最终一致（可能读到旧数据）                   │
  │            │ 适用：批量分析、对实时性不敏感的场景          │
  │            │ 延迟：最低                                  │
  └────────────┴──────────────────────────────────────────┘

  使用方式：
  ```python
  from pymilvus import ConsistencyLevel

  # 创建 Collection 时设置
  schema = CollectionSchema(fields, consistency_level=ConsistencyLevel.BOUNDED)

  # 搜索时覆盖
  results = collection.search(
      ..., consistency_level=ConsistencyLevel.STRONG
  )
  ```
"""
    print(consistency)


def experiment_performance_tuning():
    """🔬 实验 7.3：性能优化清单"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 7.3：性能优化清单")
    print(f"{'='*60}")

    tuning = """
  性能优化检查清单：

  ✅ 索引层面
    1. 数据量 > 10K 必须建索引（FLAT 太慢）
    2. 选择正确的索引类型（IVF_FLAT 是万能起步）
    3. nlist = 4 × sqrt(N)（经验公式）
    4. nprobe 不要太保守（16-64 是不错的范围）
    5. 定期重建索引（数据大量变化后）

  ✅ 搜索层面
    6. limit 不要太大（推荐 10-100）
    7. 减少 output_fields（只返回需要的字段）
    8. 使用分区缩小搜索范围
    9. 使用合适的 metric_type（文本用 COSINE，不需要 L2）

  ✅ 连接层面
    10. 使用连接池（复用连接）
    11. 批量搜索（一次传多个查询向量）

  ✅ 硬件层面
    12. 内存 >= 索引大小 × 1.5（确保索引在内存中）
    13. SSD > HDD（向量数据随机读取）
    14. Milvus Standalone 适合 10M 以下数据
    15. 10M+ 考虑 Milvus 分布式集群

  ✅ 监控指标
    - 查询延迟 P50/P95/P99
    - 索引大小 vs 内存使用
    - 插入吞吐量（条/秒）
    - 搜索 QPS
"""
    print(tuning)


def run():
    """运行实验 7：进阶特性。"""
    experiment_aliases()
    experiment_consistency()
    experiment_performance_tuning()
    disconnect()
    print(f"\n  ✅ 实验 7 完成\n")


if __name__ == "__main__":
    run()
