# 🤖 AutoGPT 自主 Agent Demo

基于 AutoGPT 核心思想的自主 AI Agent 实现。Agent 接收一个目标，自主完成**规划→思考→行动→观察→学习**的完整循环。

**布道者 · 作品**

## 什么是 AutoGPT

AutoGPT 是一个自主 AI Agent 框架。与传统 ChatBot 不同，Agent 不只是回答问题，而是：

1. 📋 **规划** — 将大目标分解为 3-5 个可执行的子任务
2. 🧠 **思考** — 基于上下文和历史经验推理下一步行动
3. ⚡ **行动** — 调用真实工具（搜索/代码/文件/网页）
4. 👁️ **观察** — 分析执行结果，评估是否达成目标
5. 💾 **学习** — 将成功经验和知识存入长期记忆

## 快速开始

```bash
cd autogpt-demo
pip install -r requirements.txt

# 零配置体验（模拟模式，无需 API Key）
python main.py                  # 交互模式
python main.py --demo           # 演示模式

# LLM 驱动模式（需要 API Key）
cp .env.example .env            # 编辑 .env 填入 OPENAI_API_KEY
python main.py --goal "你的目标" --live
```

## 运行模式

| 命令 | 说明 | API Key |
|------|------|:--:|
| `python main.py` | 交互式菜单 | 否 |
| `python main.py --demo` | 演示模式 | 否 |
| `python main.py --goal "xxx"` | 指定目标（模拟推理） | 否 |
| `python main.py --goal "xxx" --live` | 真实 LLM 驱动 | 是 |
| `python main.py --goal "xxx" --max-iter 15` | 自定义迭代次数 | 否 |
| `python main.py --goal "xxx" --resume` | 从检查点恢复 | 否 |
| `python main.py --config` | 显示配置 | 否 |
| `python main.py --list-tools` | 列出工具 | 否 |

## 项目结构

```
autogpt-demo/
├── main.py                      # 🚀 主入口 (Rich CLI)
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── config.py                # ⚙️ 配置 + Prompt 模板
│   ├── agent/
│   │   └── core.py              # 🧠 Agent 核心引擎 (Plan→Think→Act→Observe)
│   ├── tools/
│   │   ├── base.py              #   工具基类 + Registry
│   │   └── tools.py             #   WebSearch / FileOps / CodeExec / WebBrowse
│   └── memory/
│       └── memory.py            # 💾 ShortTerm / LongTerm / WorkingMemory
├── workspace/                   # 📁 Agent 工作目录
├── tests/
│   └── test_autogpt.py          # 🧪 50 个测试用例
└── docs/
    ├── 部署文档.md               # 🔧 环境要求、安装步骤、Docker 部署
    ├── 使用指南.md               # 📖 运行模式、菜单说明、最佳实践
    ├── 测试说明.md               # 🧪 测试策略、测试结构、运行指南
    ├── 实现原理.md               # 🔬 架构设计、核心循环、记忆系统
    └── 流程图.md                 # 🗺️ 执行流程 / Think-Act-Observe / 记忆数据流
```

## 核心架构

```
用户目标 → [Plan] → [Think] → [Act] → [Observe] → [Summary]
              │         │         │         │
              │    ┌────▼────┐ ┌─▼─────────▼─┐
              │    │ Memory  │ │  ToolRegistry │
              │    ├─────────┤ ├──────────────┤
              │    │ ShortTerm│ │ web_search   │
              │    │ LongTerm │ │ file_ops     │
              │    │ Working  │ │ code_exec    │
              │    └─────────┘ │ web_browse   │
              │                └──────────────┘
              └────── 记忆支持每一步决策 ──────┘
```

## 可用工具

| 工具 | 命令 | 功能 |
|------|------|------|
| 🌐 网络搜索 | `web_search` | DuckDuckGo 搜索互联网信息 |
| 📁 文件操作 | `file_ops` | 读写 workspace 目录中的文件 |
| 💻 代码执行 | `code_exec` | 在子进程中执行 Python 代码 |
| 🌍 网页浏览 | `web_browse` | 抓取并解析网页内容 |

## 测试

```bash
# 运行全部测试
pytest tests/ -v              # 50 tests ✅

# 按模块运行
pytest tests/ -v -k "TestTools"
pytest tests/ -v -k "TestMemory"
pytest tests/ -v -k "TestAgentCore"
pytest tests/ -v -k "TestIntegration"
```

## 文档

| 文档 | 内容 |
|------|------|
| [部署文档](docs/部署文档.md) | 环境要求、安装步骤、Docker 部署、配置说明 |
| [使用指南](docs/使用指南.md) | 运行模式详解、交互菜单、模拟 vs LLM、最佳实践 |
| [测试说明](docs/测试说明.md) | 测试策略、测试结构、运行方法、覆盖率要求 |
| [实现原理](docs/实现原理.md) | 核心架构、Plan-Think-Act-Observe 循环、记忆系统、设计模式 |
| [流程图](docs/流程图.md) | 整体流程、Think-Act-Observe 详解、数据流、异常处理 |

## 技术栈

| 组件 | 用途 |
|------|------|
| LangChain OpenAI | LLM 接口封装 |
| ChromaDB | 长期记忆向量存储 |
| DuckDuckGo Search | 免费网络搜索 |
| BeautifulSoup4 | 网页内容解析 |
| Rich | 终端 UI 美化 |
| Pytest | 测试框架 |

## 许可

本项目仅供学习、研究和交流目的使用。布道者出品。
