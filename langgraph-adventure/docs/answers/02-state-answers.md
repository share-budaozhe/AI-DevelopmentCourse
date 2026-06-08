# 02 · 状态管理 — 启发式问题答案

---

### Q1: 为什么 `messages` 要用 `add_messages` reducer 而不是普通覆盖？如果改成覆盖会发生什么？

**答案**：

因为 `messages` 是**对话历史**，多个节点都可能添加消息。如果使用覆盖策略：

```python
# 场景：两个节点都往 messages 里加消息
node_a → 返回 {"messages": [msg_a]}
node_b → 返回 {"messages": [msg_b]}
# 结果：只有 msg_b，msg_a 丢失！
```

用 `add_messages` 后：
```python
# 结果：[msg_a, msg_b] —— 两者都保留
```

这在 Agent 对话中至关重要——每次 LLM 回复、工具调用、系统提示都是独立的消息，必须保留完整的对话链。

---

### Q2: 如果你自己写一个自定义 reducer（比如"取最大值"），它会在什么场景下有用？

**答案**：

```python
from typing import Annotated
from operator import max as max_op  # 没有内置 max reducer，需要自己写

def take_max(a, b):
    """返回两个值中较大的一个"""
    return max(a, b)

class State(TypedDict):
    max_damage_dealt: Annotated[int, take_max]
    # 多个节点各自造成伤害，只记录最大值
```

适用场景：
- **并发竞速**：多个 Agent 同时报价，取最低价
- **风险控制**：实时监控多个指标，取最高风险等级
- **去重**：多个节点推荐同一物品，只保留一个
- **游戏统计**：记录最高分、最大伤害等"极值"指标

---

### Q3: `TypedDict(total=False)` 中 `total=False` 的作用是什么？设为 `True` 会怎样？

**答案**：

`total=False`：所有字段都是**可选的**。节点返回 `{"player_hp": 10}` 时不要求提供所有字段。

`total=True`（默认）：所有字段都是**必需的**。这意味着：
```python
# total=True 时，这段代码会类型报错
def enter_room(state: GameState) -> dict:
    return {"messages": [...]}
    # ❌ 缺少 current_room, player_hp, inventory 等所有其他字段！
```

LangGraph 的节点通常只返回 partial update，所以 `total=False` 是必需的。

---

### Q4: 如果两个节点**同时**修改 `player_hp`（一个 +10，一个 -5），最终结果是多少？

**答案**：

在 LangGraph 中，同一轮（step）内**只有一个节点执行**，所以不会出现"同时"修改——LangGraph 是单线程的顺序执行。

但如果分两轮：
```
step 1: node_a → player_hp: 30 + 10 = 40
step 2: node_b → player_hp: 40 - 5 = 35
```

默认覆盖策略下，最终是 35。

如果有**并行分支**（Send API），LangGraph 使用 reducer 来合并：
```python
player_hp: Annotated[int, lambda a, b: a + b]  # 自定义加法 reducer
# node_a 返回 +10, node_b 返回 -5 → 合并后 +5
```

---

### Q5: State 的这种"全局共享"设计，在多 Agent 协作场景下有什么优势和风险？

**优势**：
- 所有 Agent 共享上下文，无需显式传递
- 检查点自动保存全局状态
- 任何 Agent 都可以读取任何信息

**风险**：
- **命名冲突**：两个 Agent 可能无意中覆盖对方的字段
- **状态膨胀**：随着 Agent 增多，State 变得臃肿
- **耦合**：Agent 之间通过 State 隐式耦合，难以独立演进
- **调试困难**：不知道谁在什么时候改了某个字段

**最佳实践**：用命名空间隔离：
```python
class State(TypedDict):
    agent_a_data: dict     # Agent A 的私有数据
    agent_b_data: dict     # Agent B 的私有数据
    shared_context: str    # 显式的共享数据
```
