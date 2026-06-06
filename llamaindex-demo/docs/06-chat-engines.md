# 💬 LlamaIndex 学习 — 对话引擎与记忆

## 什么是 ChatEngine？

ChatEngine 是有记忆的 QueryEngine。
它能记住之前的对话，处理代词指代（「它」「这个」），
在多轮交互中保持上下文连贯。

ChatEngine 同样支持 DeepSeek——只需在 `.env` 中配置 `DEEPSEEK_API_KEY`。

## 三种对话引擎

### 1. CondenseQuestionChatEngine（推荐）
**原理**：每轮对话时，先把历史 + 新问题「压缩」为一个独立问题，
再用这个独立问题去检索。

```
对话历史: "什么是 RAG？" → "RAG 是..."
新问题: "它有什么优点？"

压缩后: "RAG（检索增强生成）有什么优点？"
→ 检索 → 生成答案
```

**优点**：
- Token 节省（历史被压缩，而非全文携带）
- 检索精准（压缩后的问题是完整语义，不含代词）
- DeepSeek 下成本极低

**代码**：
```python
from config import auto_setup

auto_setup()  # 自动检测 DeepSeek/OpenAI

chat_engine = index.as_chat_engine(
    chat_mode="condense_question",
    verbose=True,
)
```

### 2. ContextChatEngine
**原理**：将检索结果 + 完整对话历史一起发给 LLM。

**优点**：上下文最完整
**缺点**：token 消耗大（历史越来越长），成本逐轮递增

### 3. SimpleChatEngine
**原理**：纯对话，不检索文档。

**适用**：闲聊、不需要知识库的聊天场景。

---

## 对话记忆（ChatMemory）

```python
from llama_index.core.memory import ChatMemoryBuffer

memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

chat_engine = index.as_chat_engine(
    chat_mode="condense_question",
    memory=memory,
    verbose=True,
)
```

**记忆管理策略**：
- `token_limit`：超过限制时，自动丢弃最早的消息
- 也可以用 `ChatSummaryMemoryBuffer`：超限时自动压缩历史
- DeepSeek 128K 上下文足够大多数对话场景

---

## 多轮对话示例

```python
from config import auto_setup
auto_setup()

# 第 1 轮
response = chat_engine.chat("什么是 Python？")
print(response)

# 第 2 轮（代词指代）
response = chat_engine.chat("它有哪些应用领域？")
# ChatEngine 自动知道"它" = "Python"

# 第 3 轮
response = chat_engine.chat("第一个应用领域再详细说说？")

# 重置对话（清空记忆）
chat_engine.reset()
```

---

## ChatEngine vs QueryEngine 对比

| 特性 | QueryEngine | ChatEngine |
|------|------------|------------|
| 对话记忆 | ❌ | ✅ |
| 单轮问答 | ✅ | ✅ |
| 多轮对话 | ❌ | ✅ |
| 代词消解 | ❌ | ✅（condense_question） |
| 适用场景 | 一次性问答 | 客服、助手、多轮对话 |
| DeepSeek 适用 | ✅ | ✅ |

## 💡 成本提示

- CondenseQuestionChatEngine 最省 token（压缩历史，不全文携带）
- DeepSeek 每轮压缩 + 检索 + 生成 ≈ ￥0.003
- ContextChatEngine 每轮成本递增（历史越长 token 越多）
