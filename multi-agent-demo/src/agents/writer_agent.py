"""
写作型 Agent —— 基于分析结果创作内容
"""
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm
from src.tools.tools import read_shared_context, write_shared_context


SYSTEM_PROMPT = """你是一个专业的写作专员（Writer Agent），职责是：
1. 阅读分析报告
2. 根据指定的文体和受众，将分析结果转化为高质量的文章
3. 确保文章结构清晰、语言流畅、逻辑严密
4. 将初稿写入共享上下文

你擅长将复杂的专业内容转化为易于理解的优质文章。
在写作时注意：
- 使用吸引人的标题和小标题
- 保持段落清晰，每段聚焦一个主题
- 适当使用列表、表格等元素增强可读性
- 语言风格应专业但不晦涩

请始终用中文输出。"""


def write(style: str = "技术博客") -> str:
    """基于分析结果撰写文章"""
    llm = get_llm(temperature=0.7)

    topic = read_shared_context.invoke({"field": "topic"})
    analysis_result = read_shared_context.invoke({"field": "analysis_result"})

    write_shared_context.invoke({"field": "status", "value": "writing"})

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"请基于以下分析报告，撰写一篇 {style} 风格的文章：\n\n"
                    f"【课题】\n{topic}\n\n"
                    f"【分析报告】\n{analysis_result}\n\n"
                    f"文体要求：{style}\n"
                    f"字数要求：800-1500 字\n"
                    f"请直接输出文章正文。"
        )
    ]

    response = llm.invoke(messages)
    draft_content = response.content

    write_shared_context.invoke({"field": "draft_content", "value": draft_content})
    write_shared_context.invoke({"field": "status", "value": "writing_completed"})

    return draft_content
