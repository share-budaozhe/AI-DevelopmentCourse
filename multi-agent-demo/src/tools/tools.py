"""
工具模块 —— 各 Agent 可调用的共享工具
"""
from langchain_core.tools import tool
from datetime import datetime
from typing import Optional

# ──────────────────────────────────────────────
# 数据存储（模拟共享黑板/共享内存）
# ──────────────────────────────────────────────
shared_context = {
    "topic": "",
    "research_notes": "",
    "analysis_result": "",
    "draft_content": "",
    "review_feedback": "",
    "final_output": "",
    "status": "initialized",
}

# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

@tool
def get_current_time(format_string: Optional[str] = None) -> str:
    """获取当前时间，可选格式参数（如 '%Y-%m-%d %H:%M:%S'）"""
    fmt = format_string or "%Y-%m-%d %H:%M:%S"
    return datetime.now().strftime(fmt)


@tool
def read_shared_context(field: str) -> str:
    """从共享上下文中读取指定字段的值。

    可用字段: topic, research_notes, analysis_result, draft_content, review_feedback, final_output, status
    """
    return shared_context.get(field, f"字段 '{field}' 不存在")


@tool
def write_shared_context(field: str, value: str) -> str:
    """向共享上下文写入指定字段的值。

    可用字段: topic, research_notes, analysis_result, draft_content, review_feedback, final_output, status
    """
    if field in shared_context:
        shared_context[field] = value
        return f"已成功写入字段 '{field}'"
    return f"字段 '{field}' 不存在"


@tool
def search_knowledge_base(query: str) -> str:
    """模拟知识库检索——根据查询关键词返回相关信息"""
    knowledge = {
        "人工智能": (
            "人工智能(AI)是计算机科学的一个重要分支，致力于创建能够模拟人类智能的系统。"
            "当前主流技术包括机器学习、深度学习、自然语言处理、计算机视觉等。"
            "AI已广泛应用于医疗诊断、自动驾驶、智能客服、金融风控等领域。"
        ),
        "多智能体系统": (
            "多智能体系统(MAS)由多个自主决策的智能体组成，通过通信、协作与竞争完成复杂任务。"
            "核心优势包括：任务分解与并行处理、鲁棒性与容错性、灵活性与可扩展性。"
            "典型架构有集中式控制、分布式控制、混合式控制。"
        ),
        "机器学习": (
            "机器学习是AI的核心子领域，使计算机能够从数据中学习模式而无需显式编程。"
            "主要类型包括：监督学习、无监督学习、半监督学习和强化学习。"
            "常用算法有线性回归、决策树、支持向量机、神经网络等。"
        ),
        "大语言模型": (
            "大语言模型(LLM)是基于Transformer架构的预训练语言模型，如GPT、Claude、LLaMA等。"
            "参数量通常在数十亿到数千亿级别，通过海量文本训练获得强大的语言理解与生成能力。"
            "核心能力包括：文本生成、翻译、摘要、问答、代码生成等。"
        ),
    }
    for keyword, info in knowledge.items():
        if keyword in query:
            return info
    return f"未找到与 '{query}' 相关的知识。可尝试关键词：人工智能、多智能体系统、机器学习、大语言模型"


@tool
def calculate(expression: str) -> str:
    """执行数学计算（如 '2 + 2', '3 * 4', '(1 + 2) * 3'）"""
    try:
        # 安全计算：仅允许基本数学运算
        safe_globals = {"__builtins__": {}}
        safe_locals = {}
        result = eval(expression, safe_globals, safe_locals)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"
