"""
产品经理 Agent —— 需求分析与产品定义

角色定位：负责理解用户需求、分析市场背景、定义产品功能边界，
输出结构化的产品需求文档（PRD）。
"""
from crewai import Agent

from src.config import get_llm
from src.tools.tools import RequirementAnalyzerTool


def create_product_manager(llm=None) -> Agent:
    """
    创建产品经理 Agent

    参数:
        llm: LLM 实例（可选，默认使用全局配置）
    返回:
        CrewAI Agent 实例
    """
    if llm is None:
        llm = get_llm(temperature=0.5)  # 产品经理需要更稳定的输出

    return Agent(
        role="产品经理",
        goal=(
            "深入理解用户需求，进行全面的市场和技术背景调研，"
            "产出结构清晰、边界明确的产品需求文档（PRD），"
            "为后续技术方案设计提供可靠依据。"
        ),
        backstory=(
            "你是一位拥有 10 年经验的资深产品经理，曾在多家头部互联网公司主导过从零到一的产品孵化。"
            "你擅长通过用户访谈、竞品分析和数据洞察来发现真正的用户痛点。"
            "你的 PRD 文档以逻辑严密、边界清晰著称，总能精准地为技术团队划定明确的功能范围。"
            "你习惯使用结构化的思维来拆解复杂需求，避免模糊和二义性。"
            "在协作中你注重上下文传递，确保下游团队能无缝接续你的工作。"
        ),
        tools=[RequirementAnalyzerTool()],
        llm=llm,
        verbose=True,
        allow_delegation=False,  # 产品经理专注需求分析，不委托
        max_iter=5,
    )
