# 🎯 Milvus 向量数据库学习教程

> 从零掌握 Milvus — 开源向量数据库核心用法
> 支持 **Milvus Lite**（免 Docker）| Standalone | Zilliz Cloud

## 项目简介

7 个核心实验 + 完整文档 + 测试指南。

## 快速开始

```bash
cd milvus-demo
pip install -r requirements.txt  # 内含 milvus-lite
python -m src.main                # 交互式菜单
```

无需 Docker！Milvus Lite 纯 Python 实现，数据存本地 `.db` 文件。

## 项目结构

```
milvus-demo/
├── README.md
├── requirements.txt
├── docker-compose.yml        # Milvus Standalone（可选）
├── .env.example
├── docs/
│   ├── 01-overview.md         # 项目总览
│   ├── 02-installation.md     # 安装指南
│   ├── 03-collections.md      # Collection 与 CRUD
│   ├── 04-indexes.md          # 索引类型
│   ├── 05-search.md           # 向量搜索
│   ├── 06-advanced.md         # 进阶特性
│   ├── 07-faq.md              # FAQ
│   └── test-guide.md          # 测试说明
└── src/
    ├── main.py                # 交互式入口
    ├── config.py              # 连接配置
    ├── data_loader.py         # 示例数据生成
    ├── demo_connect.py        # 实验 1
    ├── demo_collections.py     # 实验 2
    ├── demo_indexes.py        # 实验 3
    ├── demo_search.py         # 实验 4
    ├── demo_filter.py         # 实验 5
    ├── demo_partition.py      # 实验 6
    └── demo_advanced.py       # 实验 7
```

## 实验列表

| 实验 | 内容 | 核心知识点 |
|------|------|-----------|
| 1 | 连接与基础 | Connection, Schema, Collection |
| 2 | CRUD 操作 | Insert, Query, Delete |
| 3 | 索引对比 | FLAT/IVF_FLAT/HNSW, 参数调优 |
| 4 | 向量搜索 | ANN Search, COSINE/IP/L2 |
| 5 | 标量过滤 | expr 表达式, 向量+条件搜索 |
| 6 | 分区管理 | Partition, 数据隔离 |
| 7 | 进阶特性 | Alias, 一致性, 性能调优 |

## 连接方式

| 方式 | 命令 | 适用 |
|------|------|------|
| **Lite（默认）** | 无需配置 | 学习/开发 |
| Standalone | `docker-compose up -d` | 项目开发 |
| Zilliz Cloud | 注册 cloud.zilliz.com | 生产 |

## License

MIT
