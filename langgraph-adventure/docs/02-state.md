# 02 · 状态管理：LangGraph 的"记忆"

## 🧠 一句话总结

State 是图中所有节点共享的"记忆"。每个节点读取它、修改它，图引擎负责合并更新。

---

## 📋 我们的 State 定义

打开 `src/state.py`，核心定义如下：

```python
from typing import Annotated, List, TypedDict
from langgraph.graph.message import add_messages

class GameState(TypedDict, total=False):
    # 使用 add_messages reducer：追加而非覆盖
    messages: Annotated[list, add_messages]

    # 普通字段：覆盖策略
    current_room: str
    player_hp: int
    max_hp: int
    player_attack: int
    inventory: List[str]
    combat_active: bool
    monster_hp: int
    monster_attack: int
    monster_name: str
    solved_puzzles: List[str]
    game_over: bool
    game_won: bool
    pending_decision: bool
```

---

## 🔑 关键概念拆解

### 1. TypedDict —— 类型安全的状态字典

```python
class GameState(TypedDict, total=False):
    current_room: str
    player_hp: int
```

`TypedDict` 是 Python 的类型提示机制，让你在写状态时获得 IDE 自动补全和类型检查。
`total=False` 表示所有字段都是可选的——这在 `return {}` 时不会报错。

### 2. Annotated + Reducer —— 控制合并策略

这是 LangGraph 最重要的设计之一。

```python
messages: Annotated[list, add_messages]
```

当两个节点都想修改 `messages` 时，LangGraph 怎么合并？

- 普通字段：**后写的覆盖先写的**
- `Annotated[list, add_messages]`：**追加不覆盖**

这就像 Git 的 merge strategy：
- 普通字段 = `git merge --strategy=ours`（直接用新版本）
- add_messages = `git merge --strategy=union`（两边都保留）

### 3. 节点如何修改 State

每个节点返回一个 **partial dict**，图引擎负责合并：

```python
def player_attack(state: GameState) -> dict:
    # 读取完整 state
    monster_hp = state.get("monster_hp", 0)
    player_atk = state.get("player_attack", 5)

    # 计算新值
    damage = player_atk + random.randint(-2, 3)
    new_monster_hp = monster_hp - damage

    # 返回 partial update
    # 图引擎会将这个 dict 合并到全局 state
    return {
        "monster_hp": new_monster_hp,          # 覆盖
        "messages": [("ai", f"造成 {damage} 点伤害")],  # 追加
    }
```

你不需要返回整个 state，只需要返回你修改的部分。

---

## 🎮 在我们的游戏中

游戏的所有数据都在 `GameState` 中流转：

```
enter_room → 读取 current_room，写入 messages
       ↓
initiate_combat → 设置 combat_active=True, monster_hp=20
       ↓
player_attack → 递减 monster_hp, 递减 player_hp
       ↓
enter_room → 重新读取 current_room（没变），展示新状态
```

---

## 🧪 实验：修改 Reducer

试试把 `inventory: List[str]` 改成：

```python
from operator import add
inventory: Annotated[List[str], add]
```

这样两个节点都往背包里加东西时，它们会自动合并（类似列表 extend），而不是一个覆盖另一个。

---

## 💭 启发式问题

1. 为什么 `messages` 要用 `add_messages` reducer 而不是普通覆盖？如果改成覆盖会发生什么？
2. 如果你自己写一个自定义 reducer（比如"取最大值"），它会在什么场景下有用？
3. `TypedDict(total=False)` 中 `total=False` 的作用是什么？设为 `True` 会怎样？
4. 如果两个节点**同时**修改 `player_hp`（一个 +10，一个 -5），最终结果是多少？LangGraph 的默认行为是什么？
5. State 的这种"全局共享"设计，在多 Agent 协作场景下有什么优势和风险？

---

👉 下一步：[03 · 节点与边](./03-nodes-and-edges.md)

💭 答案：[02-状态管理-答案](./answers/02-state-answers.md)
