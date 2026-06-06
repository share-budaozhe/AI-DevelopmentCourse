# 🧪 Milvus 测试说明与用例

## 测试环境

| 组件 | 版本 |
|------|------|
| Python | 3.10+ |
| pymilvus | >= 2.5.0 |
| milvus-lite | >= 2.4.0 |
| Milvus Server | 2.5.0 (Standalone) 或 Lite |

## 测试场景覆盖

### 1. 功能测试

| 用例 | 描述 | 预期结果 |
|------|------|---------|
| TC-01-连接 | 连接 Milvus Lite/Standalone | 连接成功 |
| TC-02-创建集合 | 创建带 Schema 的 Collection | 集合创建，字段正确 |
| TC-03-插入数据 | 单条 + 批量插入 | num_entities 匹配 |
| TC-04-Flush | flush() 持久化 | 数据落盘 |
| TC-05-创建索引 | IVF_FLAT 索引 | 索引状态正常 |
| TC-06-向量搜索 | COSINE/ANN 搜索 | 返回 Top-K 结果 |
| TC-07-标量过滤 | expr 过滤搜索 | 结果满足条件 |
| TC-08-标量查询 | query() 按条件查 | 结果正确 |
| TC-09-删除数据 | delete() 按主键 | 数据被删除 |
| TC-10-删除集合 | drop_collection() | 集合不存在 |
| TC-11-分区操作 | 创建/插入/搜索分区 | 数据隔离正确 |
| TC-12-别名操作 | create_alias/drop_alias | 别名解析正确 |

### 2. 性能测试

| 用例 | 指标 | 阈值（Lite） |
|------|------|-------------|
| TP-01-插入吞吐 | 条/秒 | > 500 条/秒 |
| TP-02-搜索延迟 | P95 延迟 | < 100ms |
| TP-03-索引构建 | 构建时间 | < 30s (10K 数据) |
| TP-04-批量搜索 | QPS | > 10 QPS |

### 3. 边界测试

| 用例 | 描述 | 预期结果 |
|------|------|---------|
| TE-01-空搜索 | 无数据时搜索 | 返回空结果 |
| TE-02-零 limit | limit=0 | 返回空 |
| TE-03-超大 limit | limit=10000 | 正常工作 |
| TE-04-重复主键 | 插入相同 id | 抛出异常 |
| TE-05-不存在分区 | 搜索不存在分区 | 抛出异常 |
| TE-06-超长字符串 | VARCHAR 超 max_length | 抛出异常 |

### 4. 正确性验证

| 用例 | 验证方法 |
|------|---------|
| TV-01-自搜索 | 用已有向量查询，score ≈ 1.0（COSINE） |
| TV-02-同类优先 | 同类商品向量搜索，同类排名靠前 |
| TV-03-过滤正确 | 搜索 + expr 过滤，所有结果满足条件 |
| TV-04-分区隔离 | 不同分区搜索，结果不跨分区 |

---

## 测试执行方式

### 方式 1：交互式运行

```bash
cd milvus-demo
python -m src.main
# 选择实验 1~7 逐个运行
```

### 方式 2：命令行批量运行

```bash
python -m src.demo_connect
python -m src.demo_collections
python -m src.demo_indexes
python -m src.demo_search
python -m src.demo_filter
python -m src.demo_partition
python -m src.demo_advanced
```

### 方式 3：一键全量

```bash
python -m src.main
# 选择 [9] 运行全部实验
```

---

## 测试结果示例

```
🎉 全部实验完成！

实验 1: 连接与基础操作   ... ✅
实验 2: Collection 管理   ... ✅
实验 3: 索引类型对比     ... ✅
实验 4: 向量搜索         ... ✅
实验 5: 标量过滤         ... ✅
实验 6: 分区管理         ... ✅
实验 7: 进阶特性         ... ✅
```
