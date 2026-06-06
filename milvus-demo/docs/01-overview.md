# 🎯 Milvus 向量数据库学习教程 — 项目总览

## 项目目标

这是一个「从零上手」的 Milvus 向量数据库学习项目。通过 7 个精心设计的实验，
你将掌握向量检索的核心概念和生产实践。

## 什么是 Milvus？

Milvus 是一个开源的向量数据库，专为 AI 应用设计。
它解决的核心问题：**在海量向量中快速找到最相似的 K 个**。

## 核心概念速览

### Collection（集合）
类似于关系数据库的"表"。一个 Collection 包含：
- 向量字段（FLOAT_VECTOR）：存储嵌入向量
- 标量字段（INT/VARCHAR/FLOAT）：存储元数据
- 主键字段：唯一标识每条记录

### Index（索引）
加速向量检索的数据结构。
- FLAT：100% 精确，最慢
- IVF_FLAT：95% 精确，10-100x 加速
- HNSW：98% 精确，内存换速度

### Partition（分区）
Collection 的逻辑子集，用于：
- 缩小搜索范围（加速）
- 数据隔离（安全）
- 快速删除（DROP PARTITION）

### Search（搜索）
近似最近邻（ANN）搜索：
1. 查询向量 → 索引 → Top-K 最相似向量 → 返回结果

## 运行模式

| 模式 | 说明 | 安装 |
|------|------|------|
| **Milvus Lite** | 嵌入式，免 Docker | `pip install milvus-lite` |
| **Milvus Standalone** | Docker 单机 | `docker-compose up -d` |
| **Zilliz Cloud** | 全托管 | 注册 cloud.zilliz.com |

本教程默认使用 Milvus Lite（零配置、即刻上手）。

## 学习路线

```
实验 1: 连接与 Schema   ← 起点：配置连接，定义数据结构
    ↓
实验 2: Collection CRUD ← 核心：增删改查，数据管理
    ↓
实验 3: 索引类型        ← 关键：索引选型，参数调优
    ↓
实验 4: 向量搜索        ← 目标：ANN 搜索，相似度度量
    ↓
实验 5: 标量过滤        ← 实战：向量搜索 + 条件过滤
    ↓
实验 6: 分区管理        ← 优化：数据隔离，缩小搜索范围
    ↓
实验 7: 进阶特性        ← 精通：别名、一致性、性能调优
```

## 费用

Milvus Lite 完全免费，运行在本地。Zilliz Cloud 有免费额度（1GB 存储）。
