# ❓ Milvus 常见问题

## Q: Milvus Lite 和 Milvus Standalone 区别？
Lite 是嵌入式版本，数据存为本地文件，无需 Docker。
Standalone 需要 Docker，支持并发和更大数据量。

## Q: 索引应该什么时候建？
数据插入完成后建。推荐先插入数据，再建索引（更快）。

## Q: 索引建好后还能插入数据吗？
可以。但大量新数据插入后索引可能变 "stale"，
建议定期 `collection.drop_index()` + 重建。

## Q: nlist 和 nprobe 怎么选？
- nlist = 4 × sqrt(N)
- nprobe = nlist 的 1/10 到 1/4
- 搜索太慢 → 增大 nlist 或减小 nprobe
- 精度不够 → 减小 nlist 或增大 nprobe

## Q: COSINE 和 IP 有什么区别？
向量归一化后，COSINE ≈ IP。
COSINE 只关心方向（角度），IP 还关心模长（大小）。
90% 的场景用 COSINE。

## Q: 数据量多大该换分布式？
Standalone 通常能处理千万级。亿级以上建议分布式集群。

## Q: 怎么监控 Milvus？
- Milvus 自带 Prometheus metrics
- 关注指标：QPS、延迟、索引大小、内存使用
