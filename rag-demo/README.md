# RAG (检索增强生成) Demo

一个模块化的 RAG 实现，包含文档加载、分块、嵌入向量化、向量存储、检索和答案生成六个核心环节。

## 架构

```
用户查询 → 嵌入向量化 → 向量检索(ChromaDB) → 上下文拼接 → LLM生成答案
                ↑
文档 → 分块 → 嵌入向量化 → 存入向量数据库
```

## 模块说明

| 模块 | 文件 | 职责 |
|------|------|------|
| 文档加载 | src/loader.py | 读取文件、文本清洗、智能分块 |
| 嵌入生成 | src/embedder.py | 调用 sentence-transformers 生成向量 |
| 向量存储 | src/store.py | ChromaDB 的增删查管理 |
| 检索 | src/retriever.py | 相似度检索、重排序 |
| 生成 | src/generator.py | 基于检索上下文生成答案 |

## 快速开始

```bash
pip install -r requirements.txt
python main.py build          # 构建知识库
python main.py search "什么是机器学习"   # 检索
python main.py ask "什么是机器学习"      # 完整RAG问答
```
