"""
═══════════════════════════════════════════════════════════════
  🤖 LlamaIndex 学习教程 — src/demo_agents.py
  实验 6：Agent 智能体深入实验
═══════════════════════════════════════════════════════════════

核心知识点：
- Agent：能自主选择工具、制定计划来回答问题的智能体
- FunctionTool：将 Python 函数包装为 Agent 可调用的工具
- QueryEngineTool：将查询引擎包装为工具
- ReAct Agent：推理-行动循环
- Router Query Engine：自动路由到合适的索引
"""
from llama_index.core import (
    VectorStoreIndex, SummaryIndex, Settings, MockEmbedding,
)
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from sample_data import DEMO_DOCUMENTS


def setup():
    Settings.embed_model = MockEmbedding(embed_dim=384)


def experiment_function_tool():
    """🔬 实验 6.1：FunctionTool - 将函数包装为工具

    知识点：
    - 任何 Python 函数都可以变成 Agent 的工具
    - Agent 根据工具的描述（description）决定何时调用
    - 参数类型提示帮助 Agent 正确传参
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 6.1：FunctionTool")
    print(f"{'='*60}")

    def calculator(expression: str) -> str:
        """计算数学表达式的结果。支持加减乘除和括号。"""
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"计算结果: {expression} = {result}"
        except Exception as e:
            return f"计算错误: {e}"

    def get_weather(city: str) -> str:
        """获取指定城市的天气信息（模拟）。"""
        weather_data = {
            "北京": "晴，25°C，湿度 40%",
            "上海": "多云，28°C，湿度 65%",
            "深圳": "阵雨，30°C，湿度 80%",
        }
        return weather_data.get(city, f"未找到 {city} 的天气数据")

    calc_tool = FunctionTool.from_defaults(
        fn=calculator,
        name="calculator",
        description="计算数学表达式。输入如 '2+3*4'。",
    )

    weather_tool = FunctionTool.from_defaults(
        fn=get_weather,
        name="get_weather",
        description="获取城市天气。输入城市名称（如'北京'）。",
    )

    print(f"\n  创建的 FunctionTool:")
    print(f"  - calculator: 数学计算工具")
    print(f"  - get_weather: 天气查询工具")

    # 演示工具调用
    print(f"\n  工具调用演示:")
    print(f"    calculator('2+3*4') → {calculator('2+3*4')}")
    print(f"    get_weather('上海')   → {get_weather('上海')}")


def experiment_query_engine_tool():
    """🔬 实验 6.2：QueryEngineTool - 将查询引擎变为工具

    知识点：
    - QueryEngineTool 让 Agent 可以用查询引擎作为工具
    - 可以组合多个索引，Agent 自动选择用哪个
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 6.2：QueryEngineTool")
    print(f"{'='*60}")

    setup()

    # 创建两个不同领域的索引
    tech_docs = DEMO_DOCUMENTS[:3]  # AI 相关
    general_docs = DEMO_DOCUMENTS[3:]  # 通用相关

    tech_index = VectorStoreIndex.from_documents(tech_docs)
    general_index = VectorStoreIndex.from_documents(general_docs)

    tech_tool = QueryEngineTool.from_defaults(
        query_engine=tech_index.as_query_engine(),
        name="tech_knowledge",
        description="查询 AI、编程、技术相关的知识。当问题涉及技术概念时使用。",
    )

    general_tool = QueryEngineTool.from_defaults(
        query_engine=general_index.as_query_engine(),
        name="general_knowledge",
        description="查询通用知识。",
    )

    print(f"\n  创建的 QueryEngineTool:")
    print(f"  - tech_knowledge: 技术知识查询（3 个文档）")
    print(f"  - general_knowledge: 通用知识查询（3 个文档）")

    print(f"\n  💡 Agent 会根据问题自动选择正确的工具:")
    print(f"    'Python 是谁发明的？' → tech_knowledge")
    print(f"    '什么是 RAG？'       → tech_knowledge")
    print(f"    '什么是向量数据库？'   → general_knowledge")


def experiment_agent_patterns():
    """🔬 实验 6.3：Agent 的核心模式

    知识点：
    - ReAct：推理(Reasoning) + 行动(Acting) 循环
    - Router：根据问题自动路由
    - 多 Agent 协作
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 6.3：Agent 核心模式")
    print(f"{'='*60}")

    patterns = """
  LlamaIndex Agent 的三种核心模式：

  1. ReAct Agent（推理-行动循环）
     流程: 思考 → 选择工具 → 执行 → 观察结果 → 再思考 → ...
     每次循环 LLM 都要决策：继续用工具还是给出最终答案？
     这是最通用的 Agent 模式，适用于复杂多步骤推理。

  2. Router Query Engine（路由模式）
     流程: 分析问题 → 选择合适的工具 → 单次调用 → 返回结果
     适用：问题可以明确分类、不需要多步骤的场景。
     例如：公司有"技术文档"和"HR 政策"两个知识库，
           问"Python 版本是多少" → 路由到技术文档
           问"年假有几天" → 路由到 HR 政策

  3. Multi-Agent（多智能体协作）
     多个 Agent 各司其职，通过消息传递协作。
     适用：任务涉及多个领域，需要专业分工。

  选择建议：
  - 简单分类问题 → Router
  - 需要多步推理 → ReAct Agent
  - 多领域复杂任务 → Multi-Agent
"""
    print(patterns)


def run():
    """运行实验 6：Agent 智能体深入实验。"""
    experiment_function_tool()
    experiment_query_engine_tool()
    experiment_agent_patterns()
    print(f"\n  ✅ 实验 6 完成\n")


if __name__ == "__main__":
    run()
