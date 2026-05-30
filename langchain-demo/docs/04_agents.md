# Demo 04 -- Agents: 智能体与工具调用

## 目标

理解 Agent 的工作原理: LLM 如何自主决策、调用工具、完成复杂任务。

## 涉及文件

- [demo_04_agents.py](../demos/demo_04_agents.py)

## 知识点

### 1. Tool 的定义

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    # 执行数学计算。输入如 '2 + 3 * 4'。
    ...

@tool
def word_length(word: str) -> str:
    # 返回一个词的字符数。
    ...
```

`@tool` 装饰器将普通函数注册为 LangChain Tool。
函数的 **docstring** 非常重要 -- Agent 靠它来判断何时使用哪个工具。

### 2. ReAct Agent

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model=llm, tools=tools)
result = agent.invoke({"messages": [("user", "计算 (3+5)*7")]})
```

LangGraph 的 `create_react_agent` 实现了 ReAct (Reasoning + Acting) 模式:

```
用户提问 -> LLM 推理 -> 决定调用工具 -> 工具执行 -> 观察结果 -> LLM 再推理 -> ... -> 最终回答
```

### 3. result["messages"] 的结构

```python
result = agent.invoke({"messages": [("user", q)]})
# result["messages"] 包含完整轨迹:
# [HumanMessage, AIMessage(tool_calls=[...]), ToolMessage(...), AIMessage(content="最终回答")]
```

最后一条 `AIMessage` 的 `content` 是最终答案。
中间的 `ToolMessage` 记录了每次工具调用的输入和输出。

### 4. 多工具协同

Agent 可以连续调用多个工具来完成一个任务:

```
Q: "把 'Hello World' 反转，然后告诉我反转后的字符串有多长"
-> Agent 调用 reverse_string("Hello World") -> "dlroW olleH"
-> Agent 调用 word_length("dlroW olleH") -> 11
-> 最终回答: "反转后是 dlroW olleH，共 11 个字符"
```

## 设计要点

- Tool 的 docstring 决定了 Agent 能否正确选择工具，必须描述清楚功能和参数
- Agent 不保证一定调用工具 -- 如果 LLM 认为可以直接回答，会跳过工具调用
- 使用安全的 eval 命名空间 (空 `__builtins__`) 防止代码注入
