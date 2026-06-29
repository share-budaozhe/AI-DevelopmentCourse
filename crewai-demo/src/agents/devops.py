"""
运维工程师 Agent —— 部署方案与运维手册

角色定位：设计 CI/CD 流水线、Docker 容器化方案、部署架构，
输出部署方案和运维手册。
"""
from crewai import Agent

from src.config import get_llm
from src.tools.tools import DeployCheckTool, SearchSimulatorTool


def create_devops(llm=None) -> Agent:
    """
    创建运维工程师 Agent

    参数:
        llm: LLM 实例（可选，默认使用全局配置）
    返回:
        CrewAI Agent 实例
    """
    if llm is None:
        llm = get_llm(temperature=0.4)

    return Agent(
        role="DevOps 运维工程师",
        goal=(
            "设计完整的 CI/CD 流水线和容器化部署方案，"
            "覆盖构建、测试、部署、监控、日志、告警的全链路。"
            "输出可直接交付生产环境使用的部署方案和运维手册。"
        ),
        backstory=(
            "你是一位 DevOps 专家，拥有 10 年运维和平台工程经验。"
            "你推崇 Infrastructure as Code（IaC）和 GitOps 理念，"
            "认为一切基础设施配置都应该版本化管理。"
            "你经历过无数次凌晨 3 点的线上故障，深知可观测性的重要性——"
            "日志、指标、链路追踪缺一不可。"
            "你设计的部署方案总是包含：健康检查、优雅关闭、资源限制、"
            "自动扩缩容、蓝绿部署/金丝雀发布等生产级实践。"
            "你相信'部署只是开始，运维才是日常'，因此运维手册总是详尽实用。"
        ),
        tools=[DeployCheckTool(), SearchSimulatorTool()],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=6,
    )
