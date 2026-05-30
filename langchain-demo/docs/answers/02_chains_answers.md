# Demo 02 参考答案 -- Chains

## 1. RunnableParallel 是否真正并行

**取决于上下文:**

- 如果每个分支调用不同的 API (如两个 LLM 调用): 因为 LLM 调用是 I/O 密集的，
  LangChain 通过 asyncio 异步执行，可以达到接近并行的效果
- 如果分支是纯 CPU 计算 (如 RunnableLambda): Python GIL 限制下实际是串行的
- LCEL 的 `RunnableParallel` 内部使用 `asyncio.gather()` 调度

验证方法: 在两个分支中分别加入 `time.sleep(2)` 和 `time.sleep(1)`，
如果总耗时约 2 秒而非 3 秒，说明是并行的。

## 2. RunnablePassthrough.assign() vs 手动构造字典

关键区别: **不丢失原始字段**。

```python
# RunnablePassthrough.assign(): 保留原始字段
result = RunnablePassthrough.assign(new_field=some_chain).invoke({"a": 1, "b": 2})
# result == {"a": 1, "b": 2, "new_field": ...}

# 手动构造: 丢失了 b
chain = {"a": itemgetter("a"), "new_field": some_chain} | ...
# result == {"a": 1, "new_field": ...}  # b 丢了!
```

## 3. 为什么推荐 itemgetter

- `itemgetter` 是 C 实现的，比 `RunnableLambda` 快 (不需要 Python 函数调用开销)
- 语义更清晰: 一眼就看出是字段提取
- 支持多字段: `itemgetter("a", "b")` 返回元组

## 4. LCEL 错误处理

```python
# 方式一: with_fallbacks - 失败时切换到备用链
chain = primary_chain.with_fallbacks([fallback_chain])

# 方式二: with_retry - 自动重试
chain = chain.with_retry(stop_after_attempt=3)

# 方式三: 自定义错误处理
from langchain_core.runnables import RunnableLambda

def safe_chain(input):
    try:
        return original_chain.invoke(input)
    except Exception:
        return "抱歉，处理出错了"

wrapped = RunnableLambda(safe_chain)
```

## 5. LCEL 中的条件分支

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: x["lang"] == "zh", chinese_chain),
    (lambda x: x["lang"] == "en", english_chain),
    default_chain  # 默认分支
)
```

`RunnableBranch` 依次检查条件，第一个为 True 的分支被执行。

## 6. bind / with_config / with_retry / with_fallbacks

```python
chain = (
    prompt
    | llm.bind(temperature=0, max_tokens=500)  # 固定参数
    | parser
    .with_config({"run_name": "my_chain"})      # 运行配置
    .with_retry(stop_after_attempt=2)           # 重试
    .with_fallbacks([simple_chain])             # 降级
)
```

## 7. 三步串行链

```python
# 这不是 RunnableParallel，而是顺序依赖
chain = (
    translate_chain                     # 翻译
    | (lambda x: {"text": x, "style": "formal"})
    | polish_chain                      # 润色
    | RunnableLambda(lambda x: f"共 {len(x)} 字")  # 统计
)
```

与 RunnableParallel 的本质区别: **串行有数据依赖，并行无依赖。**

## 8. 在 assign 的新字段中引用原字段

```python
chain = RunnablePassthrough.assign(
    word_count=RunnableLambda(lambda d: len(d["text"])),
    summary=prompt | llm | StrOutputParser(),
)
```

因为 `RunnablePassthrough` 会将原始字典传递给每个 assign 分支，
Lambda 中可以通过 `lambda d:` 访问完整字典。
