# 📐 Milvus 索引类型与原理

## 什么是索引？

索引是一种加速查找的数据结构。Milvus 的索引帮助在百万/亿级向量中
快速找到 Top-K 最相似的结果，而不需要遍历全部。

## 索引对比

| 索引 | 精度 | 速度 | 内存 | 适用 |
|------|------|------|------|------|
| FLAT | 100% | 最慢 | 低 | < 10K |
| IVF_FLAT | ≈95% | 快 | 中 | 10K-10M |
| IVF_SQ8 | ≈90% | 快 | 低 | 内存受限 |
| HNSW | ≈98% | 快 | 高 | 高性能 |
| IVF_PQ | ≈80% | 快 | 极低 | 亿级 |
| SCANN | 可调 | 快 | 低 | 生产大规模 |

## IVF_FLAT 原理

```
1. 聚类：将 N 个向量用 K-means 分为 nlist 个簇
2. 搜索：查询向量只与最近的 nprobe 个簇比较
3. 效果：搜索 128/4096 ≈ 3% 的向量

参数：
- nlist：簇数（越大 → 搜索越少 → 越快，但精度越低）
- nprobe：搜索策略（越大 → 精度越高 → 越慢）
```

## 索引创建

```python
index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128},
}
collection.create_index(field_name="vector", index_params=index_params)
collection.load()
```

## 选择指南

1. 数据 < 10K → FLAT（精度优先）
2. 数据 10K-10M → IVF_FLAT（平衡之选）
3. 高性能需求 → HNSW（内存换速度）
4. 亿级数据 → IVF_PQ 或 SCANN
