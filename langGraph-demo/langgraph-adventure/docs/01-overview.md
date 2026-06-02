# 01 · LangGraph 概览：什么是"图"？

## 🧠 一句话总结

**LangGraph 是一个用"有向图"来编排 AI Agent 工作流的框架。**

如果把 LangChain 比作"链"（Chain）——一条流水线从头走到尾——那 LangGraph 就是"图"（Graph）——允许分支、循环、条件跳转和暂停等待。

---

## 🎮 在我们的 Demo 中

打开 `src/graph.py`，你会看到这样的结构：

```
进入房间 → 检查房间类型 → 战斗？/ 解谜？/ 捡物品？
                ↑              ↓
                └──── 回到房间 ←┘
                         ↓
                   等待玩家输入
                         ↓
                   移动 / 攻击 / 逃跑
                         ↓
                   再次进入房间 ...
```

这比线性的 if-else 链灵活得多：你可以从任意节点跳转到任意节点，还可以在中途暂停等待输入。

---

## 🏗️ 图的核心组成

```
┌──────────────────────────────────────────────────┐
│              LangGraph 图的五要素                  │
├────────────┬─────────────────────────────────────┤
│ State      │ 所有节点共享的状态字典               │
│            │ → 看 src/state.py                    │
├────────────┼─────────────────────────────────────┤
│ Nodes      │ 处理函数，接收 state，返回 partial    │
│            │ → 看 src/nodes.py                    │
├────────────┼─────────────────────────────────────┤
│ Edges      │ 固定边（A→B）和条件边（A→?→B/C/D）   │
│            │ → 看 src/graph.py                    │
├────────────┼─────────────────────────────────────┤
│ Entry/Exit │ 图的起点和终点                       │
│            │ → SET_START / END                    │
├────────────┼─────────────────────────────────────┤
│ Checkpoint │ 持久化状态，支持中断恢复             │
│            │ → MemorySaver / SqliteSaver          │
└────────────┴─────────────────────────────────────┘
```

---

## 📊 与普通程序的对比

| 传统程序 | LangGraph |
|---------|-----------|
| 函数调用函数 | 图通过"边"连接节点 |
| 状态通过参数传递 | 状态是全局共享的字典 |
| 控制流用 if/while | 条件边决定路由 |
| 无法中途暂停 | interrupt() 暂停等待输入 |
| 重启需要手动保存 | checkpoint 自动持久化 |

---

## 🔑 关键理念

### 1. 节点是"纯函数"

每个节点只做一件事：读 state，返回 partial update。它不调用下一个节点——图结构决定谁调用谁。

```python
# nodes.py: enter_room
def enter_room(state: GameState) -> dict:
    """展示房间信息，不修改状态"""
    room_id = state.get("current_room", "entrance")
    room = get_room(room_id)
    room_text = _format_room(room_id, state)
    return {"messages": [("ai", room_text)]}
    # 注意：这里没有 "接下来调用 XXX" 的逻辑
```

### 2. 路由与计算分离

"做什么" 由节点决定；"去哪里" 由条件边决定。这种分离让代码更容易测试和修改。

### 3. Human-in-the-Loop 是一等公民

`interrupt()` 不是 hack，而是 LangGraph 的核心机制。它允许图在任何位置暂停，等待外部输入后再继续。

---

## 🔍 查看关键源码

| 文件 | 作用 |
|------|------|
| `src/graph.py` | `build_adventure_graph()` 函数——组装整张图 |
| `src/state.py` | `GameState` TypedDict——状态定义 |
| `src/nodes.py` | 所有节点函数 |
| `src/main.py` | `run_game()` 主循环——invoke/resume 交互 |

---

## 💭 启发式问题

1. 为什么 LangGraph 选择"图"而不是"链"作为编排模型？什么场景下图优于链？
2. 如果把 `enter_room()` 改成直接调用 `initiate_combat()`，会带来什么问题？
3. 状态（State）和普通 Python 函数参数有什么区别？为什么图需要共享状态？
4. 你能否想到一个现实中适合用 LangGraph 建模的业务流程？（提示：审批流、客服机器人、多步骤数据管道）

---

👉 下一步：[02 · 状态管理详解](./02-state.md)
