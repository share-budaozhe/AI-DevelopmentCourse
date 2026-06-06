# 03 · 节点与边：图的"肉"与"骨"

## 🧠 一句话总结

节点是图的"计算单元"，边是图中的"路径"。节点不决定去哪儿，边决定。

---

## 🔲 节点（Node）：做一件事，把它做好

### 节点签名

所有节点函数都遵循同样的签名：

```python
def node_name(state: GameState) -> dict:
    # 1. 读取 state
    # 2. 执行逻辑
    # 3. 返回 partial state update
    return {"field": new_value, "messages": [...], ...}
```

**输入**：完整的 `GameState`  
**输出**：一个 dict，表示你想修改的状态字段  
**不做的**：不直接调用其他节点，不决定下一步去哪儿

### 我们的节点一览

| 节点 | 文件位置 | 功能 |
|------|---------|------|
| `enter_room` | `nodes.py:76` | 展示房间信息 |
| `pickup_items` | `nodes.py:89` | 拾取地上物品 |
| `initiate_combat` | `nodes.py:108` | 初始化战斗状态 |
| `player_attack` | `nodes.py:132` | 执行攻击回合 |
| `flee_combat` | `nodes.py:195` | 尝试逃跑 |
| `solve_puzzle` | `nodes.py:213` | 展示谜题 |
| `move_player` | `nodes.py:246` | 移动到新房间 |
| `game_over_screen` | `nodes.py:274` | 展示结局 |
| `wait_for_input` | `graph.py:143` | **Human-in-the-Loop** 暂停点 |

### 节点设计原则

```
✅ 好的节点                           ❌ 不好的节点
─────────────────────────           ─────────────────────
单一职责，只做一件事                 一个节点做三件事
不调用其他节点                      节点里 if-else 调不同节点
返回 partial update                 返回完整 state（浪费）
不关心"接下来去哪儿"                硬编码路由逻辑
```

---

## 🔗 边（Edge）：连接世界的线

### 固定边 vs 条件边

```python
# ── 固定边：A 总是去 B ──
graph.add_edge("pickup_items", "enter_room")
# pickup_items 执行完 → 一定进入 enter_room

# ── 条件边：A 根据 state 决定去 B/C/D ──
graph.add_conditional_edges(
    "enter_room",              # 起点
    route_from_room,            # 路由函数
    {
        "initiate_combat": "initiate_combat",   # route 返回这个 → 去这个节点
        "solve_puzzle": "solve_puzzle",
        "pickup_items": "pickup_items",
        "enter_room": "enter_room",
    },
)
```

### 路由函数深入

打开 `src/graph.py:36`，看 `route_from_room()`：

```python
def route_from_room(state: GameState) -> Literal["initiate_combat", ...]:
    room_id = state.get("current_room", "")
    room = get_room(room_id)
    if not room:
        return "enter_room"

    room_type = room.room_type

    if room_type in ("combat", "boss") and room.monster_id:
        if not state.get("combat_active", False):
            return "initiate_combat"    # 👈 触发战斗

    if room_type == "puzzle" and room.puzzle_id:
        if room.puzzle_id not in state.get("solved_puzzles", []):
            return "solve_puzzle"       # 👈 触发解谜

    if room_type == "treasure" and room.items:
        if any(item not in state.get("inventory", []) for item in room.items):
            return "pickup_items"       # 👈 触发捡物品

    return "enter_room"                 # 默认展示房间
```

这个函数就是"游戏的大脑"——它根据房间类型和当前状态，决定玩家会经历什么。

---

## 🎨 图的可视化结构

```
                    ┌──────────┐
                    │ enter_room│ ← 起点，也是枢纽
                    └─────┬────┘
                          │ route_from_room()
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
     ┌────────────┐ ┌──────────┐ ┌────────────┐
     │initiate_   │ │solve_    │ │pickup_     │
     │combat      │ │puzzle    │ │items       │
     └─────┬──────┘ └────┬─────┘ └─────┬──────┘
           │             │             │
           └─────────────┼─────────────┘
                         │ 固定边
                         ▼
                    ┌──────────┐
                    │ enter_room│ ← 循环回到枢纽
                    └─────┬────┘
                          │ route_after_enter()
                    ┌─────┴─────┐
                    ▼           ▼
                 END        wait_for_input
                                │
                           (外部输入)
                                │
                     _route_user_input()
                    ┌───┬───┬───┬───┐
                    ▼   ▼   ▼   ▼   ▼
                  move attack flee puzzle ...
```

---

## 💭 启发式问题

1. 为什么节点不应该调用下一个节点？如果你在 `enter_room` 里直接调用 `initiate_combat()`，会出现什么问题？
2. 条件路由函数必须是**纯函数**吗？如果 `route_from_room()` 内部修改了 state，会发生什么？
3. 你能想到哪些场景适合用固定边，哪些适合用条件边？给出实际例子。
4. 如果图中有 20 个节点和 50 条边，你会如何测试这张图的正确性？
5. 假如你想加一个"中毒"机制（每走一步扣 1 HP），应该在哪里加？是加节点还是改路由？

---

👉 下一步：[04 · 条件路由](./04-conditional-routing.md)

💭 答案：[03-节点与边-答案](./answers/03-nodes-answers.md)
