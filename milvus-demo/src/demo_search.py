"""
═══════════════════════════════════════════════════════════════
  🔍 Milvus 学习教程 — src/demo_search.py
  实验 4：向量搜索深入实验

  知识点：
  - 基础向量搜索（top-k ANN）
  - 相似度度量（COSINE / IP / L2）
  - 搜索参数调优
  - 搜索结果解析
  - 多向量批量搜索
"""
import numpy as np
from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType, utility,
)
from config import auto_connect, disconnect
from data_loader import generate_product_vectors


COLLECTION_NAME = "demo_search_test"


def _setup() -> Collection:
    """准备测试数据。"""
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
    schema = CollectionSchema(fields, description="搜索测试集合")
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

    # 创建索引
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    col.create_index(field_name="vector", index_params=index_params)
    col.load()
    return col


def experiment_basic_search():
    """🔬 实验 4.1：基础向量搜索"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 4.1：基础向量搜索")
    print(f"{'='*60}")

    col = _setup()

    # 用数据集中第一条的向量作为查询（自己搜自己，分数应该接近 1.0）
    # 先取一条数据的向量
    result = col.query(expr="id == 1", output_fields=["vector"])
    query_vec = [result[0]["vector"]]

    search_params = {"nprobe": 16}
    results = col.search(
        data=query_vec,
        anns_field="vector",
        param=search_params,
        limit=5,
        output_fields=["name", "category", "price", "rating"],
    )

    print(f"\n  查询: 商品 id=1 的向量")
    print(f"\n  Top-5 相似商品:")
    for i, hits in enumerate(results):
        for j, hit in enumerate(hits):
            print(f"    [{j+1}] id={hit.id}, score={hit.distance:.4f}, "
                  f"{hit.entity.get('name')} | "
                  f"￥{hit.entity.get('price')} | ⭐{hit.entity.get('rating')}")

    col.release()
    utility.drop_collection(COLLECTION_NAME)


def experiment_similarity_metrics():
    """🔬 实验 4.2：相似度度量对比

    知识点：
    - COSINE：余弦相似度 [-1, 1]，最常用，关注方向
    - IP (Inner Product)：内积，关注方向和大小
    - L2 (Euclidean)：欧氏距离 [0, ∞)，关注绝对距离
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 4.2：相似度度量对比")
    print(f"{'='*60}")

    metrics = """
  三种相似度度量：

  ┌──────────┬──────────────────┬────────────────┬───────────────┐
  │ 度量      │ 范围              │ 含义            │ 适用场景       │
  ├──────────┼──────────────────┼────────────────┼───────────────┤
  │ COSINE   │ [-1, 1]          │ 越大越相似      │ 文本/语义搜索  │
  │ IP       │ (-∞, ∞)          │ 越大越相似      │ 需归一化向量   │
  │ L2       │ [0, ∞)           │ 越小越相似      │ 图像/精确匹配  │
  └──────────┴──────────────────┴────────────────┴───────────────┘

  ⚠️ 重要：
  - COSINE 要求向量已归一化（单位向量）
  - IP 在向量归一化后 ≈ COSINE（区别：IP 考虑大小）
  - L2 返回距离（越小越好），搜索时返回的是距离值
  - 本教程数据已归一化，适合 COSINE

  选择建议：
  - 90% 场景用 COSINE
  - 图像检索用 L2
  - 推荐系统用 IP（用户-物品交互矩阵）
"""
    print(metrics)


def experiment_search_params():
    """🔬 实验 4.3：搜索参数详解"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 4.3：搜索参数")
    print(f"{'='*60}")

    params_doc = """
  search() 参数详解：

  ```python
  results = collection.search(
      data=query_vectors,     # 查询向量列表 [[v1], [v2], ...]
      anns_field="vector",    # 向量字段名
      param={"nprobe": 16},   # 搜索参数（索引相关）
      limit=10,               # Top-K：返回几个最相似结果
      expr="price > 100",     # 标量过滤（可选）
      output_fields=[...],    # 返回哪些标量字段
      timeout=10,             # 超时（秒）
  )
  ```

  返回结构：
  ```python
  for hits in results:              # 每个查询向量一组结果
      for hit in hits:              # 该查询的 Top-K 结果
          print(hit.id)             # 实体 ID
          print(hit.distance)       # 相似度分数
          print(hit.entity.get("name"))  # 标量字段
  ```

  limit 建议：
  - 精确搜索：limit=5~10
  - 召回场景（后续重排）：limit=50~100
  - 注意：limit 越大，速度越慢
"""
    print(params_doc)


def run():
    """运行实验 4：向量搜索深入实验。"""
    experiment_basic_search()
    experiment_similarity_metrics()
    experiment_search_params()
    disconnect()
    print(f"\n  ✅ 实验 4 完成\n")


if __name__ == "__main__":
    run()
