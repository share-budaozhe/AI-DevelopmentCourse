# CrewAI 多 Agent 软件研发团队 Demo

一个基于 [CrewAI](https://crewai.com) 的多智能体协作系统演示。5 个具有不同角色的 AI Agent 组成**软件研发团队**，协同完成从需求分析到部署方案的全流程。

## 核心概念

| 概念 | 说明 |
|------|------|
| **Agent** | 角色驱动的 AI 实体，包含 role（角色）、goal（目标）、backstory（背景） |
| **Task** | 分配给 Agent 的具体工作，支持上下文依赖 |
| **Crew** | 团队编排器，管理 Agent + Task 的协作 |
| **Process** | 执行模式：Sequential（顺序）或 Hierarchical（层级管理） |
| **Tool** | Agent 可调用的外部能力（继承 BaseTool） |
| **Memory** | CrewAI 内置的跨任务记忆机制 |

## 团队成员

```
📋 产品经理  →  🏗️ 架构师  →  💻 开发工程师  →  🧪 测试工程师  →  🚀 DevOps
 PRD文档       技术方案      代码实现        测试报告        部署方案
```

| Agent | 角色 | 工具 | 可委托 |
|-------|------|------|--------|
| 📋 Product Manager | 产品经理 | requirement_analyzer | 否 |
| 🏗️ Architect | 系统架构师 | tech_stack_recommender, knowledge_search | **是** |
| 💻 Developer | 高级开发工程师 | code_reviewer, knowledge_search | 否 |
| 🧪 QA Tester | 测试工程师 | code_reviewer | 否 |
| 🚀 DevOps | 运维工程师 | deploy_checker, knowledge_search | 否 |

## 项目结构

```
crewai-demo/
├── main.py                      # 🚀 主入口（交互/演示/指定需求）
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── config.py                # ⚙️ LLM 多 Provider 配置
│   ├── crew.py                  # 🎯 Crew 编排（构建团队 + 启动执行）
│   ├── agents/                  # 🤖 Agent 定义
│   │   ├── product_manager.py   #   产品经理
│   │   ├── architect.py         #   系统架构师
│   │   ├── developer.py         #   开发工程师
│   │   ├── tester.py            #   测试工程师
│   │   └── devops.py           #   运维工程师
│   ├── tasks/
│   │   └── tasks.py             # 📋 5 个阶段 Task 定义
│   └── tools/
│       └── tools.py             # 🔧 5 个自定义工具
├── tests/
│   └── test_crew.py             # 🧪 完整测试套件
└── docs/
    ├── 项目说明.md               # 项目背景、目标、适用场景
    ├── 实现原理.md               # 架构设计、核心概念、执行流程
    ├── 技术要点.md               # API 详解、调试指南、扩展建议
    └── 流程图.md                 # 可视化流程与架构图
```

## 快速开始

```bash
# 1. 进入项目目录
cd crewai-demo

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 API Key（OpenAI / DeepSeek / Anthropic）

# 4. 运行
python main.py                  # 交互模式
python main.py --demo           # 演示模式（内置示例）
python main.py --topic "你的需求"  # 直接指定需求
```

## 运行模式

| 命令 | 说明 |
|------|------|
| `python main.py` | 交互模式：从 4 个内置项目中选择，或输入自定义需求 |
| `python main.py --demo` | 演示模式：自动运行内置示例（智能客服系统） |
| `python main.py --topic "xxx"` | 直接指定项目需求描述 |
| `python main.py --process hierarchical` | 使用层级管理模式（Manager Agent 调度） |
| `python main.py --demo --output result.txt` | 演示模式 + 保存结果到文件 |

## 执行流程

```
用户输入需求
    │
    ▼
┌─────────────────────────────────────┐
│  📋 Task 1: 需求分析                  │
│  产品经理 → PRD 文档                  │
│  使用: requirement_analyzer          │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  🏗️ Task 2: 架构设计                  │
│  架构师 → 技术方案                    │
│  使用: tech_stack_recommender        │
│        knowledge_search              │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  💻 Task 3: 代码实现                  │
│  开发工程师 → 代码 + API              │
│  使用: code_reviewer, search         │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  🧪 Task 4: 质量测试                  │
│  测试工程师 → 测试报告                │
│  使用: code_reviewer                 │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  🚀 Task 5: 部署方案                  │
│  DevOps → 部署方案 + 运维手册         │
│  使用: deploy_checker, search        │
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

- **CrewAI** — 多 Agent 角色驱动协作框架
- **CrewAI Tools** — 内置工具基类
- **LangChain OpenAI / Anthropic** — LLM 接口封装
- **python-dotenv** — 环境变量管理
- **Rich** — 终端 UI 美化
- **Pytest + pytest-mock** — 测试框架

## 与 LangGraph Demo 对比

本项目与仓库中的 [multi-agent-demo](../multi-agent-demo/) 形成互补：

| 维度 | CrewAI Demo（本项目） | LangGraph Demo |
|------|----------------------|----------------|
| 框架 | CrewAI | LangGraph |
| 理念 | 角色驱动团队协作 | 状态图流程编排 |
| Agent 定义 | role + goal + backstory | 自定义函数 + Prompt |
| 上下文 | 自动传递（context） | 显式 State 管理 |
| 记忆 | 内置 Memory | 共享字典 |
| 流程 | Sequential / Hierarchical | 自定义 Graph DAG |
| 场景 | 软件研发团队 | 内容创作团队 |

## 许可

本项目仅用于学习、研究和交流目的。
