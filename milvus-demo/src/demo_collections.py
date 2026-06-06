"""
═══════════════════════════════════════════════════════════════
  📦 Milvus 学习教程 — src/demo_collections.py
  实验 2：Collection 管理与数据操作

  知识点：
  - Collection 的完整生命周期
  - 数据插入（单条/批量/分批）
  - 数据查询（get/query）
  - 数据删除（按主键/按条件）
  - Flush 与 Load
"""
import numpy as np
from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType, utility,
)
from config import auto_connect, disconnect
from data_loader import generate_product_vectors


COLLECTION_NAME = "demo_products"


def experiment_collection_lifecycle():
    """🔬 实验 2.1：Collection 生命周期管理

    完整流程：创建 → 插入 → 加载 → 查询 → 删除 → 销毁
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 2.1：Collection 生命周期")
    print(f"{'='*60}")

    auto_connect()

    # ── 1. 创建 ──
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="price", dtype=DataType.FLOAT),
        FieldSchema(name="rating", dtype=DataType.FLOAT),
        FieldSchema(name="stock", dtype=DataType.INT32),
    ]
    schema = CollectionSchema(fields, description="商品向量数据库")
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    print(f"\n  [1] ✅ 创建: {collection.name} ({len(fields)} 个字段)")

    # ── 2. 插入数据 ──
    data = generate_product_vectors(500, dim=128)

    # 单条插入示例
    single = data[0]
    collection.insert([
        [single["id"]],
        [single["vector"].tolist()],
        [single["name"]],
        [single["category"]],
        [single["price"]],
        [single["rating"]],
        [single["stock"]],
    ])
    print(f"  [2] ✅ 单条插入: id={single['id']}")

    # 批量插入剩余数据
    ids = [d["id"] for d in data[1:]]
    vectors = [d["vector"].tolist() for d in data[1:]]
    names = [d["name"] for d in data[1:]]
    cats = [d["category"] for d in data[1:]]
    prices = [d["price"] for d in data[1:]]
    ratings = [d["rating"] for d in data[1:]]
    stocks = [d["stock"] for d in data[1:]]

    collection.insert([ids, vectors, names, cats, prices, ratings, stocks])
    collection.flush()
    print(f"  [2] ✅ 批量插入: {len(ids)} 条")

    # ── 3. 查看统计 ──
    print(f"\n  [3] 📊 统计信息:")
    print(f"      总行数: {collection.num_entities}")

    # ── 4. 按主键查询 ──
    results = collection.query(
        expr=f"id in [1, 2, 3]",
        output_fields=["name", "category", "price", "rating"],
    )
    print(f"\n  [4] 🔍 按主键查询 (id=1,2,3):")
    for r in results:
        print(f"      [{r['id']}] {r['name']} | {r['category']} | ￥{r['price']} | ⭐{r['rating']}")

    # ── 5. 按条件查询 ──
    results = collection.query(
        expr="price > 500 and rating > 4.5",
        output_fields=["name", "category", "price", "rating"],
        limit=5,
    )
    print(f"\n  [5] 🔍 条件查询 (price>500 & rating>4.5): {len(results)} 条")
    for r in results[:5]:
        print(f"      [{r['id']}] {r['name']} | ￥{r['price']} | ⭐{r['rating']}")

    # ── 6. 删除指定数据 ──
    delete_count = collection.delete("id == 1")
    print(f"\n  [6] 🗑️ 删除 id=1: {delete_count} 条")
    print(f"      剩余行数: {collection.num_entities}")

    # ── 7. 释放内存 ──
    collection.release()
    print(f"  [7] 🔓 已释放内存")

    # ── 8. 删除 Collection ──
    utility.drop_collection(COLLECTION_NAME)
    print(f"  [8] 💣 已删除 Collection")


def experiment_batch_operations():
    """🔬 实验 2.2：批量操作最佳实践

    知识点：
    - 批量插入比逐条插入快 10-100 倍
    - 推荐 batch_size: 1000-5000
    - flush() 确保数据持久化
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 2.2：批量操作性能")
    print(f"{'='*60}")

    print(f"""
  批量操作最佳实践：

  1. 批量插入（推荐 batch_size=1000-5000）
     ```python
     for i in range(0, len(data), 2000):
         batch = data[i:i+2000]
         collection.insert([ids, vectors, ...])
     collection.flush()  # 持久化到磁盘
     ```

  2. 批量查询（单条 vs 批量）
     ❌ 不好: for id in ids: collection.query(expr=f"id=={id}")
     ✅ 好:   collection.query(expr=f"id in {ids}")

  3. 批量删除
     ❌ 不好: for id in ids: collection.delete(f"id=={id}")
     ✅ 好:   collection.delete(f"id in {ids}")

  4. 数据持久化
     - insert() → 写入内存
     - flush()  → 持久化到磁盘（确保数据不丢失）

  5. 数据加载
     - 搜索前需要 collection.load()
     - 查询前也需要（Milvus 2.4+ 某些操作自动加载）
     - release() 释放内存
""")


def run():
    """运行实验 2：Collection 管理与数据操作。"""
    experiment_collection_lifecycle()
    experiment_batch_operations()
    disconnect()
    print(f"\n  ✅ 实验 2 完成\n")


if __name__ == "__main__":
    run()
