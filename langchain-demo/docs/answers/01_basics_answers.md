# Demo 01 参考答案 -- 基础

## 1. ChatOpenAI vs 直接调用 OpenAI API

LangChain 的 `ChatOpenAI` 将 API 调用包装为 `Runnable` 接口:

- **标准化**: 所有模型都通过 `.invoke()`, `.stream()`, `.batch()` 调用
- **可组合**: 作为 Runnable 可以与其他组件用 `|` 串联
- **可替换**: 切换到 Anthropic/本地模型只需改一行代码
- **内置功能**: 自动重试、token 计数、回调钩子

如果直接调用 `openai.ChatCompletion.create()`，每次都要处理认证、错误、结构化，且无法融入 LCEL 管道。

## 2. System/Human/AI 角色

- **system**: 设定 AI 的行为准则、角色、输出格式。是"元指令"
- **human**: 用户的输入
- **ai**: 历史中 AI 的回答 (多轮对话时使用)

去掉 system 消息: LLM 会失去行为约束，可能产生更随机的回答。但有时不需要 system 消息 (如简单的翻译任务)。

## 3. OutputParser 实现原理

`StrOutputParser` 简单地将 `AIMessage.content` 提取为字符串。
`CommaSeparatedListOutputParser` 按逗号分割字符串并 strip 空白。

OutputParser 失败时 (如 LLM 返回了非逗号分隔的内容):
- 默认会抛出 `OutputParserException`
- 可以通过 `.with_fallbacks()` 或自定义 `OutputFixingParser` 处理

## 4. LCEL 管道的实现

```python
# chain = prompt | llm | parser
# 等价于:
chain = prompt.__or__(llm).__or__(parser)
```

每个 Runnable 实现了 `__or__` 方法，返回 `RunnableSequence`。
`RunnableSequence` 的 `invoke()` 会依次调用每个组件，将上一个输出传给下一个输入。

与 Unix 管道的异同:
- 相同: 数据从左到右流动，前一个输出 = 后一个输入
- 不同: LCEL 管道可以自动处理 dict 的键映射 (如 `{"key": sub_chain}`)

## 5. 在 Prompt 中嵌入文件内容

方式一: 直接在代码中读取文件并传入变量
```python
with open("doc.txt") as f:
    content = f.read()
chain.invoke({"context": content, "question": "..."})
```

方式二: 使用 RunnablePassthrough.assign()
```python
chain = (
    RunnablePassthrough.assign(context=lambda _: open("doc.txt").read())
    | prompt | llm
)
```

方式三: 自定义 Tool 让 Agent 按需读取文件

方式一最直接但耦合度高，方式二稍好但仍是同步阻塞，方式三最灵活。

## 6. temperature=0 是否一定确定性?

**不是。** temperature=0 只是将概率分布中的随机性降到最低，但:
- GPU 浮点运算的不确定性 (不同硬件可能略有不同)
- Seed 参数: OpenAI 支持 `seed` 参数来控制确定性
- 不同模型版本: 即使是 temperature=0，模型更新后输出也可能变化

## 7. 文本提取为 JSON 的设计

```python
template = ChatPromptTemplate.from_messages([
    ("system", "你是一个信息提取工具。请严格输出 JSON 数组，每个元素包含 name/date/amount 字段。"),
    ("human", "从以下文本中提取信息:\n{text}\n\nJSON:")
])
```

技巧:
- system 消息强调 "严格输出 JSON"
- 在 human 消息末尾加上 "JSON:" 前缀引导格式
- 使用 `JsonOutputParser` 配合 Pydantic schema 做二次校验

## 8. 中英文逗号混用

`CommaSeparatedListOutputParser` 只识别英文逗号 `,`。
如果 LLM 返回 `列表,推导式,生成器` (中文逗号)，解析会失败，整个字符串被当成一个元素。

鲁棒方案:
```python
class RobustListParser(BaseOutputParser):
    def parse(self, text: str):
        # 统一用英文逗号分割
        return [item.strip() for item in text.replace("，", ",").split(",") if item.strip()]
```
