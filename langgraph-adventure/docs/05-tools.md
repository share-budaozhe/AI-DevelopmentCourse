# 05 · 工具集成：给 Agent 装上"手和脚"

## 🧠 一句话总结

工具（Tools）是 Agent 与外部世界交互的接口。LangGraph 中的工具通过 `@tool` 装饰器定义，可以被 Agent 节点调用。

---

## 🔧 我们的工具定义

打开 `src/tools.py`，我们定义了 4 个工具：

```python
from langchain_core.tools import tool

@tool
def roll_dice(sides: int = 20, times: int = 1) -> str:
    """🎲 掷骰子，返回结果。"""
    results = [random.randint(1, sides) for _ in range(times)]
    total = sum(results)
    return f"🎲 D{sides}: {results} 总和 = {total}"

@tool
def calculate_damage(base_attack: int, dice_result: int,
                     has_advantage: bool = False) -> str:
    """⚔️ 计算战斗伤害。"""
    ...

@tool
def use_item(item_name: str, inventory: List[str]) -> str:
    """🧪 使用背包中的物品。"""
    ...

@tool
def check_inventory(inventory: List[str]) -> str:
    """🎒 查看背包内容。"""
    ...
```

---

## 🎯 `@tool` 装饰器做了什么？

```python
@tool
def roll_dice(sides: int = 20, times: int = 1) -> str:
    """🎲 掷骰子，返回结果。"""
```

这个装饰器自动做了几件事：

1. **提取函数签名**：参数名、类型、默认值
2. **提取 docstring**：作为工具的描述（LLM 会读到）
3. **包装为 Tool 对象**：可以被 `ToolNode` 调用
4. **生成 JSON Schema**：供 LLM Function Calling 使用

---

## 🔗 ToolNode：批量执行工具

```python
from langgraph.prebuilt import ToolNode

ALL_TOOLS = [roll_dice, calculate_damage, use_item, check_inventory]
tool_node = ToolNode(ALL_TOOLS)
graph.add_node("tools", tool_node)
```

`ToolNode` 会：
1. 读取 state 中 LLM 产生的 tool_calls
2. 并行/串行调用对应的工具函数
3. 将工具返回结果写入 state

---

## 🧪 在我们的 Demo 中的工具使用

虽然我们的 Demo 主要用纯节点函数实现游戏逻辑（因为游戏规则是确定性的），但工具在 LangGraph 中的典型用法是：

```
用户输入 → Agent 节点（LLM 决策）
              ↓
         需要调用工具？
         ↙        ↘
       是            否
       ↓             ↓
   ToolNode       直接回复
       ↓
   工具结果
       ↓
   Agent 节点（LLM 整合结果）
       ↓
   最终回复给用户
```

在我们的游戏中，假如你接入了 LLM，`roll_dice` 和 `calculate_damage` 就会由 LLM 自动判断何时调用：

```
玩家：「我要攻击地精！」
LLM：  "这是个战斗动作，我需要 roll_dice(D20)"
        → 调用工具 roll_dice(20)
        → 得到结果：15
        → "好的一掷！接下来计算伤害..."
        → 调用工具 calculate_damage(5, 15)
        → "造成了 7 点伤害！地精反击..."
```

---

## 🎮 工具 vs 直接调用函数

| 维度 | 直接调用 | 通过 Tool |
|------|---------|-----------|
| 调用者 | 代码中明确写 | LLM 自主决定 |
| 时机 | 编译时确定 | 运行时动态 |
| 灵活性 | 低 | 高 |
| 可观测性 | 日志 | Tool 调用记录在 state 中 |
| 适用场景 | 确定性逻辑 | 需要 LLM 判断的场景 |

---

## 💭 启发式问题

1. `@tool` 装饰器和普通 `def` 在 LangGraph 中的行为有什么区别？不使用 `@tool` 的函数能否被 `ToolNode` 调用？
2. 如果工具执行失败（比如抛异常），LangGraph 会如何处理？你需要在哪里加错误处理？
3. 在一个 Agent 图中有 10 个工具时，LLM 如何选择调用哪个？提示工程在其中扮演什么角色？
4. 工具的 docstring 有多重要？如果 `roll_dice` 的 docstring 写得很模糊，LLM 可能做出什么错误判断？
5. 假如你想让工具之间相互调用（比如 `use_item` 内部调用 `roll_dice`），这在 LangGraph 中是好做法吗？

---

👉 下一步：[06 · Human-in-the-Loop](./06-human-in-loop.md)

💭 答案：[05-工具-答案](./answers/05-tools-answers.md)
