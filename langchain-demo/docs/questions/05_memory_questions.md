# Demo 05 启发性问题 -- Memory

## 基础理解

1. `RunnableWithMessageHistory` 在每次调用时是如何"注入"历史记录的?
   历史的存储和加载是同步还是异步的?

2. 如果用户连续发送 100 轮对话，Prompt 中的历史记录会变得非常长。
   LangChain 提供了哪些机制来控制历史长度?

3. `MessagesPlaceholder` 和手动在 Prompt 模板中拼接 `{history}`
   有什么区别? 为什么推荐使用前者?

## 深入思考

4. `BaseChatMessageHistory` 是一个抽象基类。如果要用 PostgreSQL
   存储对话历史，需要实现哪些方法? 数据表应该如何设计?

5. 在多用户并发场景下，`store = {}` (内存字典) 有什么问题?
   如何设计一个线程安全的、支持水平扩展的会话存储?

6. 对话摘要 (ConversationSummaryMemory) 和 滑动窗口 (ConversationBufferWindowMemory)
   各有什么优缺点? 能否结合使用?

## 实战挑战

7. 设计一个 "记忆压缩" 策略: 当对话历史超过 token 上限时，
   自动对早期对话进行摘要，保留最近 N 轮的完整记录。

8. 如何实现跨设备的会话持久化?
   用户从手机切换到电脑后，能否继续之前的对话?
