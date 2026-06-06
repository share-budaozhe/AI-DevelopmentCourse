# 05 · 工具集成 — 启发式问题答案

---

### Q1: `@tool` 装饰器和普通 `def` 在 LangGraph 中的行为有什么区别？不使用 `@tool` 的函数能否被 `ToolNode` 调用？

**答案**：

区别在于**元数据**。`@tool` 装饰器会：

1. 将函数包装为 `BaseTool` 子类
2. 自动生成 `args_schema`（Pydantic 模型）
3. 提取 `name` 和 `description` 供 LLM 识别

```python
@tool
def roll_dice(sides: int = 20) -> str:
    ...

# tool 对象上的额外属性：
print(roll_dice.name)           # "roll_dice"
print(roll_dice.description)    # "🎲 掷骰子，返回结果。"
print(roll_dice.args_schema)    # Pydantic 模型 {sides: int}
```

不经 `@tool` 的函数**不能被 `ToolNode` 直接使用**，因为 `ToolNode` 期望 `BaseTool` 实例。但你可以：

```python
from langchain_core.tools import tool

# 方案1：手动包装
my_func = tool(my_func)

# 方案2：用 StructuredTool
from langchain_core.tools import StructuredTool
my_func = StructuredTool.from_function(func=my_func, name="my_func", ...)
```

---

### Q2: 如果工具执行失败（比如抛异常），LangGraph 会如何处理？你需要在哪里加错误处理？

**答案**：

默认情况下，工具执行失败会**向上传播异常，中止图执行**。

**处理方案**：

```python
@tool
def roll_dice(sides: int = 20) -> str:
    if sides <= 0:
        return "❌ 错误：骰子面数必须大于 0"
    try:
        result = random.randint(1, sides)
    except Exception as e:
        return f"❌ 工具执行失败: {str(e)}"
    return f"🎲 D{sides}: {result}"
```

或者用包装器：

```python
from functools import wraps

def safe_tool(func):
    """包装 @tool 函数，自动捕获异常"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return f"❌ 工具 '{func.__name__}' 执行失败: {str(e)}"
    return wrapper
```

**最佳实践**：
- 工具内部处理已知异常，返回错误消息（不是抛异常）
- 未知异常向上传播，让图级错误处理节点处理
- 可以添加一个 `error_handler` 节点来捕获所有工具异常

---

### Q3: 在一个 Agent 图中有 10 个工具时，LLM 如何选择调用哪个？提示工程在其中扮演什么角色？

**答案**：

LLM 通过**工具描述**（docstring）来选择：

```python
@tool
def roll_dice(sides: int = 20, times: int = 1) -> str:
    """🎲 掷骰子，用于战斗攻击判定和随机事件。返回掷骰结果。"""
```

LLM 会收到类似这样的 system prompt：

```
You have access to the following tools:
- roll_dice: 🎲 掷骰子，用于战斗攻击判定和随机事件...
- calculate_damage: ⚔️ 计算战斗伤害...
- use_item: 🧪 使用背包中的物品...
- check_inventory: 🎒 查看背包内容...
```

**提示工程的角色**：
- 工具描述是 LLM 的"菜单"——写得越清晰，选择越准确
- 在 system prompt 中可以加选择指引：*"当用户提到战斗时，优先用 roll_dice 和 calculate_damage"*
- 工具名本身也是信号：`search_weather` 比 `tool_1` 好 100 倍
- 提供工具使用的示例可以大幅提升准确率（few-shot prompting）

---

### Q4: 工具的 docstring 有多重要？如果 `roll_dice` 的 docstring 写得很模糊，LLM 可能做出什么错误判断？

**答案**：

**Docstring 是 LLM 选择工具的"唯一说明书"**。如果写得很模糊：

```python
# ❌ 模糊的 docstring
@tool
def roll_dice(sides: int) -> str:
    """Rolls."""
```

LLM 可能：
- 不知道什么时候该用它
- 错误地用 `calculate_damage` 代替
- 传错误的参数（不知道 `sides` 是面数）
- 在不需要骰子的场景也调用它（"我要开宝箱"→ 掷骰子？）

**好的 docstring 公式**：
```
[Emoji] [一句话概述]。[使用场景]。[参数说明]。[返回值说明]。[注意事项]
```

```python
@tool
def roll_dice(sides: int = 20, times: int = 1) -> str:
    """🎲 掷骰子，用于战斗攻击判定和随机事件。
    当需要随机数时调用此工具，如攻击命中判定、伤害浮动。
    sides: 骰子面数（默认D20），times: 掷几次。
    返回掷骰结果的描述字符串。
    注意：不应用于非随机计算。"""
```

---

### Q5: 假如你想让工具之间相互调用，这在 LangGraph 中是好做法吗？

**答案**：

**不推荐工具直接相互调用**。原因：

1. **破坏图的可追溯性**：调用链 `tool_a → tool_b` 在图层面不可见
2. **检查点丢失**：`tool_b` 的中间状态不会保存
3. **循环风险**：`tool_a → tool_b → tool_a` 死循环

**推荐做法**：让图来控制工具调用顺序：

```python
# 图中定义清晰的调用顺序
graph.add_node("tool_a", ToolNode([tool_a]))
graph.add_node("tool_b", ToolNode([tool_b]))
graph.add_edge("tool_a", "tool_b")  # 显式边
```

如果你确实需要工具组合，使用**工具链（Tool Chain）**：

```python
@tool
def attack_with_weapon(weapon: str, target: str) -> str:
    """攻击目标。内部使用 roll_dice + calculate_damage。"""
    dice_result = random.randint(1, 20)
    damage = calculate_damage_inline(weapon, dice_result)  # 直接调用普通函数
    return f"用{weapon}攻击{target}，造成{damage}点伤害"
```

关键是：工具内部调用**普通函数**（不是 `@tool` 函数），让图管理工具间的调度。
