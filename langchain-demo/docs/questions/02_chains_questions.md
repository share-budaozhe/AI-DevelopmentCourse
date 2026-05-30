# Demo 02 启发性问题 -- Chains

## 基础理解

1. `RunnableParallel` 中的多个分支是真正的并行执行吗?
   在什么条件下是串行的? 如何验证?

2. `RunnablePassthrough.assign()` 和手动构造字典 `{"a": x, "b": y}` 有什么本质区别?
   什么场景下前者明显更好?

3. `itemgetter` 和 `RunnableLambda(lambda d: d["key"])` 功能相同，
   为什么 LangChain 推荐使用 `itemgetter`?

## 深入思考

4. 如果管道中间某个环节失败 (比如 LLM 返回了不符合预期的格式)
   ，LCEL 是如何处理错误的? 有哪些错误恢复策略?

5. 如何在 LCEL 链中实现条件分支 -- 根据中间结果选择不同的下游链?

6. Runnable 的 `.bind()`, `.with_config()`, `.with_retry()`, `.with_fallbacks()`
   分别解决什么问题? 设计一个结合 retry + fallback 的容错链。

## 实战挑战

7. 设计一个"翻译 + 润色 + 字数统计"的三步链，中间环节的输出作为下一环节的输入。
   这与你见过的 `RunnableParallel` 模式有何不同?

8. 如果要在 `RunnablePassthrough.assign()` 中新生成的字段中引用原字段的值
   (比如生成摘要后还想保留原始字数)，应该如何实现?
