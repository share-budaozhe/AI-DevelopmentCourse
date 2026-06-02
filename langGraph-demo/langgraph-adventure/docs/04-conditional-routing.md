# 04 · 条件路由：让图学会"选择"

## 🧠 一句话总结

条件路由是 LangGraph 实现**分支逻辑**的机制。条件路由函数根据 state 返回一个字符串，图引擎根据这个字符串选择下一个节点。

---

## 🔀 在我们的 Demo 中

整个游戏的控制流都是条件路由驱动的。打开 `src/graph.py`，你会看到三个关键路由函数：

### 1. 房间路由：`route_from_room(state)`

```python
def route_from_room(state: GameState) -> str:
    room = get_room(state.get("current_room", ""))
    room_type = room.room_type

    if room_type == "combat":
        return "initiate_combat"     # → 战斗
    elif room_type == "puzzle":
        return "solve_puzzle"        # → 解谜
    elif room_type == "treasure":
        return "pickup_items"        # → 捡物品
    else:
        return "enter_room"          # → 展示房间
```

### 2. 战斗后路由：`route_after_combat(state)`

```python
def route_after_combat(state: GameState) -> str:
    if state.get("game_over"):
        return "game_over"           # → 游戏结束画面
    return "enter_room"              # → 继续探索
```

### 3. 用户输入路由：`_route_user_input(state)`

```python
def _route_user_input(state: GameState) -> str:
    # 读取最后一条用户消息
    user_input = get_last_user_message(state)

    if combat_active:
        return "player_attack" if "攻击" in user_input else "flee_combat"

    if "北" in user_input:
        return "move_player"
    ...
```

---

## 🎯 条件路由的核心模式

```
        ┌──────────┐
        │  节点 A   │
        └─────┬────┘
              │
        ┌─────▼──────┐
        │ route(state)│  ← 纯函数，读 state，返回字符串
        └──┬──┬──┬───┘
           │  │  │
      "a"  ▼  ▼  ▼ "c"
          │ "b" │
      ┌────┐ ┌─┐ ┌────┐
      │节点B│ │C│ │节点D│
      └────┘ └─┘ └────┘
```

路由函数必须是**纯函数**：只读 state，不修改 state。如果你在路由里改了 state，图引擎不会感知到。

---

## 🧠 设计模式：用路由替代 if-else

对比传统代码和 LangGraph 的条件路由：

```python
# ❌ 传统方式：硬编码控制流
def handle_room(room):
    if room.type == "combat":
        state = initiate_combat(state)
        state = player_attack(state)
    elif room.type == "puzzle":
        state = solve_puzzle(state)
    state = enter_room(state)
```

```python
# ✅ LangGraph 方式：图定义控制流，节点定义计算
graph.add_conditional_edges("enter_room", route_from_room, {
    "initiate_combat": "initiate_combat",
    "solve_puzzle": "solve_puzzle",
    "pickup_items": "pickup_items",
})
```

LangGraph 的方式让：
- 流程可视化（图就是文档）
- 节点可独立测试
- 路由可独立修改

---

## 🌲 嵌套路由：路由链式组合

在我们的图中，条件路由可以串联：

```
enter_room
    │
    ├─ route_from_room() → combat / puzzle / treasure / enter
    │                              │
    │                         initiate_combat
    │                              │
    │                         (固定边)
    │                              │
    │                         enter_room ← 回到枢纽
    │                              │
    └─ route_after_enter() → END / wait_for_input
                                    │
                               _route_user_input()
                                    │
                              move / attack / flee / ...
```

这种"回到枢纽"再重新路由的模式，在 LangGraph 中非常常见——就像游戏主循环。

---

## 💭 启发式问题

1. 路由函数为什么必须是纯函数？如果路由函数修改了 state，会出现什么后果？
2. 什么是"循环边"？在我们的 Demo 中，`enter_room → enter_room` 会形成循环，什么情况下这样设计是合理的？什么情况下你应该避免？
3. 假如你想实现"玩家生命低于 10 时自动使用治疗药水"，应该在哪里加这个逻辑？路由函数中？还是节点中？
4. `add_conditional_edges` 的第三个参数（路由表）要求你列出所有可能的返回值。如果你漏写了一个，会发生什么？
5. 如果你有 5 个不同的战斗节点（近战/远程/魔法/道具/防御），条件路由函数会变得多复杂？你如何管理这种复杂度？

---

👉 下一步：[05 · 工具集成](./05-tools.md)

💭 答案：[04-条件路由-答案](./answers/04-routing-answers.md)
