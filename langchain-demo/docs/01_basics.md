# Demo 01 -- 基础: 模型调用、Prompt、Output Parser

## 目标

理解 LangChain 与 LLM 交互的三个核心组件及其协作方式。

## 涉及文件

- [demo_01_basics.py](../demos/demo_01_basics.py)
- [config.py](../demos/config.py)

## 知识点

### 1. Chat Model (模型调用)

```python
from config import get_llm
llm = get_llm(temperature=0.7)
response = llm.invoke("用一句话介绍 Python")
```

LangChain 的 `ChatOpenAI` 封装了 OpenAI 兼容的 Chat Completion API。
`invoke()` 是 LangChain 的标准调用接口，所有 Runnable 对象都支持。
`temperature` 控制输出的随机性: 0=确定性, 1=高随机性。

### 2. ChatPromptTemplate (提示词模板)

```python
template = ChatPromptTemplate.from_messages([
    ("system", "你是一位{role}，请用{style}的风格回答问题。"),
    ("human", "{question}")
])
prompt_value = template.invoke({"role": "专家", "style": "简洁", "question": "..."})
```

Prompt 模板将变量与模板分离，使得同一结构可复用。
消息列表支持 system / human / ai 三种角色。

### 3. OutputParser (输出解析器)

```python
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser

parser = CommaSeparatedListOutputParser()
chain = template | llm | parser
result = chain.invoke({...})  # 返回 list 而非 str
```

OutputParser 将模型的原始文本输出转换为结构化数据。
常用的还有: `JsonOutputParser`, `PydanticOutputParser`, `StructuredOutputParser`。

### 4. LCEL 管道 (|)

```python
chain = prompt | llm | parser
```

`|` 是 LangChain Expression Language 的管道操作符，
将 Runnable 串联为一个 DAG (有向无环图)。

## 设计要点

- `get_llm()` 自动根据 `LLM_PROVIDER` 环境变量选择 OpenAI 或 DeepSeek
- 所有 Demo 在 `__main__` 开头调用 `check_api_key()` 进行前置校验
- `print_config()` 打印当前使用的后端和模型名称
