"""
═══════════════════════════════════════════════════════════════
  🎯 Milvus 学习教程 — src/demo_filter.py
  实验 5：标量过滤与混合搜索

  知识点：
  - 标量过滤（expr）：在向量搜索前/后过滤
  - 过滤表达式语法（==, >, <, in, and, or, not）
  - 元数据过滤实战
  - 过滤对性能的影响
"""
import numpy as np
from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType, utility,
)
from config import auto_connect, disconnect
from data_loader import generate_product_vectors


COLLECTION_NAME = "demo_filter_test"


def _setup() -> Collection:
    auto_connect()
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="price", dtype=DataType.FLOAT),
        FieldSchema(name="rating", dtype=DataType.FLOAT),
    ]
    schema = CollectionSchema(fields, description="过滤测试集合")
    col = Collection(name=COLLECTION_NAME, schema=schema)

    data = generate_product_vectors(1000, dim=128)
    ids = [d["id"] for d in data]
    vectors = [d["vector"].tolist() for d in data]
    names = [d["name"] for d in data]
    cats = [d["category"] for d in data]
    prices = [d["price"] for d in data]
    ratings = [d["rating"] for d in data]

    col.insert([ids, vectors, names, cats, prices, ratings])
    col.flush()

    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    col.create_index(field_name="vector", index_params=index_params)
    col.load()
    return col


def experiment_scalar_filter():
    """🔬 实验 5.1：标量过滤实战

    模拟场景：用户搜"像这个商品一样的"，但只想要某个类目、某个价位的。
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 5.1：标量过滤 — 商品搜索")
    print(f"{'='*60}")

    col = _setup()

    # 用一个电子产品作为查询向量
    result = col.query(expr="category == '电子产品'", output_fields=["vector", "name"], limit=1)
    if not result:
        print("  无数据")
        return
    query_vec = [result[0]["vector"]]
    query_name = result[0]["name"]

    # ── 搜索 1：无过滤 ──
    results = col.search(
        data=query_vec, anns_field="vector",
        param={"nprobe": 16}, limit=5,
        output_fields=["name", "category", "price", "rating"],
    )
    print(f"\n  查询: 与「{query_name}」相似的商品")
    print(f"\n  --- 无过滤 ---")
    for hit in results[0]:
        print(f"    [{hit.id}] {hit.entity['name']:<12} | {hit.entity['category']:<8} | ￥{hit.entity['price']:<8} | score={hit.distance:.4f}")

    # ── 搜索 2：只搜电子产品 ──
    results = col.search(
        data=query_vec, anns_field="vector",
        param={"nprobe": 16}, limit=5,
        expr="category == '电子产品'",
        output_fields=["name", "category", "price", "rating"],
    )
    print(f"\n  --- 过滤: category == '电子产品' ---")
    for hit in results[0]:
        print(f"    [{hit.id}] {hit.entity['name']:<12} | {hit.entity['category']:<8} | ￥{hit.entity['price']:<8} | score={hit.distance:.4f}")

    # ── 搜索 3：电子产品 + 价格范围 ──
    results = col.search(
        data=query_vec, anns_field="vector",
        param={"nprobe": 16}, limit=5,
        expr="category == '电子产品' and price >= 100 and price <= 500",
        output_fields=["name", "category", "price", "rating"],
    )
    print(f"\n  --- 过滤: 电子产品 + ￥100-500 ---")
    for hit in results[0]:
        print(f"    [{hit.id}] {hit.entity['name']:<12} | ￥{hit.entity['price']:<8} | score={hit.distance:.4f}")

    col.release()
    utility.drop_collection(COLLECTION_NAME)


def experiment_expr_syntax():
    """🔬 实验 5.2：过滤表达式语法大全"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 5.2：过滤表达式语法")
    print(f"{'='*60}")

    syntax = """
  Milvus 过滤表达式（expr）语法：

  比较运算符：
    ==   等于          price == 100
    !=   不等于        category != "食品"
    >    大于          rating > 4.0
    >=   大于等于      stock >= 10
    <    小于          price < 500
    <=   小于等于      rating <= 3.5

  逻辑运算符：
    and  与            price > 100 and category == "电子"
    or   或            category == "图书" or category == "服装"
    not  非            not (category == "食品")

  集合运算：
    in   在...之中     category in ["电子", "图书", "服装"]
    not in 不在...之中  category not in ["食品", "家居"]

  字符串匹配（Milvus 2.4+）：
    like 模式匹配      name like "Python%"
                      name like "%入门%"

  数学运算：
    + - * / // %       price * 0.8 > 300

  复合示例：
    # 电子或图书，评分 >= 4，价格 50-500
    (category == "电子产品" or category == "图书")
        and rating >= 4.0
        and price >= 50
        and price <= 500

  ⚠️ 注意：
  - LIKE 操作慢，避免在大数据集上使用
  - in 列表过长也会影响性能
  - 过滤在向量搜索之后执行（Post-filtering）
  - 过滤掉太多结果可能导致返回数量 < limit
"""
    print(syntax)


def run():
    """运行实验 5：标量过滤与混合搜索。"""
    experiment_scalar_filter()
    experiment_expr_syntax()
    disconnect()
    print(f"\n  ✅ 实验 5 完成\n")


if __name__ == "__main__":
    run()
