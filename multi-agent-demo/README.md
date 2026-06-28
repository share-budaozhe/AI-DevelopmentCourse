# 多智能体协作系统 Demo (Multi-Agent Collaboration)

一个基于 LangGraph 的多智能体协作系统演示，展示了 5 个 AI Agent 如何通过结构化工作流协同完成从信息调研到最终交付的全流程。

## 核心概念

| 概念 | 说明 |
|------|------|
| **Agent** | 具有特定角色的 AI 实体，配备角色提示词和能力 |
| **工作流** | LangGraph 编排的有向无环图，定义 Agent 执行顺序 |
| **共享上下文** | 基于内存的黑板模式，Agent 间通过读写共享数据协作 |
| **工具** | Agent 可调用的外部功能（知识检索、计算等） |

## 项目结构

```
multi-agent-demo/
├── main.py                      # 主入口（交互/演示/指定话题）
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── config.py                # 统一 LLM 配置（OpenAI/DeepSeek）
│   ├── agents/
│   │   ├── research_agent.py    # 🔍 研究 Agent
│   │   ├── analysis_agent.py    # 📊 分析 Agent
│   │   ├── writer_agent.py      # ✍️  写作 Agent
│   │   ├── reviewer_agent.py    # 📋 审核 Agent
│   │   └── summarizer_agent.py  # 📦 汇总 Agent
│   ├── workflow/
│   │   └── collaboration_graph.py # LangGraph 工作流编排
│   └── tools/
│       └── tools.py             # 共享工具与上下文
├── tests/
│   └── test_agents.py           # 单元测试与集成测试
└── docs/
    └── (详细文档)
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 3. 运行
python main.py                  # 交互模式
python main.py --demo           # 演示模式
python main.py --topic "你的课题"  # 直接指定课题
```

## 运行模式

| 命令 | 说明 |
|------|------|
| `python main.py` | 交互模式：从菜单选择话题，指定文章风格 |
| `python main.py --demo` | 演示模式：自动运行内置示例 |
| `python main.py --topic "xxx"` | 直接研究指定课题 |

## Agent 协作流程

```
用户输入课题
    │
    ▼
┌─────────────────────────────────────┐
│  🔍 Research Agent (研究员)         │
│  任务：信息搜集、知识检索、整理笔记   │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  📊 Analysis Agent (分析师)         │
│  任务：深度分析、趋势识别、洞见提炼   │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  ✍️  Writer Agent (写作专员)        │
│  任务：内容创作、文体适配、初稿输出   │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  📋 Reviewer Agent (审核官)         │
│  任务：质量审查、评分反馈、改进建议   │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  📦 Summarizer Agent (汇总官)       │
│  任务：综合产出、过程回顾、最终交付   │
└──────────────┬──────────────────────┘
               ▼
         最终交付物 🎉
```

## 测试

```bash
# 运行单元测试（无需 API Key）
pytest tests/ -v -k "not Integration"

# 运行全部测试（含集成测试，需要 API Key）
pytest tests/ -v
```

## 技术栈

- **LangChain** — Agent 构建与工具绑定
- **LangGraph** — 状态图工作流编排
- **LangChain OpenAI** — LLM 接口封装
- **python-dotenv** — 环境变量管理
- **Rich** — 终端 UI 美化
- **Pytest** — 单元测试框架
