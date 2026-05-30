# RAG Demo 学习路径

从零理解检索增强生成，按以下六个阶段循序渐进。

---

## 第一阶段：理解 RAG 是什么（10分钟）

### 目标
搞清楚 RAG 解决了什么问题，整体数据流是怎样的。

### 动手
```powershell
# 先本地跑一遍，感受没有 LLM 时 RAG 能做什么
python main.py build
python main.py ask "机器学习有哪些类型"
```

观察输出，注意两个关键环节：
1. **检索** → 从 3 篇文档中找到了 4 个相关片段，按相关度排序
2. **回答** → 因为没接 LLM，直接把检索到的原文展示出来

### 阅读
打开 [data/documents/rag_explained.txt](/C:/Users/Lenovo/Documents/New project/rag-demo/data/documents/rag_explained.txt)，这篇文档就是这个 demo 的理论基础。

### 总结
RAG = 从知识库检索 + 让 LLM 基于检索结果回答。核心管线：

```
离线：文档 → 分块 → 向量化 → 存入向量库
在线：查询 → 向量化 → 检索Top-K → 拼接上下文 → LLM生成
```

---

## 第二阶段：文档加载与分块（20分钟）

### 目标
理解为什么要把文档切开，以及怎么切。

### 核心文件
[src/loader.py](/C:/Users/Lenovo/Documents/New project/rag-demo/src/loader.py)

### 关键概念
| 概念 | 代码位置 | 说明 |
|------|----------|------|
| `DocumentLoader` | 第 23 行 | 遍历目录读取所有 .txt |
| `TextSplitter` | 第 42 行 | 按分隔符递归切分，保证每块不超过 chunk_size |
| `ChunkingPipeline` | 第 90 行 | 串联加载→清洗→分块的流水线 |

### 动手实验
```python
# 在项目目录下开个 Python 交互环境
$env:PYTHONIOENCODING='utf-8'; python

>>> from src.loader import TextSplitter
>>> text = "第一段。第二段很长" * 50
>>> splitter = TextSplitter(chunk_size=200, chunk_overlap=50)
>>> chunks = splitter.split_with_overlap(text)
>>> for i, c in enumerate(chunks):
>>>     print(f"块{i}: 长度={len(c)}, 开头={c[:30]}")
```

### 思考题
1. `chunk_overlap=100` 有什么用？去掉会怎样？
2. 如果把 `chunk_size` 从 500 改成 100，会多出多少块？
3. 分隔符顺序 `["\n\n", "\n", "。", ".", " ", ""]` 为什么这样排？

---

## 第三阶段：文本向量化（20分钟）

### 目标
理解文本怎么变成计算机能比较的向量。

### 核心文件
[src/embedder.py](/C:/Users/Lenovo/Documents/New project/rag-demo/src/embedder.py)

### 关键概念
| 概念 | 代码位置 | 说明 |
|------|----------|------|
| 分词 `_tokenize` | 第 24 行 | 把中文逐字拆开，英文单词保留 |
| TF（词频） | 第 57 行 | 某个词在一段文本中出现几次 |
| IDF（逆文档频率） | 第 43 行 | 某个词在整个语料中是否罕见 |
| L2归一化 | 第 66 行 | 让向量长度为1，方便余弦相似度计算 |

### 动手实验
```python
$env:PYTHONIOENCODING='utf-8'; python

>>> from src.embedder import Embedder
>>> docs = ["我喜欢机器学习", "机器学习很有趣", "今天天气很好"]
>>> emb = Embedder()
>>> emb.fit(docs)
>>> print(f"词表: {list(emb.vocabulary.keys())}")
>>> vec = emb.embed_query("什么是机器学习")
>>> # 看看哪些词权重最高
>>> for word, idx in emb.vocabulary.items():
>>>     if vec[idx] > 0:
>>>         print(f"{word}: {vec[idx]:.4f}")
```

### 思考题
1. 为什么"机器学习"在查询向量中权重高，"天气"权重低？
2. TF-IDF 和 BERT/sentence-transformers 产生的向量有什么本质区别？
3. L2 归一化后点积为什么就等于余弦相似度？

---

## 第四阶段：向量存储与检索（20分钟）

### 目标
理解向量数据库的核心操作：存和搜。

### 核心文件
[src/store.py](/C:/Users/Lenovo/Documents/New project/rag-demo/src/store.py) —— 向量存储
[src/retriever.py](/C:/Users/Lenovo/Documents/New project/rag-demo/src/retriever.py) —— 检索器

### 关键概念
| 概念 | 代码位置 | 说明 |
|------|----------|------|
| `add` | store.py 第 47 行 | 把向量+文本+元数据一起存 |
| `search` | store.py 第 59 行 | 余弦相似度检索 Top-K |
| `retrieve` | retriever.py 第 37 行 | 查询→向量→检索→过滤→排序 |
| `format_context` | retriever.py 第 56 行 | 拼成 LLM 能读的上下文 |

### 动手实验
```python
$env:PYTHONIOENCODING='utf-8'; python

>>> from src.store import VectorStore
>>> import numpy as np
>>> # 创建几个二维向量
>>> store = VectorStore(persist_path="test.json")
>>> store.add(
>>>     ids=["a", "b", "c"],
>>>     embeddings=np.array([[1.0,0.0], [0.0,1.0], [0.7,0.7]]),
>>>     documents=["苹果很好吃", "香蕉是黄色的", "苹果和香蕉都是水果"],
>>> )
>>> # 查询"水果"——应该是 [0.7, 0.7] 相关性最高
>>> query = np.array([0.7, 0.7])
>>> hits = store.search(query, top_k=2)
>>> for h in hits:
>>>     print(f"score={h['score']:.4f} text={h['text']}")
>>> store.clear()  # 清理测试数据
```

### 思考题
1. `top_k=5` 和 `top_k=1` 对最终答案有什么影响？
2. `min_score` 过滤阈值设多少合适？
3. 这个 JSON 持久化的向量库在 10 万条数据时有什么问题？

---

## 第五阶段：答案生成（15分钟）

### 目标
理解怎么把检索结果喂给 LLM，以及提示词工程的核心要点。

### 核心文件
[src/generator.py](/C:/Users/Lenovo/Documents/New project/rag-demo/src/generator.py)

### 关键概念
| 概念 | 代码位置 | 说明 |
|------|----------|------|
| `PROVIDERS` 配置 | 第 33 行 | 多后端自动切换 |
| `_detect_provider` | 第 58 行 | 按环境变量检测可用后端 |
| `_generate_llm` | 第 85 行 | 构建消息发给 LLM |
| `SYSTEM_PROMPT` | 第 15 行 | 控制 LLM 行为的核心 |
| `USER_PROMPT_TMPL` | 第 27 行 | 把检索上下文和问题拼在一起 |

### 动手实验
```powershell
# 设置 DeepSeek key 后运行
$env:DEEPSEEK_API_KEY = "sk-..."
python main.py ask "Python有哪些数据处理库"
```

观察输出中的 `模式: LLM (DeepSeek)`，对比本地模式和 LLM 模式回答的差异：
- 本地模式：原文堆砌
- LLM 模式：总结提炼，结构化输出

### 思考题
1. 如果 SYSTEM_PROMPT 去掉第2条"充分利用所有参考文档"，输出会有什么变化？
2. `max_tokens=2048` 设太小会截断，设太大会怎样？
3. 怎么用 `$env:OPENAI_API_KEY` 切回 OpenAI？看代码里哪一行决定了优先级？

---

## 第六阶段：串联完整管线（15分钟）

### 目标
把五个模块串起来，理解 main.py 里的完整数据流。

### 核心文件
[main.py](/C:/Users/Lenovo/Documents/New project/rag-demo/main.py)

### 关键函数调用链

```
cmd_ask("什么是机器学习")
  │
  ├─ Embedder.fit(store.documents)    ← 从已存文档重建 TF-IDF 模型
  ├─ retriever.retrieve(query)        ← 查询→向量→检索
  │    ├─ embedder.embed_query()      ← 查询向量化
  │    └─ store.search()              ← 余弦相似度 Top-K
  │
  └─ generator.generate(query, results, context)
       ├─ _generate_llm()             ← 调 DeepSeek/OpenAI
       └─ _generate_local()           ← 无 Key 时的降级方案
```

### 动手实验

**实验1：加入你自己的文档**
```powershell
# 在 data/documents/ 下新建一个 txt 文件
echo "你的内容..." > data/documents/my_doc.txt
python main.py build
python main.py ask "关于你的文档的问题"
```

**实验2：调整检索参数**
修改 `main.py` 顶部的 `TOP_K = 5` → `TOP_K = 3`，看看检索结果变少对答案有什么影响。

**实验3：对比分块效果**
修改 `main.py` 顶部的 `CHUNK_SIZE = 200`，重新 `python main.py build`，看看分块变细后检索结果有什么变化。

---

## 进阶方向

1. **替换嵌入模型**：把 `embedder.py` 换成 sentence-transformers（`pip install sentence-transformers`），从 TF-IDF 稀疏向量升级为语义稠密向量，检索质量会大幅提升。

2. **替换向量数据库**：把 `store.py` 的 JSON 存储换成 ChromaDB 或 FAISS，支持百万级检索。

3. **加入重排序**：在 `retriever.py` 里加入 Cross-Encoder 对 Top-K 结果重新排序。

4. **查询优化**：加入查询重写（Query Rewriting）或 HyDE（先让 LLM 生成假设答案再检索）。

5. **多路召回**：同时用 TF-IDF 和语义向量两路检索，再加融合排序。
