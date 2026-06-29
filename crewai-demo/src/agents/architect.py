"""
架构师 Agent —— 技术方案与系统设计

角色定位：基于产品需求文档，设计系统架构、选择技术栈、
输出详细的技术方案文档。
"""
from crewai import Agent

from src.config import get_llm
from src.tools.tools import TechStackRecommenderTool, SearchSimulatorTool


def create_architect(llm=None) -> Agent:
    """
    创建架构师 Agent

    参数:
        llm: LLM 实例（可选，默认使用全局配置）
    返回:
        CrewAI Agent 实例
    """
    if llm is None:
        llm = get_llm(temperature=0.3)  # 架构设计需要严谨，低温度

    return Agent(
        role="系统架构师",
        goal=(
            "基于产品需求文档，设计可扩展、高可用、高性能的系统架构方案。"
            "选择最适合的技术栈，输出包含架构图描述、模块划分、接口定义、"
            "数据模型和数据流设计的完整技术方案。"
        ),
        backstory=(
            "你是一位拥有 15 年经验的系统架构师，曾在电商、金融、AI 等多个领域设计过大规模分布式系统。"
            "你精通微服务、事件驱动、CQRS、DDD 等各种架构模式，能根据业务场景做出最优选择。"
            "你坚信'简单即美'——能用简单方案解决的问题绝不引入不必要的复杂性。"
            "你习惯为每个技术决策附带理由（ADR），让团队理解'为什么这样选'而不仅仅是'怎么做'。"
            "在设计时你会主动考虑：可扩展性、可维护性、安全性、成本四个维度。"
        ),
        tools=[TechStackRecommenderTool(), SearchSimulatorTool()],
        llm=llm,
        verbose=True,
        allow_delegation=True,  # 架构师可以将子任务委托给其他 Agent
        max_iter=7,
    )
