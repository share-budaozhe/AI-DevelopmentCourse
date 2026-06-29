"""
CrewAI 编排模块 —— 将 Agent 和 Task 组合成协作团队

本模块是 CrewAI 的核心编排逻辑：
1. 创建 5 个角色 Agent
2. 定义 5 个顺序执行的 Task
3. 使用 Crew 类将 Agent + Task 组合成可运行的团队

CrewAI 支持两种执行模式：
- Sequential（顺序）：任务按列表顺序依次执行 → 推荐用于流水线式工作流
- Hierarchical（层级）：有一个 Manager Agent 负责分发任务 → 适合复杂自治场景

本 Demo 默认使用 Sequential 模式，展示清晰的流水线协作过程。
"""
from crewai import Crew, Process

from src.config import get_llm, get_crewai_config
from src.agents.product_manager import create_product_manager
from src.agents.architect import create_architect
from src.agents.developer import create_developer
from src.agents.tester import create_tester
from src.agents.devops import create_devops
from src.tasks.tasks import (
    create_requirement_task,
    create_architecture_task,
    create_development_task,
    create_testing_task,
    create_deployment_task,
)


def build_crew(topic: str, process: str = None, verbose: bool = None) -> Crew:
    """
    构建 CrewAI 协作团队

    参数:
        topic: 项目课题（用户需求描述）
        process: 执行模式 "sequential"（顺序）或 "hierarchical"（层级）
        verbose: 是否输出详细日志

    返回:
        配置好的 Crew 实例，可直接调用 kickoff()
    """
    # ── 配置 ──────────────────────────────────
    crew_config = get_crewai_config()
    if process is None:
        process = crew_config["process"]
    if verbose is None:
        verbose = crew_config["verbose"]

    # 使用同一个 LLM 配置
    llm = get_llm()

    # ── 创建 Agent ────────────────────────────
    product_manager = create_product_manager(llm)
    architect = create_architect(llm)
    developer = create_developer(llm)
    tester = create_tester(llm)
    devops = create_devops(llm)

    # ── 创建 Task ─────────────────────────────
    requirement_task = create_requirement_task(product_manager, topic)
    architecture_task = create_architecture_task(architect, topic)
    development_task = create_development_task(developer, topic)
    testing_task = create_testing_task(tester, topic)
    deployment_task = create_deployment_task(devops, topic)

    # ── 设置任务间的上下文依赖 ─────────────────
    # CrewAI 会按顺序将前一个任务的输出作为后一个任务的上下文
    architecture_task.context = [requirement_task]
    development_task.context = [architecture_task]
    testing_task.context = [development_task]
    deployment_task.context = [testing_task]

    # ── 创建 Crew ─────────────────────────────
    process_enum = Process.sequential if process == "sequential" else Process.hierarchical

    crew = Crew(
        agents=[product_manager, architect, developer, tester, devops],
        tasks=[
            requirement_task,
            architecture_task,
            development_task,
            testing_task,
            deployment_task,
        ],
        process=process_enum,
        verbose=verbose,
        memory=True,  # 启用 CrewAI 内置记忆，跨任务保留关键信息
        planning=True,  # 启用任务规划，让 Agent 在执行前先制定计划
    )

    return crew


def run_software_team(topic: str, process: str = None, verbose: bool = None) -> dict:
    """
    启动软件开发团队，执行完整的协作流程

    参数:
        topic: 项目课题
        process: "sequential" 或 "hierarchical"
        verbose: 是否详细输出

    返回:
        dict，包含：
        - result: CrewAI 最终输出文本
        - token_usage: Token 使用统计
        - task_outputs: 各任务的详细输出
    """
    crew = build_crew(topic, process, verbose)

    # 执行协作流程
    result = crew.kickoff()

    # 构建返回结果
    output = {
        "result": str(result),
        "token_usage": getattr(result, "token_usage", {}),
        "task_outputs": getattr(result, "tasks_output", []),
        "topic": topic,
        "process": process or get_crewai_config()["process"],
    }

    return output
