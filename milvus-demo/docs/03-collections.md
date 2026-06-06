# 📦 Milvus Collection 管理与数据操作

## Schema 定义

```python
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="price", dtype=DataType.FLOAT),
]
schema = CollectionSchema(fields, description="商品数据库")
collection = Collection(name="products", schema=schema)
```

## 字段类型

| 类型 | 用途 | 示例 |
|------|------|------|
| INT64 | 主键、计数 | id=1 |
| VARCHAR | 标题、名称 | title="Python 编程" |
| FLOAT/DOUBLE | 价格、评分 | price=99.9 |
| BOOL | 标志位 | is_active=True |
| FLOAT_VECTOR | 向量嵌入 | [0.1, 0.2, ...] |
| JSON | 复杂结构 | {"tags": [...]} |

## 数据操作

### 插入
```python
collection.insert([
    [1, 2, 3],              # id
    [[v1], [v2], [v3]],     # vectors
    ["a", "b", "c"],        # title
    [9.9, 19.9, 29.9],      # price
])
collection.flush()  # 持久化
```

### 查询（标量）
```python
results = collection.query(
    expr="price > 100",
    output_fields=["title", "price"],
    limit=10,
)
```

### 删除
```python
collection.delete("id == 1")
collection.delete("price < 10")
```

### 搜索（向量）
```python
results = collection.search(
    data=[query_vector],
    anns_field="vector",
    param={"nprobe": 16},
    limit=10,
)
```

## 最佳实践
- 批量插入（1000-5000 条一批）
- 插入后 `flush()` 确保持久化
- 搜索前 `load()` 加载到内存
- 搜索完成后 `release()` 释放内存
