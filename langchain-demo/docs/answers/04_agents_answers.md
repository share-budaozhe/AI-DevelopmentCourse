# Demo 04 参考答案 -- Agents

## 1. Agent vs Chain 的本质区别

| 维度 | Chain | Agent |
|------|-------|-------|
| 执行路径 | 预定义、固定 | 动态、LLM 自主决定 |
| 工具调用 | 无 (或手动编排) | LLM 自主选择 |
| 适用场景 | 确定性流程 | 开放式、需要决策的任务 |
| 复杂度 | 低 | 高 |
| 成本 | 低 (1 次 LLM 调用) | 高 (多次 LLM 调用) |
| 可靠性 | 高 | 中等 (可能选错工具) |

规则: 能用 Chain 解决的问题不要用 Agent。

## 2. ReAct vs Function Calling

ReAct 是一种**prompt 策略**: LLM 生成 "Thought: ... Action: ... Observation: ..."
格式的文本，Agent 框架解析后执行。
Function Calling 是 OpenAI 的**原生 API 能力**: 客户端定义 function schema，
模型返回结构化的 `tool_calls`。

LangGraph 的 `create_react_agent` 底层使用 Function Calling:
```python
# 内部等价于:
llm_with_tools = llm.bind_tools(tools)
```

使用 Function Calling 比纯文本 ReAct 更可靠，因为工具调用是结构化的 JSON。

## 3. Tool docstring 如何被使用

Agent 创建时，会将所有 Tool 的 **name + description + 参数 schema** 发送给 LLM。
LLM 根据这些信息判断何时调用哪个工具。

```python
# 发送给 LLM 的信息类似:
# Tool: calculator
# Description: 执行数学计算。输入如 '2 + 3 * 4'
# Parameters: expression (string)
```

这就是为什么 docstring 必须清晰准确 -- 它是 LLM 选择工具的唯一依据。

## 4. 无限循环与限制

LangGraph 的 `create_react_agent` 默认最大迭代 25 步。
可通过 `recursion_limit` 配置:

```python
agent = create_react_agent(model=llm, tools=tools)
result = agent.invoke(
    {"messages": [("user", q)]},
    config={"recursion_limit": 5}  # 最多 5 轮
)
```

也可在创建时全局设置。

## 5. 共享 Context Window 的问题

是的，ReAct 循环中所有 Thought/Observation 都会累积在 context window 中。
问题:
- Token 消耗快速增长
- "Lost in the Middle" 效应: 早期的观察结果可能被忽略
- 成本高: 每步都要重新发送完整的对话历史

解决方案: 滑动窗口式管理历史，对早期步骤做摘要。

## 6. Agent 的幻觉

Agent 的幻觉有特殊形式:
- **工具幻觉**: LLM 声称调用了不存在的工具 (常见于 ReAct 文本模式)
- **结果幻觉**: LLM 编造工具返回的结果
- **循环幻觉**: 在相同问题上反复调用工具，期望不同结果

Function Calling 模式大幅减少了工具幻觉，因为工具调用是结构化的。

## 7. SQL 查询工具

```python
@tool
def sql_query(query: str) -> str:
    # 在数据库中执行 SQL 查询。仅支持 SELECT 语句。
    if not query.strip().upper().startswith("SELECT"):
        return "仅支持 SELECT 查询"
    try:
        conn = get_db_connection()
        result = conn.execute(query).fetchmany(50)
        if len(result) >= 50:
            return str(result) + "\n(结果已截断，共 50 行)"
        return str(result)
    except Exception as e:
        return f"查询出错: {e}"
```

关键安全措施: 限制为只读查询、限制返回行数、使用只读数据库用户。

## 8. 工具优先级引导

```python
# 方式一: tool 名称中加入暗示
@tool
def calculator_preferred(expr: str) -> str:
    # 首选计算工具...
    ...

# 方式二: system prompt 中明确指示
system_msg = "进行计算时，优先使用 calculator，不要使用 wolfram_alpha"
```

## 9. Agent 层面的自动重试

```python
# Chain 层面: 对单个 LLM 调用重试
chain.with_retry(stop_after_attempt=3)

# Agent 层面: 在 Python 代码中包裹整个 invoke
for attempt in range(3):
    try:
        result = agent.invoke({"messages": [("user", q)]})
        if "出错" not in result["messages"][-1].content:
            break
    except Exception:
        if attempt == 2: raise
```

区别: Chain 重试是同一个输入重试多次，Agent 重试可以修改输入/策略。
