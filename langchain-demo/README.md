# LangChain 学习 Demo

一套覆盖 LangChain 核心应用场景的演示代码，配有详细的知识点文档、启发性问题和参考答案。
每个 Demo 都支持 **演示模式** (自动运行) 和 **交互模式** (动手实验)。

## 项目结构

```
langchain-demo/
├── main.py                        # 总入口，支持 --guided / --interactive
├── requirements.txt
├── .env.example                   # 支持 OpenAI + DeepSeek
├── README.md
├── demos/
│   ├── config.py                  # 统一 LLM 配置模块
│   ├── demo_01_basics.py          # 基础 + 交互式自由提问/角色扮演/翻译
│   ├── demo_02_chains.py          # Chains + 交互式链实验台
│   ├── demo_03_rag.py             # RAG + 交互式知识库问答
│   ├── demo_04_agents.py          # Agents + 交互式智能助手
│   └── demo_05_memory.py          # Memory + 交互式多轮对话/会话切换
├── data/                          # RAG 知识文档
└── docs/                          # 学习文档
    ├── overview.md
    ├── 01_basics.md ~ 05_memory.md
    ├── questions/                 # 启发性问题 (40+ 题)
    └── answers/                   # 参考答案
```

## 快速开始

```bash
pip install -r requirements.txt
copy .env.example .env   # 编辑填入 API Key
python main.py           # 菜单选择模式
```

## 使用方式

### 主入口 main.py

| 命令 | 说明 |
|------|------|
| `python main.py` | 菜单选择 (可输入 g/i/数字) |
| `python main.py --guided` | 演示模式: 运行全部 |
| `python main.py --guided 1 3` | 演示模式: 运行 Demo 01, 03 |
| `python main.py --interactive 1` | 交互模式: Demo 01 自由提问 |
| `python main.py --interactive 3` | 交互模式: Demo 03 RAG 问答 |

### 单独运行 Demo

```bash
python demos/demo_01_basics.py   # 启动后选择 [1]演示 或 [2]交互
python demos/demo_03_rag.py      # 交互模式可自由提问知识库
```

### 每个 Demo 的交互功能

| Demo | 交互模式功能 | 命令 |
|------|-------------|------|
| 01 基础 | 自由提问 / 角色扮演 / 翻译 | `/qa` `/role` `/trans` |
| 02 Chains | 翻译链 / 笑话+冷知识 / 摘要 / 词汇解释 / 字数统计 | `/trans` `/joke` `/summary` `/explain` `/count` |
| 03 RAG | 基于知识库的问答，显示检索来源 | `/sources` |
| 04 Agents | 自由向 Agent 提问，观察工具调用过程 | `/trace` `/tools` |
| 05 Memory | 多轮对话，会话切换/查看历史/清除 | `/switch` `/history` `/clear` `/sessions` |

统一退出命令: `/quit`

## Demo 说明

| Demo | 主题 | 涉及概念 |
|------|------|----------|
| 01 | 基础 | ChatOpenAI, ChatPromptTemplate, StrOutputParser, CommaSeparatedListOutputParser, LCEL |
| 02 | Chains | RunnableParallel, RunnablePassthrough, RunnableLambda, itemgetter, 管道 `|` |
| 03 | RAG | TextLoader, RecursiveCharacterTextSplitter, Embeddings, Chroma, 检索链 |
| 04 | Agents | @tool 装饰器, create_react_agent, ReAct 循环, 多工具协同 |
| 05 | Memory | RunnableWithMessageHistory, InMemoryChatMessageHistory, 多会话隔离 |

## 学习路径

1. 先阅读 `docs/overview.md` 了解整体架构
2. 运行每个 Demo 的演示模式，观察输出
3. 进入交互模式，动手实验
4. 阅读对应的 `docs/0X_xxx.md` 理解知识点
5. 思考 `docs/questions/` 中的启发性问题
6. 对照 `docs/answers/` 中的参考答案检查理解
