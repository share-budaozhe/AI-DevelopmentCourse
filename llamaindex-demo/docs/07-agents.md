# 🤖 LlamaIndex 学习 — Agent 与工具

## 什么是 Agent？

Agent 是「能自主选择工具、制定计划来解决问题的智能体」。
与 QueryEngine（固定流程）不同，Agent 会自己思考：
"这个问题该用什么工具？该分几步解决？"

Agent 需要 LLM 来推理，完美支持 DeepSeek。

## ReAct Agent（核心模式）

ReAct = Reasoning（推理）+ Acting（行动）

```
用户: "北京今天天气怎么样？适合户外运动吗？"
    │
    ▼
Agent 思考: 需要查天气
    │
    ▼
调用 get_weather("北京") → "晴，25°C"
    │
    ▼
Agent 思考: 25°C 晴天，适合户外运动
    │
    ▼
最终答案: "北京今天晴天，25°C，非常适合户外运动！"
```

## FunctionTool

把普通 Python 函数包装为 Agent 可调用的工具：

```python
from llama_index.core.tools import FunctionTool

def get_stock_price(symbol: str) -> str:
    """获取股票实时价格。"""
    return f"{symbol} 当前价格: $150.00"

tool = FunctionTool.from_defaults(
    fn=get_stock_price,
    name="stock_price",
    description="查询股票实时价格。输入股票代码（如 AAPL）。",
)
```

## QueryEngineTool

把查询引擎包装为 Agent 的工具——这是 RAG + Agent 的标准组合：

```python
from llama_index.core.tools import QueryEngineTool
from config import auto_setup

auto_setup()  # DeepSeek 或 OpenAI

# 技术文档知识库
tech_index = VectorStoreIndex.from_documents(tech_docs)
tech_tool = QueryEngineTool.from_defaults(
    query_engine=tech_index.as_query_engine(),
    name="tech_docs",
    description="查询技术文档。当问题涉及 Python/AI 等技术时使用。",
)

# HR 政策知识库
hr_index = VectorStoreIndex.from_documents(hr_docs)
hr_tool = QueryEngineTool.from_defaults(
    query_engine=hr_index.as_query_engine(),
    name="hr_policy",
    description="查询公司 HR 政策。当问题涉及假期、福利时使用。",
)

# Agent 自动选择工具
from llama_index.core.agent import ReActAgent

agent = ReActAgent.from_tools([tech_tool, hr_tool])
agent.chat("Python 版本该用哪个？")  # → 自动选 tech_tool
agent.chat("年假有几天？")          # → 自动选 hr_tool
```

## Router Query Engine

简单场景的轻量级「路由」方案：

```python
from llama_index.core.query_engine import RouterQueryEngine

router = RouterQueryEngine(
    selector=...,
    query_engine_tools=[tech_tool, hr_tool],
)
```

Agent vs Router 的选择：
- 问题可明确分类 → Router（更快，一次调用）
- 问题需要多步推理 → Agent（更灵活，多次调用）

## 多工具协同示例

```python
from config import auto_setup

auto_setup()  # 启用 DeepSeek

# 工具 1: 计算器
def calculator(expr: str) -> str:
    """计算数学表达式。"""
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return f"{expr} = {result}"
    except:
        return "计算失败"

# 工具 2: RAG 查询
from llama_index.core.tools import QueryEngineTool
doc_tool = QueryEngineTool.from_defaults(
    query_engine=index.as_query_engine(),
    name="knowledge_base",
    description="知识库查询",
)

# 创建 Agent
from llama_index.core.agent import ReActAgent

agent = ReActAgent.from_tools(
    [FunctionTool.from_defaults(fn=calculator), doc_tool],
    verbose=True,
)

# Agent 会自动判断：先算数学，再查文档
agent.chat("如果每天读 50 页，300 页的书要几天读完？")
# → 调用 calculator("300/50") → "300/50 = 6.0" → "需要 6 天"
```

## 💡 成本提示

DeepSeek 做 Agent 非常适合：
- ReAct Agent 每次决策是单独一次 LLM 调用
- DeepSeek 每百万 token ≈ ￥1，Agent 多次调用的总成本依然很低
- 一个复杂 Agent 任务（5-10 步推理）≈ ￥0.01-0.05

## Agent 最佳实践

1. **工具描述要精确**：Agent 靠描述来判断该用哪个工具
2. **工具职责要单一**：一个工具做一件事
3. **错误处理**：工具应该返回友好的错误信息，而非抛异常
4. **Token 监控**：Agent 的思考过程也消耗 Token（DeepSeek 成本低，但也别浪费）
