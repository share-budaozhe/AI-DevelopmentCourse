"""
═══════════════════════════════════════════════════════════════
  🔌 Milvus 学习教程 — src/demo_connect.py
  实验 1：连接与基础操作

  知识点：
  - 连接 Milvus（Lite / Standalone / Zilliz Cloud）
  - 创建/删除 Collection
  - Schema 定义（字段类型、主键、向量维度）
  - 查看 Collection 信息
"""
from pymilvus import (
    connections, utility, Collection, CollectionSchema,
    FieldSchema, DataType,
)
from config import auto_connect, disconnect, print_connection_guide


def experiment_connect():
    """🔬 实验 1.1：连接 Milvus"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 1.1：连接 Milvus")
    print(f"{'='*60}")

    print_connection_guide()

    alias = auto_connect()
    print(f"\n  连接别名: {alias}")

    # 检查连接状态
    print(f"  连接状态: {connections.has_connection(alias)}")

    return alias


def experiment_list_collections():
    """🔬 实验 1.2：列出所有 Collection"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 1.2：列出 Collection")
    print(f"{'='*60}")

    collections = utility.list_collections()
    print(f"\n  当前 Collection 数: {len(collections)}")
    for name in collections:
        print(f"    - {name}")


def experiment_create_collection():
    """🔬 实验 1.3：创建 Collection（定义 Schema）

    知识点：
    - Schema 是 Collection 的骨架，定义字段名、类型、约束
    - 主键字段（is_primary=True）唯一标识每条记录
    - 向量字段（dim=xxx）定义向量维度
    - 索引参数决定检索方式
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 1.3：创建 Collection")
    print(f"{'='*60}")

    collection_name = "demo_hello"

    # 如果已存在则删除
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)
        print(f"\n  🔄 已删除旧 Collection: {collection_name}")

    # 定义 Schema
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
    ]

    schema = CollectionSchema(fields, description="Hello Milvus 演示集合")

    # 创建 Collection
    collection = Collection(name=collection_name, schema=schema)

    print(f"\n  ✅ Collection 创建成功!")
    print(f"  名称: {collection.name}")
    print(f"  描述: {collection.description}")
    print(f"  字段数: {len(collection.schema.fields)}")

    print(f"\n  Schema 结构:")
    for field in collection.schema.fields:
        print(f"    - {field.name}: {field.dtype} "
              f"(主键={field.is_primary}, 维度={field.params.get('dim', 'N/A')})")

    return collection


def run():
    """运行实验 1：连接与基础操作。"""
    alias = experiment_connect()
    experiment_list_collections()
    col = experiment_create_collection()

    # 清理
    if utility.has_collection("demo_hello"):
        utility.drop_collection("demo_hello")

    disconnect()
    print(f"\n  ✅ 实验 1 完成\n")


if __name__ == "__main__":
    run()
