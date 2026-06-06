# 🏰 AI 地牢探险 · LangGraph 学习 Demo

一个用 **LangGraph** 状态图驱动的交互式文字冒险游戏，通过游戏化的方式学习 LangGraph 的核心概念。

## 🎮 游戏简介

你是一名冒险者，闯入了一座古老的地牢。地牢中有：

| 区域 | 挑战 |
|------|------|
| 🚪 地牢入口 | 起点，选择方向 |
| 🌑 黑暗走廊 | 探索，发现线索 |
| 👹 地精巢穴 | 战斗：地精守卫 |
| ⚔️ 废弃军械库 | 获取装备 |
| 🧩 谜题密室 | 解谜开锁 |
| 🐉 龙穴 | Boss 战：远古火龙 |
| 💎 封印宝库 | 需要钥匙 |
| 🌅 出口 | 胜利！ |

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 进入项目目录
cd langgraph-adventure

# 3. 运行游戏
python -m src.main
```

## 📖 项目结构

```
langgraph-adventure/
├── README.md                    # 项目说明
├── requirements.txt             # Python 依赖
├── src/
│   ├── __init__.py
│   ├── main.py                  # 🎮 游戏入口 & 主循环
│   ├── state.py                 # 📋 LangGraph 状态定义 (TypedDict)
│   ├── graph.py                 # 🔗 图的组装 (核心！)
│   ├── nodes.py                 # 🔲 节点函数
│   ├── tools.py                 # 🔧 工具定义
│   └── adventure_data.py        # 🗺️ 游戏世界数据
└── docs/                        # 📚 详细学习文档（见下方）
```

## 🎯 LangGraph 学习要点

| 概念 | 对应源码 | 说明 |
|------|---------|------|
| **State** | `state.py` | TypedDict + Annotated 定义状态 |
| **Nodes** | `nodes.py` | 纯函数节点，接收 state 返回 partial update |
| **Edges** | `graph.py` | 固定边 + 条件边实现流程控制 |
| **Conditional Routing** | `graph.py` → `route_*` | 基于状态的条件分发 |
| **Tools** | `tools.py` | @tool 装饰器 + 外部能力封装 |
| **Human-in-the-Loop** | `graph.py` → `interrupt()` | 暂停图执行等待外部输入 |
| **Checkpoints** | `graph.py` → `MemorySaver` | 状态持久化与恢复 |

## 📚 详细文档

所有文档位于 `docs/` 目录：

1. [LangGraph 概览](docs/01-overview.md)
2. [状态管理详解](docs/02-state.md)
3. [节点与边](docs/03-nodes-and-edges.md)
4. [条件路由](docs/04-conditional-routing.md)
5. [工具集成](docs/05-tools.md)
6. [Human-in-the-Loop](docs/06-human-in-loop.md)
7. [检查点与持久化](docs/07-checkpoints.md)

每篇文档末尾都包含 **启发式问题**，答案在 `docs/answers/` 目录中。
