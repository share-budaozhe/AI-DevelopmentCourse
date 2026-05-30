# Demo 01 启发性问题 -- 基础

## 基础理解

1. LangChain 的 `ChatOpenAI` 和直接调用 `openai.ChatCompletion.create()` 有什么区别?
   为什么需要这一层抽象?

2. `ChatPromptTemplate.from_messages()` 中的 system / human / ai 三种角色分别起什么作用?
   如果去掉 system 消息会怎样?

3. `StrOutputParser` 和 `CommaSeparatedListOutputParser` 的实现原理是什么?
   OutputParser 失败时会发生什么?

## 深入思考

4. LCEL 管道 (|) 在 Python 中是如何实现的?
   Runnable 对象的 `__or__` 方法做了什么? 这与 Unix 管道有什么异同?

5. 如果要在 Prompt 模板中嵌入一个文件的内容 (而不是手动传入)
   ，有哪些实现方式? 各自的优缺点是什么?

6. 当温度 (temperature) 设为 0 时，LLM 的输出是否一定是确定性的?
   什么情况下仍可能出现不同输出?

## 实战挑战

7. 设计一个 Prompt 模板，让 LLM 将一段自由文本提取为 JSON 格式的 "姓名、日期、金额"
   三元组列表。考虑: 如何让 LLM 稳定输出有效 JSON?

8. `CommaSeparatedListOutputParser` 在中文逗号和英文逗号混用时可能出现什么问题?
   如何设计一个更鲁棒的中文列表解析器?
