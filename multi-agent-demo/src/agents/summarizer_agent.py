"""
汇总型 Agent —— 综合全流程产出，生成最终交付物
"""
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm
from src.tools.tools import read_shared_context, write_shared_context


SYSTEM_PROMPT = """你是一个专业的汇总官（Summarizer Agent），职责是：
1. 收集本次协作全流程的所有产出（研究笔记、分析报告、初稿、审阅意见）
2. 综合所有信息，生成最终交付物
3. 交付物应包含：
   - 项目摘要（一句话概括）
   - 核心内容（经过审阅改进的最终版）
   - 协作过程回顾（各Agent的贡献总结）
4. 将最终交付物写入共享上下文

你是多智能体协作的最后一道工序，确保交付物的质量和完整性。

请始终用中文输出。"""


def summarize() -> str:
    """汇总全流程产出，生成最终交付物"""
    llm = get_llm(temperature=0.5)

    # 读取所有上下文
    fields = ["topic", "research_notes", "analysis_result",
              "draft_content", "review_feedback"]
    context = {}
    for field in fields:
        context[field] = read_shared_context.invoke({"field": field})

    write_shared_context.invoke({"field": "status", "value": "summarizing"})

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"请综合以下所有材料，生成最终交付物：\n\n"
                    f"【课题】\n{context['topic']}\n\n"
                    f"【研究笔记】\n{context['research_notes']}\n\n"
                    f"【分析报告】\n{context['analysis_result']}\n\n"
                    f"【初稿】\n{context['draft_content']}\n\n"
                    f"【审阅意见】\n{context['review_feedback']}\n\n"
                    f"请输出包含项目摘要、核心内容（已考虑审阅意见进行优化）和协作过程回顾的完整交付物。"
        )
    ]

    response = llm.invoke(messages)
    final_output = response.content

    write_shared_context.invoke({"field": "final_output", "value": final_output})
    write_shared_context.invoke({"field": "status", "value": "completed"})

    return final_output
