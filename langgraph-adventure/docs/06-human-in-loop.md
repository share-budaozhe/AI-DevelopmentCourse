# 06 · Human-in-the-Loop：让人参与决策

## 🧠 一句话总结

Human-in-the-Loop (HITL) 是 LangGraph 让**人类在 Agent 执行过程中介入**的机制。通过 `interrupt()` 暂停图执行，等待外部输入后恢复。

---

## 🎮 在我们的 Demo 中

这是整个游戏最核心的交互模式。打开 `src/graph.py`：

```python
def wait_for_input(state: GameState) -> dict:
    """⏸️ 暂停节点 —— 等待玩家输入。"""
    user_input = interrupt("请选择你的动作：")
    return {
        "messages": [("user", user_input)],
        "pending_decision": False,
    }
```

而在 `src/main.py` 的主循环中：

```python
# 1️⃣ 首次 invoke：图运行到 interrupt() 暂停
current_state = app.invoke(INITIAL_STATE, config)

while True:
    # 2️⃣ 显示图暂停位置的输出
    for msg in current_state.get("messages", []):
        print_message(msg)

    # 3️⃣ 获取用户输入
    user_input = input("> ")

    # 4️⃣ 恢复执行：传入用户输入
    current_state = app.invoke(
        Command(resume=user_input),    # 👈 这就是"恢复"
        config,
    )
```

---

## 🔄 完整流程

```
        ┌──────────────────────────────────────────────────┐
        │                 LangGraph 图内部                   │
        │                                                    │
        │  enter_room → route → ... → wait_for_input         │
        │                                     │               │
        │                              interrupt("请选择")     │
        │                                     │               │
        └─────────────────────────────────────┼───────────────┘
                                              │ 图暂停
        ══════════════════════════════════════╪═══════════════
                                              │ 外部世界
        ┌─────────────────────────────────────┼──────────────┐
        │            main.py 主循环            │               │
        │                                      ▼               │
        │         显示消息（图暂停位置的输出）                  │
        │         等待用户输入：input("> ")                    │
        │         用户输入 "北"                                │
        │         Command(resume="北")                        │
        │                        │                            │
        └────────────────────────┼────────────────────────────┘
                                 │
        ══════════════════════════╪════════════════════════════
                                 │ 恢复执行
        ┌────────────────────────┼────────────────────────────┐
        │                 LangGraph 图内部                     │
        │                        ▼                             │
        │         user_input = "北" (interrupt 的返回值)       │
        │         → route → move_player → enter_room           │
        │                          │                           │
        │                   interrupt("请选择...")  ← 再次暂停  │
        └──────────────────────────┼───────────────────────────┘
                                   │
                              循环往复...
```

---

## 🧩 `Command(resume=...)` 详解

```python
from langgraph.types import Command

# 恢复执行，interrupt() 返回 "北"
app.invoke(Command(resume="北"), config)

# 除了 resume，Command 还可以同时更新 state：
app.invoke(Command(resume="北", update={"player_hp": 50}), config)
```

`Command` 是一个多用途指令：
- `resume`：传给 `interrupt()` 的返回值
- `update`：在恢复前直接修改 state
- `goto`：跳转到指定节点（高级用法）

---

## 🆚 对比：有 HITL vs 无 HITL

```
无 HITL：                         有 HITL：
                                  
  图开始                            图开始
    ↓                                 ↓
  Agent 决策                        Agent 分析
    ↓                                 ↓
  调用工具                          interrupt() 暂停
    ↓                                 ↓
  Agent 回复                      👤 人类审核
    ↓                                 ↓
  图结束                          批准/拒绝/修改
                                      ↓
                                  继续执行
                                      ↓
                                   图结束
```

---

## 🎯 实际应用场景

| 场景 | 暂停点 |
|------|--------|
| 审批流程 | 关键决策前等待批准 |
| 客服机器人 | 遇到无法回答的问题时转人工 |
| 代码审查 | AI 生成代码后等待人类审查 |
| 数据标注 | AI 标注后人工抽查确认 |
| 敏感操作 | 删除/支付前等待确认 |

---

## 💭 启发式问题

1. `interrupt()` 返回后，图是如何知道"从哪里继续"的？背后的机制是什么？
2. 如果 `interrupt()` 暂停后，外部程序没有调用 `Command(resume=...)` 而是重新 `invoke()`，会发生什么？
3. 如何在一次 `invoke` 中实现多次暂停？（提示：`interrupt()` 可以在图中多处使用）
4. `Command` 的 `update` 参数允许在恢复时直接修改 state。这在什么场景下有用？有什么风险？
5. 在人机交互模式下，如果用户输入了一个无效命令，你应该在 `main.py` 中过滤还是在图内部处理？为什么？

---

👉 下一步：[07 · 检查点与持久化](./07-checkpoints.md)

💭 答案：[06-Human-in-the-Loop-答案](./answers/06-human-answers.md)
