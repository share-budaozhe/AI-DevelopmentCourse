"""
审核型 Agent —— 负责质量审查与改进建议
"""
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm
from src.tools.tools import read_shared_context, write_shared_context


SYSTEM_PROMPT = """你是一个专业的内容审核官（Reviewer Agent），职责是：
1. 审阅写作专员提交的初稿
2. 从以下维度进行质量评估：
   - ✅ 内容准确性：事实是否准确，逻辑是否自洽
   - ✅ 结构完整性：是否有清晰的开头、主体和结尾
   - ✅ 语言表达：用词是否恰当，语句是否通顺
   - ✅ 目标适配：是否符合指定的文体和受众需求
3. 给出具体的修改建议（指出问题 + 改进方案）
4. 将审阅意见写入共享上下文

你以严谨著称，既能看到文章的闪光点，也能敏锐发现改进空间。
请给出建设性的、具体的反馈意见。

请始终用中文输出。"""


def review() -> str:
    """审核文章初稿"""
    llm = get_llm(temperature=0.3)

    topic = read_shared_context.invoke({"field": "topic"})
    draft_content = read_shared_context.invoke({"field": "draft_content"})

    write_shared_context.invoke({"field": "status", "value": "reviewing"})

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"请对以下文章进行质量审核：\n\n"
                    f"【课题】\n{topic}\n\n"
                    f"【初稿】\n{draft_content}\n\n"
                    f"请从内容准确性、结构完整性、语言表达和目标适配四个维度进行评分（满分10分），"
                    f"并给出具体的改进建议。"
        )
    ]

    response = llm.invoke(messages)
    review_feedback = response.content

    write_shared_context.invoke({"field": "review_feedback", "value": review_feedback})
    write_shared_context.invoke({"field": "status", "value": "review_completed"})

    return review_feedback
