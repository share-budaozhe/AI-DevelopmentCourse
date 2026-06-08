# 04 · 条件路由 — 启发式问题答案

---

### Q1: 路由函数为什么必须是纯函数？如果路由函数修改了 state，会出现什么后果？

**答案**：

LangGraph 的路由函数在"规划阶段"被调用——图引擎在执行下一步之前调用它来决定路径。如果此时修改了 state：

```python
# ❌ 在路由中改状态
def route_from_room(state):
    state["last_route_time"] = time.time()  # 侧效应！
    return "initiate_combat"
```

后果：
1. **非确定性行为**：修改可能被保留也可能被丢弃，取决于 LangGraph 内部实现
2. **检查点污染**：状态在"规则阶段"被修改，检查点记录的是中间态
3. **并发不安全**：如果 LangGraph 未来支持并行路由评估，会产生竞态条件
4. **调试地狱**：状态变更的来源无法追踪

**正确做法**：在节点中修改，在路由中只读。

---

### Q2: 什么是"循环边"？在我们的 Demo 中，`enter_room → enter_room` 会形成循环，什么情况下这样设计是合理的？

**答案**：

循环边是**节点指向自己的边**。在我们的 Demo 中，`route_from_room` 可能返回 `"enter_room"`，形成自循环。

**合理场景**：
- **空闲等待**：Agent 在等待外部事件期间不断检查状态
- **轮询模式**：每隔 N 步检查某个条件
- **默认重试**：操作失败后重试直到成功或达到上限

**应该避免的场景**：
- **无退出条件的死循环**：会导致图永远运行
- **不必要的循环**：如果状态没变，循环没有意义

**安全实践**：
```python
def route_with_limit(state):
    state["loop_count"] = state.get("loop_count", 0) + 1
    if state["loop_count"] > 10:
        return "timeout"  # 强制退出
    return "retry"
```

---

### Q3: 假如你想实现"玩家生命低于 10 时自动使用治疗药水"，应该在哪里加这个逻辑？

**答案**：

**最佳做法：在移动节点（或回合结束节点）中检查并在进入房间前处理。**

```python
def auto_heal(state: GameState) -> dict:
    hp = state.get("player_hp", 0)
    inventory = state.get("inventory", [])

    if hp < 10 and hp > 0 and "治疗药水" in inventory:
        new_inv = [i for i in inventory if i != "治疗药水"]
        return {
            "player_hp": min(hp + 15, state.get("max_hp", 30)),
            "inventory": new_inv,
            "messages": [("ai", "🧪 生命值过低，自动使用治疗药水！+15 HP")],
        }

    if hp <= 0:
        return {"game_over": True}

    return {}
```

然后在图中插入：
```python
graph.add_edge("move_player", "auto_heal")
graph.add_conditional_edges("auto_heal", route_after_combat, {
    "enter_room": "enter_room",
    "game_over": "game_over",
})
```

**为什么不放路由中**：路由是"只读决策"，不应修改状态。自动治疗需要修改 `player_hp` 和 `inventory`，所以必须在节点中。

---

### Q4: `add_conditional_edges` 的第三个参数（路由表）要求列出所有可能的返回值。如果漏写一个，会发生什么？

**答案**：

LangGraph 在**编译时**会验证路由表是否覆盖所有可能返回值。如果漏写：

```python
graph.add_conditional_edges("enter_room", route, {
    "go_left": "left_room",
    "go_right": "right_room",
    # 漏了 "go_straight"！
})
```

编译阶段会**抛出异常**，指出路由函数可能返回 `"go_straight"` 但路由表中没有。

这是 LangGraph 的**安全性设计**——宁愿编译失败也不要运行时静默跳转到状态异常。

如果你故意想忽略某些返回值，可以加一个 fallback：
```python
graph.add_conditional_edges("enter_room", route, {
    "go_left": "left_room",
    "go_right": "right_room",
    "go_straight": END,  # 显式处理
})
```

---

### Q5: 如果你有 5 个不同的战斗节点（近战/远程/魔法/道具/防御），条件路由函数会变得多复杂？如何管理？

**答案**：

当路由变复杂时，采用**策略模式**：

```python
# 策略表
COMBAT_ACTIONS = {
    "近战": {"node": "melee_attack", "requires": ["武器"]},
    "远程": {"node": "ranged_attack", "requires": ["弓", "箭"]},
    "魔法": {"node": "magic_attack", "requires": ["法杖", "魔力"]},
    "道具": {"node": "use_item", "requires": []},
    "防御": {"node": "defend", "requires": []},
}

def route_combat(state):
    user_input = get_last_user_input(state)
    inventory = state.get("inventory", [])

    action = COMBAT_ACTIONS.get(user_input)
    if action:
        required = action["requires"]
        if all(r in inventory for r in required):
            return action["node"]
        return "error_missing_requirements"

    return "unknown_action"
```

更好的做法：**子图（Subgraph）**：
```python
combat_subgraph = StateGraph(CombatState)
combat_subgraph.add_node("melee", melee_attack)
combat_subgraph.add_node("ranged", ranged_attack)
# ... 战斗子图内部的复杂路由 ...

main_graph.add_node("combat_engine", combat_subgraph.compile())
```

子图让复杂度模块化，主图只需知道"进入战斗引擎"，而战斗引擎内部的路由对外透明。
