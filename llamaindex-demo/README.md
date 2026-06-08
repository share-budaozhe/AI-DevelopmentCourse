# 📚 LlamaIndex 学习教程

> 从零掌握 RAG（检索增强生成）与 LlamaIndex 数据框架
> 🆕 支持 **DeepSeek** API | 零成本 Mock 模式 | 本地嵌入

## 项目简介

这是一个系统化的 **LlamaIndex 学习项目**，包含：

- **8 个核心实验** — 从文档加载到 Agent 智能体的完整知识链
- **12 道启发式思考题** — 带着问题学，理解更深
- **9 篇详细文档** — 框架原理、实现细节、最佳实践
- **交互式运行入口** — 菜单导航，选择即运行

## API 配置（三选一）

### 方案 1：DeepSeek ⭐推荐（最便宜）

```bash
# 1. 注册 https://platform.deepseek.com ，获取 API Key
# 2. 创建 .env 文件
echo DEEPSEEK_API_KEY=sk-your-key > .env
echo USE_LOCAL_EMBEDDING=true >> .env

# 3. LLM 用 DeepSeek（≈￥1/百万 token），嵌入用本地模型（免费）
```

### 方案 2：OpenAI

```bash
echo OPENAI_API_KEY=sk-your-key > .env
```

### 方案 3：无 API（Mock 模式）

不配置任何密钥，项目自动以 Mock 模式运行。**索引创建和结构演示完全可用**，只是不能实际调用 LLM。

## 快速开始

```bash
cd llamaindex-demo

# 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Mac/Linux

# 安装依赖
pip install -r requirements.txt

# （可选）配置 DeepSeek API
copy .env.example .env
# 编辑 .env 填入你的 DEEPSEEK_API_KEY

# 运行
python -m src.main
```

## 项目结构

```
llamaindex-demo/
├── README.md
├── .env.example               # 环境变量示例
├── requirements.txt
├── data/sample_docs/          # 3 篇中文示例文档
├── docs/                      # 9 篇学习文档 + 思考题
│   ├── 01-overview.md         #   项目总览
│   ├── 02-documents.md        #   文档与节点
│   ├── 03-indexes.md          #   索引类型
│   ├── 04-retrievers.md       #   检索器
│   ├── 05-query-engines.md    #   查询引擎
│   ├── 06-chat-engines.md     #   对话引擎
│   ├── 07-agents.md           #   Agent
│   ├── 08-advanced.md         #   进阶特性
│   ├── 09-faq.md              #   常见问题
│   └── answers/thinking-questions.md  # 12 道思考题
└── src/
    ├── main.py                #   交互式主入口
    ├── config.py              #   LLM 配置中心 (DeepSeek/OpenAI/Mock)
    ├── sample_data.py         #   示例数据
    ├── demo_documents.py      #   实验 1
    ├── demo_indexes.py        #   实验 2
    ├── demo_retrievers.py     #   实验 3
    ├── demo_query.py          #   实验 4 ← 需要 API
    ├── demo_chat.py           #   实验 5 ← 需要 API
    ├── demo_agents.py         #   实验 6 ← 需要 API
    ├── demo_storage.py        #   实验 7
    └── demo_advanced.py       #   实验 8
```

## 学习路线

| 实验 | 内容 | API | 说明 |
|------|------|-----|------|
| 1 | 文档与节点 | ❌ 不需要 | 理解数据怎么进来 |
| 2 | 索引类型 | ❌ 不需要 | VectorStore vs Summary |
| 3 | 检索器 | ❌ 不需要 | Top-K、相似度阈值 |
| 4 | 查询引擎 | ✅ 需要 | 真实的 LLM 问答 |
| 5 | 对话引擎 | ✅ 需要 | 多轮对话 + 记忆 |
| 6 | Agent | ✅ 需要 | 工具调用 + 自主决策 |
| 7 | 存储 | ❌ 不需要 | 持久化与加载 |
| 8 | 进阶特性 | ❌ 不需要 | 后处理器、管线 |

**建议顺序**：1 → 2 → 3 → 4 → 7 → 5 → 6 → 8

## 费用对比

| 方案 | LLM 成本 | 嵌入成本 | 适合 |
|------|---------|---------|------|
| DeepSeek + 本地嵌入 | ≈￥1/百万 token | 免费 | 学习、小项目 |
| DeepSeek + OpenAI 嵌入 | ≈￥1/百万 token | ≈$0.02/百万 token | 生产小规模 |
| OpenAI (GPT-4o-mini) | ≈$0.15/百万 token | ≈$0.02/百万 token | 不差钱 |
| Mock 模式 | 免费 | 免费 | 结构学习 |

## LlamaIndex 核心流程

```
你的数据 → Document → NodeParser(切分) → Embedding(向量化)
                                              ↓
                                          VectorStore
                                              ↓
用户问题 → Embedding(向量化) → Retriever(检索) → LLM(生成) → 答案
```

## 适合谁

- 🎓 正在学习 RAG 和 LLM 应用开发的**初学者**
- 📝 准备技术面试的**求职者**（深入理解 RAG 原理）
- 🔧 需要快速上手 LlamaIndex 的**工程师**
- 🤔 对「AI + 知识检索」感兴趣的所有人

## License

MIT — 自由学习，自由使用
