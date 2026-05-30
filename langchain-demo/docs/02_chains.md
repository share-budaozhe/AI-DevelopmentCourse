# Demo 02 -- Chains: LCEL 链式编排

## 目标

掌握 LCEL 的核心 Runnable 类型及其组合方式。

## 涉及文件

- [demo_02_chains.py](../demos/demo_02_chains.py)

## 知识点

### 1. RunnableParallel -- 并行执行

```python
parallel_chain = RunnableParallel(joke=joke_chain, fact=fact_chain)
result = parallel_chain.invoke({"topic": "编程"})
# result: {"joke": "...", "fact": "..."}
```

多个子链共享同一输入，并行执行 (实际并行度取决于后端)。
输出是一个字典，key 为分支名。

### 2. RunnablePassthrough -- 透传增强

```python
chain = RunnablePassthrough.assign(
    summary=prompt | llm | StrOutputParser()
)

result = chain.invoke({"text": "...", "style": "一句话"})
# result: {"text": "...", "style": "一句话", "summary": "新生成的字段"}
```

`.assign()` 在原字典基础上追加新字段，不修改原有字段。
非常适合 "输入 + LLM处理结果" 的模式。

### 3. itemgetter -- 字段提取

```python
chain = (
    {"word": itemgetter("word"), "target_lang": itemgetter("target_lang")}
    | prompt | llm | StrOutputParser()
)
result = chain.invoke({"word": "ML", "target_lang": "中文", "extra": "ignored"})
```

`itemgetter` 从输入字典中提取指定字段，忽略多余的键。
等价于 `RunnableLambda(lambda d: {"word": d["word"]})`。来自 Python 标准库 `operator`。

### 4. RunnableLambda -- 自定义逻辑

```python
chain = RunnableLambda(word_count) | RunnableLambda(format_output)
```

将任意 Python 函数包装为 Runnable，融入 LCEL 管道中。
适合处理数据转换、格式化等轻量逻辑。

## 设计要点

- LCEL 的核心理念是 "一切皆 Runnable"，通过 `|` 自由组合
- 数据在管道中流动的形式始终是 dict
- `RunnablePassthrough.assign()` 是构建复杂链最常用的模式之一
