"""
多智能体协作工作流 —— 基于 LangGraph 的状态图编排
"""
from typing import TypedDict, Dict, Any, Annotated, Literal
from langgraph.graph import StateGraph, END
from src.agents.research_agent import research
from src.agents.analysis_agent import analyze
from src.agents.writer_agent import write
from src.agents.reviewer_agent import review
from src.agents.summarizer_agent import summarize
from src.tools.tools import read_shared_context, shared_context


# ──────────────────────────────────────────────
# 定义状态类型
# ──────────────────────────────────────────────
class AgentState(TypedDict):
    """协作工作流的状态"""
    topic: str
    writing_style: str
    research_output: str
    analysis_output: str
    draft_output: str
    review_output: str
    final_output: str
    status: str
    error: str


# ──────────────────────────────────────────────
# 节点函数（每个节点对应一个 Agent 的执行）
# ──────────────────────────────────────────────

# 工具函数：重置共享上下文
def _reset_context(topic: str):
    shared_context["topic"] = topic
    shared_context["research_notes"] = ""
    shared_context["analysis_result"] = ""
    shared_context["draft_content"] = ""
    shared_context["review_feedback"] = ""
    shared_context["final_output"] = ""
    shared_context["status"] = "initialized"


def research_node(state: AgentState) -> Dict[str, Any]:
    """研究节点：执行信息调研"""
    print("\n" + "=" * 60)
    print("🔍 【研究 Agent】开始调研...")
    print("=" * 60)

    _reset_context(state["topic"])

    try:
        output = research(state["topic"])
        print(f"\n✅ 调研完成，输出长度: {len(output)} 字符")
        return {"research_output": output, "status": "research_completed"}
    except Exception as e:
        error_msg = f"研究阶段失败: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {"error": error_msg, "status": "error"}


def analysis_node(state: AgentState) -> Dict[str, Any]:
    """分析节点：执行深度分析"""
    print("\n" + "=" * 60)
    print("📊 【分析 Agent】开始分析...")
    print("=" * 60)

    try:
        output = analyze()
        print(f"\n✅ 分析完成，输出长度: {len(output)} 字符")
        return {"analysis_output": output, "status": "analysis_completed"}
    except Exception as e:
        error_msg = f"分析阶段失败: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {"error": error_msg, "status": "error"}


def writing_node(state: AgentState) -> Dict[str, Any]:
    """写作节点：撰写内容"""
    print("\n" + "=" * 60)
    print("✍️  【写作 Agent】开始创作...")
    print("=" * 60)

    try:
        style = state.get("writing_style", "技术博客")
        output = write(style)
        print(f"\n✅ 写作完成，输出长度: {len(output)} 字符")
        return {"draft_output": output, "status": "writing_completed"}
    except Exception as e:
        error_msg = f"写作阶段失败: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {"error": error_msg, "status": "error"}


def review_node(state: AgentState) -> Dict[str, Any]:
    """审阅节点：质量审查"""
    print("\n" + "=" * 60)
    print("📋 【审核 Agent】开始审阅...")
    print("=" * 60)

    try:
        output = review()
        print(f"\n✅ 审阅完成，输出长度: {len(output)} 字符")
        return {"review_output": output, "status": "review_completed"}
    except Exception as e:
        error_msg = f"审阅阶段失败: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {"error": error_msg, "status": "error"}


def summarize_node(state: AgentState) -> Dict[str, Any]:
    """汇总节点：生成最终交付物"""
    print("\n" + "=" * 60)
    print("📦 【汇总 Agent】生成最终交付物...")
    print("=" * 60)

    try:
        output = summarize()
        final = read_shared_context.invoke({"field": "final_output"})
        print(f"\n✅ 汇总完成，输出长度: {len(output)} 字符")
        return {"final_output": final, "status": "completed"}
    except Exception as e:
        error_msg = f"汇总阶段失败: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {"error": error_msg, "status": "error"}


# ──────────────────────────────────────────────
# 工作流编排
# ──────────────────────────────────────────────

def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """条件路由：检查是否有错误"""
    if state.get("status") == "error":
        return "end"
    return "continue"


def build_collaboration_graph() -> StateGraph:
    """构建多智能体协作流程图"""
    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("review", review_node)
    workflow.add_node("summarize", summarize_node)

    # 添加边：顺序执行
    workflow.add_edge("research", "analysis")
    workflow.add_edge("analysis", "writing")
    workflow.add_edge("writing", "review")
    workflow.add_edge("review", "summarize")
    workflow.add_edge("summarize", END)

    # 设置入口
    workflow.set_entry_point("research")

    # 编译
    return workflow.compile()


def run_collaboration(topic: str, style: str = "技术博客") -> Dict[str, Any]:
    """运行多智能体协作工作流"""
    graph = build_collaboration_graph()

    initial_state: AgentState = {
        "topic": topic,
        "writing_style": style,
        "research_output": "",
        "analysis_output": "",
        "draft_output": "",
        "review_output": "",
        "final_output": "",
        "status": "started",
        "error": "",
    }

    result = graph.invoke(initial_state)
    return result
