"""
分析型 Agent —— 对研究笔记进行深度分析
"""
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm
from src.tools.tools import read_shared_context, write_shared_context


SYSTEM_PROMPT = """你是一个专业的分析师（Analysis Agent），职责是：
1. 阅读研究员提供的研究笔记
2. 进行深度分析，包括：
   - 识别关键趋势与模式
   - 比较不同观点或方法
   - 评估信息的可靠性与局限性
   - 提出深入见解和延伸思考
3. 将分析结果写入共享上下文

你擅长逻辑推理和批判性思考，能够从信息中发现隐藏的关联和洞见。
在输出分析报告时，请使用清晰的 Markdown 格式，包含：
- 核心发现总结
- 趋势与模式分析
- 优势与局限性评估
- 延伸思考与建议

请始终用中文输出。"""


def analyze() -> str:
    """对研究笔记进行分析"""
    llm = get_llm(temperature=0.4)

    # 读取研究笔记
    topic = read_shared_context.invoke({"field": "topic"})
    research_notes = read_shared_context.invoke({"field": "research_notes"})

    write_shared_context.invoke({"field": "status", "value": "analyzing"})

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"请对以下研究笔记进行深度分析：\n\n"
                    f"【课题】\n{topic}\n\n"
                    f"【研究笔记】\n{research_notes}\n\n"
                    f"请从多角度进行系统分析，形成有深度分析报告。"
        )
    ]

    response = llm.invoke(messages)
    analysis_result = response.content

    # 保存到共享上下文
    write_shared_context.invoke({"field": "analysis_result", "value": analysis_result})
    write_shared_context.invoke({"field": "status", "value": "analysis_completed"})

    return analysis_result
