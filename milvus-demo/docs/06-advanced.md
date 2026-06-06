# 🚀 Milvus 进阶特性与性能调优

## 别名（Alias）

零停机切换——线上服务始终查询别名：

```python
utility.create_alias("products_v2", "products_current")
utility.drop_alias("products_current")
utility.create_alias("products_v3", "products_current")
```

## 一致性级别

| 级别 | 延迟 | 适用 |
|------|------|------|
| STRONG | 最高 | 金融/订单 |
| BOUNDED | 中 | 在线服务（默认） |
| EVENTUALLY | 最低 | 批量分析 |

## 性能优化清单

1. 数据 > 10K 必须建索引
2. nlist = 4 × sqrt(N)
3. nprobe = 16-64
4. 批量插入（1000-5000 条/批）
5. 使用分区缩小搜索范围
6. SSD 存储（向量数据随机读）

## 监控指标

- 查询延迟（P50/P95/P99）
- 插入吞吐量（条/秒）
- 索引大小 vs 可用内存
