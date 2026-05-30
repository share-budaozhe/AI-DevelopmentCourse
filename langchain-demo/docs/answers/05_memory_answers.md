# Demo 05 参考答案 -- Memory

## 1. 历史记录的注入机制

`RunnableWithMessageHistory.invoke()` 的执行流程:

```python
1. 从 config 中提取 session_id
2. 调用 get_session_history(session_id) 获取历史对象
3. 将历史对象中的消息列表填入 prompt 的 "history" 位置
4. 调用底层 chain.invoke({"input": ..., "history": [...]})
5. 将新的 HumanMessage 和 AIMessage 追加到历史对象中
```

整个过程是**同步**的 -- `get_session_history` 必须是同步函数。

## 2. 控制历史长度

LangChain 提供了多种 Memory 类型:

- `ConversationBufferMemory`: 保留全部历史 (无限制)
- `ConversationBufferWindowMemory(size=k)`: 只保留最近 k 轮
- `ConversationSummaryMemory`: 对早期对话做摘要，保留 token 数可控
- `ConversationSummaryBufferMemory`: 摘要 + 窗口的混合

```python
# 窗口记忆: 只保留最近 4 条消息
from langchain.memory import ConversationBufferWindowMemory
memory = ConversationBufferWindowMemory(k=4)
```

## 3. MessagesPlaceholder vs 手动拼接 {history}

`MessagesPlaceholder` 的优势:
- **类型安全**: 自动将 Message 对象序列化为正确的格式
- **角色感知**: HumanMessage/AIMessage/SystemMessage 的格式不同
- **框架集成**: `RunnableWithMessageHistory` 自动填充

手动拼接 `{history}` 的问题:
- 需要自己格式化消息列表为字符串
- 不同 LLM 的 message 格式不同 (OpenAI vs Anthropic)
- 容易丢失角色信息

## 4. PostgreSQL 持久化

```sql
CREATE TABLE chat_history (
    session_id VARCHAR(255) NOT NULL,
    message_index INT NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'human' | 'ai' | 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (session_id, message_index)
);
CREATE INDEX idx_session ON chat_history(session_id);
```

需要实现的方法:
- `add_message(message)`: INSERT 新消息
- `clear()`: DELETE WHERE session_id = ?
- `messages` 属性: SELECT ... ORDER BY message_index

## 5. 多用户并发

`store = {}` 的问题:
- 进程重启后数据丢失
- 多进程部署时数据不共享
- 没有并发控制

线程安全 + 水平扩展方案:
- **Redis**: 单线程模型天然线程安全，支持集群
- **PostgreSQL**: 连接池 + 事务
- **专用方案**: LangChain 的 `RedisChatMessageHistory`

```python
from langchain_community.chat_message_histories import RedisChatMessageHistory
```

## 6. Summary vs Window 的对比

| 特性 | SummaryMemory | WindowMemory |
|------|--------------|--------------|
| 信息密度 | 高 (压缩) | 低 (原始) |
| 细节保留 | 可能丢失 | 完整保留 |
| Token 控制 | 精确 (固定摘要长度) | 粗略 (固定轮数) |
| 额外成本 | 需要额外 LLM 调用做摘要 | 无 |

结合方案: `ConversationSummaryBufferMemory` -- 保留最近 K 轮原始对话，
更早的对话压缩为摘要。

## 7. 记忆压缩策略

```python
MAX_TOKENS = 4000
RECENT_ROUNDS = 3

def compress_memory(history: list):
    if estimate_tokens(history) <= MAX_TOKENS:
        return history
    # 保留最近 3 轮
    recent = history[-RECENT_ROUNDS * 2:]  # 每轮 = human + ai
    old = history[:-RECENT_ROUNDS * 2]
    # 用 LLM 对早期对话生成摘要
    summary = llm.invoke(f"请用 100 字以内总结以下对话:\n{old}")
    return [SystemMessage(f"对话摘要: {summary}")] + recent
```

## 8. 跨设备会话持久化

需要:
1. **服务端存储**: 使用 Redis/PostgreSQL 而非内存
2. **会话标识**: 用用户 ID (而非设备 ID) 作为 session_id
3. **认证机制**: JWT token 或 OAuth 确保用户身份一致性

```python
# session_id = f"{user_id}:{conversation_id}" 而不是设备 ID
chain.invoke(
    {"input": "..."},
    config={"configurable": {"session_id": f"user_123:conv_456"}}
)
```
