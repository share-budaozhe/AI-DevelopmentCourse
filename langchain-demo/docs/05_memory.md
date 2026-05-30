# Demo 05 -- Memory: 对话记忆管理

## 目标

理解如何在多轮对话中保持上下文，以及多会话隔离的实现方式。

## 涉及文件

- [demo_05_memory.py](../demos/demo_05_memory.py)

## 知识点

### 1. RunnableWithMessageHistory

```python
from langchain_core.runnables.history import RunnableWithMessageHistory

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,        # 历史记录获取函数
    input_messages_key="input",  # 新输入的 key
    history_messages_key="history", # 历史消息的 key
)
```

`RunnableWithMessageHistory` 是一个包装器，它:
1. 调用前: 从 `get_session_history(session_id)` 加载历史
2. 注入 Prompt: 将历史消息填入 `MessagesPlaceholder`
3. 调用后: 将本次对话追加到历史中

### 2. ChatMessageHistory

```python
from langchain_core.chat_history import InMemoryChatMessageHistory

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
```

`InMemoryChatMessageHistory` 在内存中存储消息列表。
生产环境可替换为 `RedisChatMessageHistory` 或数据库持久化。

### 3. MessagesPlaceholder

```python
from langchain_core.prompts import MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的助手。"),
    MessagesPlaceholder(variable_name="history"),  # 历史消息插入点
    ("human", "{input}"),
])
```

`MessagesPlaceholder` 在 Prompt 中预留一个位置，运行时由 `RunnableWithMessageHistory`
自动填入历史消息列表。

### 4. 多会话隔离

```python
# 会话 A
chain.invoke({"input": "我叫 Alice"}, config={"configurable": {"session_id": "session_a"}})

# 会话 B (完全独立的上下文)
chain.invoke({"input": "我叫 Bob"}, config={"configurable": {"session_id": "session_b"}})

# 回到会话 A -- 记得 Alice
chain.invoke({"input": "还记得我叫什么吗?"}, config={"configurable": {"session_id": "session_a"}})
```

通过 `session_id` 区分不同用户的对话，历史互不干扰。
`configurable` 字典是 LangChain 传递运行时配置的标准方式。

## 设计要点

- `get_session_history` 使用惰性创建，首次访问时才创建历史对象
- `store` 字典在模块级别，生产环境应使用 Redis/数据库
- `HumanMessage` vs `AIMessage` 可用于区分对话角色
