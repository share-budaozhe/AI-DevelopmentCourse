# 06 · Human-in-the-Loop — 启发式问题答案

---

### Q1: `interrupt()` 返回后，图是如何知道"从哪里继续"的？背后的机制是什么？

**答案**：

`interrupt()` 内部使用了**检查点（Checkpoint）机制**：

1. 调用 `interrupt()` 时，LangGraph 保存当前检查点，标记当前节点为"等待恢复"
2. 检查点记录了：`next=("wait_for_input",)` —— 恢复后从哪个节点继续
3. 外部程序调用 `Command(resume=value)` 时：
   - LangGraph 读取最新检查点
   - 从记录的 `next` 节点恢复执行
   - 将 `resume` 的值作为 `interrupt()` 的返回值

```python
# 背后的伪代码
def interrupt(prompt):
    save_checkpoint(state, next_node=current_node)
    raise InterruptException(prompt)  # 暂停

# 外部恢复时
def invoke(Command(resume=value), config):
    checkpoint = load_checkpoint(config)
    restore_state(checkpoint)
    return checkpoint.next_node(state)  # 从中断点继续
    # 此时 interrupt() 返回 value
```

这就是为什么**必须用同一个 `thread_id`** —— 否则找不到正确的检查点。

---

### Q2: 如果 `interrupt()` 暂停后，外部程序没有调用 `Command(resume=...)` 而是重新 `invoke()`，会发生什么？

**答案**：

如果重新 `invoke(initial_state, config)`：

```python
# 使用相同 thread_id 和相同初始状态
app.invoke(INITIAL_STATE, config)
```

结果取决于 LangGraph 版本和配置：

**通常会**：从最新检查点恢复，而不是重新开始。图会直接跳到 `wait_for_input` 节点，卡在 `interrupt()` 等待。

**如果想重新开始**，必须使用**新的 `thread_id`**：
```python
new_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
app.invoke(INITIAL_STATE, new_config)  # 全新开局
```

**或者清除检查点**（需要 access checkpointer 的 API）。

---

### Q3: 如何在一次 `invoke` 中实现多次暂停？

**答案**：

简单：在图中多个位置放置 `interrupt()`：

```python
def review_purchase(state):
    """第一步：确认金额"""
    amount = interrupt(f"确认购买金额: {state['amount']} 元？")
    return {"confirmed_amount": amount}

def review_shipping(state):
    """第二步：确认地址"""
    address = interrupt(f"确认收货地址: {state['address']}？")
    return {"confirmed_address": address}

# 图结构
graph.add_node("review_amount", review_purchase)
graph.add_node("review_address", review_shipping)
graph.add_edge("review_amount", "review_address")
```

外部循环：
```python
while True:
    try:
        # 图会运行到下一个 interrupt() 暂停
        state = app.invoke(state, config)
    except GraphInterrupt:
        user_input = input("> ")
        state = app.invoke(Command(resume=user_input), config)
```

还可以用 **`interrupt_after`/`interrupt_before`**（编译时配置）来在每个节点前后自动暂停。

---

### Q4: `Command` 的 `update` 参数允许在恢复时直接修改 state。这在什么场景下有用？有什么风险？

**答案**：

**有用场景**：
- **管理员强制修改**：管理员审核时修改 Agent 的决策参数
- **用户纠错**：用户发现 Agent 误解了意图，直接注入正确的 state
- **回退**：恢复到某个历史检查点的状态

```python
# 管理员：强制降低扣款金额
app.invoke(Command(
    resume="approved",
    update={"amount": 100, "admin_note": "价格有误，调整为100"}
), config)
```

**风险**：
- **绕过业务逻辑**：`update` 直接修改 state，不经过节点的验证逻辑
- **状态不一致**：可能改了一个字段但依赖它的其他字段没更新
- **调试困难**：状态变更的来源难以追踪
- **安全风险**：外部输入直接注入 state，可能被恶意利用

**最佳实践**：仅在明确需要外部覆盖时使用，加审计日志。

---

### Q5: 在人机交互模式下，如果用户输入了一个无效命令，应该在 `main.py` 中过滤还是在图内部处理？为什么？

**答案**：

**两者配合使用**，但各有侧重：

**在 `main.py` 中（外部层）**：
- 处理系统级命令（退出、帮助、存档）
- 快速输入校验（空输入、明显无效）
- UI 层面的提示

**在图内部（`_route_user_input`）**：
- 处理业务逻辑的无效输入
- 返回有意义的错误消息
- 决定是重试还是 fallback

```python
# main.py：UI 层过滤
if not user_input.strip():
    print("请输入有效命令")
    continue

# graph.py：业务层处理
def _route_user_input(state):
    user_input = get_last_user_input(state)
    if user_input not in VALID_COMMANDS:
        return "unknown_command"  # 图内处理
```

**为什么不在外部全部过滤**：
- 外部不知道图的当前上下文（战斗中？解谜中？）
- 业务规则在图中维护，保持单一真源
- 图可能需要根据状态给出不同的错误提示

**推荐的分层**：
```
用户输入 → main.py (基础校验/系统命令) → Command(resume) → graph (业务路由/错误处理)
```
