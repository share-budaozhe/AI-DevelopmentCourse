# 🔍 Milvus 向量搜索深入

## 基础搜索

```python
results = collection.search(
    data=query_vectors,
    anns_field="vector",
    param={"nprobe": 16},
    limit=10,
    output_fields=["title", "price"],
)
```

## 相似度度量

| 度量 | 含义 | 选择 |
|------|------|------|
| COSINE | 余弦相似度 | 文本搜索（推荐） |
| IP | 内积 | 推荐系统 |
| L2 | 欧氏距离 | 图像检索 |

## 搜索参数优化

- **limit**：3-10（精准），50-100（后续重排）
- **nprobe**：nlist 的 1/10~1/4
- **ef**（HNSW）：top_k ~ 32768

## 搜索结果解析

```python
for hits in results:
    for hit in hits:
        print(hit.id)        # 实体 ID
        print(hit.distance)  # 相似度分数
        print(hit.entity.get("title"))  # 标量字段
```
