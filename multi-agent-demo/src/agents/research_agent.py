"""
研究型 Agent —— 负责信息搜集与初步调研
"""
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm
from src.tools.tools import search_knowledge_base, write_shared_context, read_shared_context

# 系统提示词 —— 定义 Agent 的角色与职责
SYSTEM_PROMPT = """你是一个专业的研究员（Research Agent），职责是：
1. 接收用户提出的课题
2. 使用知识库检索工具收集相关信息
3. 整理研究笔记，提取核心观点、关键数据和发展脉络
4. 将研究成果写入共享上下文

你注重信息的准确性和全面性，擅长结构化思考。
在输出研究笔记时，请使用清晰的 Markdown 格式，包含：
- 课题概述
- 核心发现（用列表呈现）
- 关键数据与事实
- 参考资料摘要

请始终用中文输出。"""


def research(topic: str) -> str:
    """执行研究流程"""
    llm = get_llm(temperature=0.3)

    # 先写入话题到共享上下文
    write_shared_context.invoke({"field": "topic", "value": topic})
    write_shared_context.invoke({"field": "status", "value": "researching"})

    # 构建消息
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"请对以下课题进行全面调研：\n\n课题：{topic}\n\n"
                    f"请使用知识库检索工具获取相关信息，整理出结构化的研究笔记。"
        )
    ]

    # 绑定工具
    llm_with_tools = llm.bind_tools([search_knowledge_base])

    response = llm_with_tools.invoke(messages)

    # 处理工具调用
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "search_knowledge_base":
                result = search_knowledge_base.invoke(tc["args"])
                messages.append(response)
                messages.append(HumanMessage(content=f"检索结果：{result}"))

        # 获取最终回复
        final_response = llm.invoke(messages)
        research_notes = final_response.content
    else:
        research_notes = response.content

    # 保存到共享上下文
    write_shared_context.invoke({"field": "research_notes", "value": research_notes})
    write_shared_context.invoke({"field": "status", "value": "research_completed"})

    return research_notes
