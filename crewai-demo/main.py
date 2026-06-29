"""
CrewAI 多 Agent 协作 Demo —— 主入口

一个基于 CrewAI 的软件研发团队模拟系统。
5 个角色 Agent（产品经理、架构师、开发、测试、运维）通过 CrewAI 框架
协同完成从需求分析到部署上线的全流程。

用法:
    python main.py                          # 交互模式
    python main.py --demo                   # 演示模式（内置示例）
    python main.py --topic "你的需求"       # 直接指定需求
    python main.py --process hierarchical  # 使用层级管理模式
"""

import sys
import argparse
import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from src.crew import run_software_team

console = Console()

# ──────────────────────────────────────────────
# 演示项目（内置示例需求）
# ──────────────────────────────────────────────
DEMO_PROJECTS = [
    {
        "title": "智能客服工单系统",
        "desc": "构建一个企业级智能客服工单管理平台，支持多渠道接入、"
                "智能分配、SLA 管理、数据分析等功能。需支持日处理 10 万+ 工单量。",
    },
    {
        "title": "在线教育直播平台",
        "desc": "开发一个在线教育直播互动平台，支持万人同时在线、"
                "实时白板协作、AI 助教问答、课后回放与学情分析。",
    },
    {
        "title": "AI 驱动的代码审查助手",
        "desc": "构建一个 AI 驱动的代码审查工具，集成 GitHub/GitLab，"
                "支持自动代码审查、安全漏洞检测、重构建议、团队编码规范管理。",
    },
    {
        "title": "医疗健康数据中台",
        "desc": "设计医疗健康数据中台，整合 HIS/EMR/LIS 等多源数据，"
                "支持数据治理、隐私计算、临床辅助决策和科研数据分析。",
    },
]

WELCOME_ART = r"""
╔══════════════════════════════════════════════════════════╗
║          🤖 CrewAI 多 Agent 软件研发团队 Demo            ║
║       Multi-Agent Software Development Team              ║
║       Framework: CrewAI  |  5 Agents  |  5 Tasks        ║
╚══════════════════════════════════════════════════════════╝
"""


def print_header():
    """输出欢迎页"""
    console.print(WELCOME_ART, style="bold cyan")
    console.print(Panel.fit(
        "本 Demo 展示了 CrewAI 框架中 5 个角色 Agent 如何协作完成软件开发全流程：\n"
        "[yellow]📋 产品经理[/yellow] → [blue]🏗️ 架构师[/blue] → [green]💻 开发工程师[/green] → "
        "[magenta]🧪 测试工程师[/magenta] → [red]🚀 DevOps 工程师[/red]",
        title="🤝 CrewAI 协作模式",
        border_style="blue",
    ))


def print_agents_table():
    """输出 Agent 角色说明"""
    table = Table(title="🤖 Agent 角色详表", show_header=True,
                  header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Agent", style="bold")
    table.add_column("角色", style="bold")
    table.add_column("核心职责")
    table.add_column("可用工具")
    table.add_column("可委托")

    table.add_row(
        "[yellow]📋 Product Manager[/yellow]", "产品经理",
        "需求分析、竞品调研\nPRD 文档输出",
        "requirement_analyzer",
        "否"
    )
    table.add_row(
        "[blue]🏗️ Architect[/blue]", "系统架构师",
        "架构设计、技术选型\n技术方案文档",
        "tech_stack_recommender\nknowledge_search",
        "是"
    )
    table.add_row(
        "[green]💻 Developer[/green]", "高级开发工程师",
        "代码实现、API 开发\n自审自查",
        "code_reviewer\nknowledge_search",
        "否"
    )
    table.add_row(
        "[magenta]🧪 QA Tester[/magenta]", "测试工程师",
        "测试策略、质量评估\n测试报告输出",
        "code_reviewer",
        "否"
    )
    table.add_row(
        "[red]🚀 DevOps[/red]", "运维工程师",
        "CI/CD 设计、容器化\n部署方案与运维手册",
        "deploy_checker\nknowledge_search",
        "否"
    )

    console.print(table)


def print_process_info():
    """输出执行模式说明"""
    table = Table(title="⚙️ CrewAI 执行模式", show_header=True,
                  header_style="bold cyan", box=box.ROUNDED)
    table.add_column("模式", style="bold green")
    table.add_column("说明")
    table.add_column("适用场景")

    table.add_row(
        "Sequential（顺序）",
        "任务按顺序依次执行，前一任务的输出\n自动成为下一任务的上下文",
        "流水线式工作流，步骤之间有明确依赖关系\n（本 Demo 默认模式）"
    )
    table.add_row(
        "Hierarchical（层级）",
        "由 Manager Agent 负责分发任务，\n动态决定执行顺序和委托关系",
        "复杂自治场景，需要灵活的任务分配和\n动态决策"
    )

    console.print(table)


def show_demo_menu(projects: list) -> Optional[int]:
    """显示演示项目菜单"""
    console.print("\n[bold]请选择一个演示项目:[/bold]\n")
    for i, proj in enumerate(projects, 1):
        console.print(f"  [cyan]{i}.[/cyan] [bold]{proj['title']}[/bold]")
        console.print(f"      [dim]{proj['desc'][:80]}...[/dim]")
    console.print(f"  [cyan]0.[/cyan] 自定义需求")
    console.print(f"  [cyan]q.[/cyan] 退出")

    choice = Prompt.ask("\n请输入选项", default="1")

    if choice.lower() == "q":
        return None
    if choice == "0":
        return -1

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            return idx
    except ValueError:
        pass

    console.print("[red]无效选项，请重新输入[/red]")
    return show_demo_menu(projects)


def display_result(result: dict):
    """展示 CrewAI 执行结果"""
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]🎉 软件开发团队协作完成！[/bold green]",
        border_style="green",
    ))

    # ── 执行摘要 ──
    process_label = "顺序执行" if result.get("process") == "sequential" else "层级管理"
    summary = Table(title="📊 执行摘要", show_header=True,
                    header_style="bold cyan", box=box.ROUNDED)
    summary.add_column("项目", style="bold yellow")
    summary.add_column("内容")

    summary.add_row("课题", result.get("topic", "N/A"))
    summary.add_row("执行模式", process_label)
    summary.add_row("最终输出长度", f"{len(result.get('result', ''))} 字符")

    # Token 使用
    token_usage = result.get("token_usage", {})
    if token_usage:
        summary.add_row("Token 用量",
                         f"Prompt: {token_usage.get('total_prompt_tokens', 'N/A')} | "
                         f"Completion: {token_usage.get('total_completion_tokens', 'N/A')} | "
                         f"Total: {token_usage.get('total_tokens', 'N/A')}")

    console.print(summary)

    # ── 任务输出摘要 ──
    task_outputs = result.get("task_outputs", [])
    if task_outputs:
        task_table = Table(title="📋 各阶段产出", show_header=True,
                           header_style="bold cyan", box=box.ROUNDED)
        task_table.add_column("阶段", style="bold")
        task_table.add_column("Agent")
        task_table.add_column("输出长度")
        task_table.add_column("开头预览")

        task_names = ["需求分析", "架构设计", "代码实现", "质量测试", "部署方案"]
        for i, task_output in enumerate(task_outputs):
            raw = str(task_output) if task_output else ""
            preview = raw[:80].replace("\n", " ") + "..." if len(raw) > 80 else raw
            stage_name = task_names[i] if i < len(task_names) else f"任务 {i+1}"
            task_table.add_row(
                stage_name,
                task_names[i] if i < len(task_names) else "—",
                f"{len(raw)} 字符",
                preview,
            )

        console.print(task_table)

    # ── 最终交付物 ──
    final_output = result.get("result", "")
    if final_output:
        console.print("\n[bold]📄 最终交付物预览:[/bold]")
        # 截取前 2000 字符展示
        display_text = final_output[:2500]
        if len(final_output) > 2500:
            display_text += "\n\n[dim]...(内容较长，已截断。完整输出可通过 --output 参数保存到文件)[/dim]"
        console.print(Panel(display_text, border_style="green"))


def run_demo_mode(process: str = "sequential"):
    """演示模式：自动运行内置示例"""
    console.print("[bold yellow]\n📢 演示模式启动[/bold yellow]")
    proj = DEMO_PROJECTS[0]
    console.print(f"[cyan]使用内置示例需求:[/cyan] {proj['title']}")
    console.print(f"[dim]{proj['desc']}[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="团队协作中...", total=None)
        result = run_software_team(proj["desc"], process=process)

    display_result(result)


def run_interactive_mode(process: str = "sequential"):
    """交互模式：用户选择或输入需求"""
    while True:
        choice = show_demo_menu(DEMO_PROJECTS)

        if choice is None:
            console.print("[yellow]感谢使用 CrewAI 多 Agent 团队，再见！[/yellow]")
            break

        if choice == -1:
            console.print("\n[bold]请输入你的项目需求（可以详细描述）:[/bold]")
            console.print("[dim]（输入完成后按 Enter，输入空行结束）[/dim]")
            lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
            topic = "\n".join(lines) if lines else ""
            if not topic.strip():
                console.print("[red]需求不能为空[/red]")
                continue
            title = "自定义需求"
        else:
            proj = DEMO_PROJECTS[choice]
            topic = proj["desc"]
            title = proj["title"]

        console.print(f"\n[bold]项目:[/bold] {title}")
        console.print(f"[bold]需求:[/bold] {topic[:200]}{'...' if len(topic) > 200 else ''}")
        console.print(f"[bold]执行模式:[/bold] {process}")

        # 确认
        confirm = Prompt.ask(
            "\n开始团队协作？", choices=["y", "n", "q"], default="y"
        )
        if confirm == "q":
            console.print("[yellow]已取消[/yellow]")
            break
        if confirm != "y":
            continue

        console.print("\n[bold cyan]🚀 启动软件开发团队...[/bold cyan]")
        console.print("[dim]流程: 需求分析 → 架构设计 → 代码实现 → 质量测试 → 部署方案[/dim]\n")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description="Agent 团队协作进行中...", total=None)
                result = run_software_team(topic, process=process)

            display_result(result)

        except Exception as e:
            console.print(f"\n[red]执行出错: {e}[/red]")
            console.print("[yellow]请检查 API Key 配置和网络连接。[/yellow]")

        # 询问是否继续
        again = Prompt.ask("\n是否继续体验？", choices=["y", "n"], default="n")
        if again.lower() != "y":
            console.print("[yellow]感谢使用 CrewAI 多 Agent 团队，再见！[/yellow]")
            break


def main():
    parser = argparse.ArgumentParser(
        description="CrewAI 多 Agent 软件研发团队 Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                                   交互模式
  python main.py --demo                            演示模式
  python main.py --topic "构建一个xxx系统"         直接指定需求
  python main.py --process hierarchical            使用层级管理模式
  python main.py --demo --output result.txt        演示模式 + 保存结果

关于 CrewAI:
  CrewAI 是一个专注于角色扮演 Agent 协作的框架。
  每个 Agent 有明确的 role（角色）、goal（目标）和 backstory（背景故事）。
  支持 Sequential（顺序）和 Hierarchical（层级）两种执行模式。
        """,
    )

    parser.add_argument(
        "--demo", action="store_true",
        help="演示模式（使用内置示例需求）"
    )
    parser.add_argument(
        "--topic", type=str,
        help="直接指定项目需求描述"
    )
    parser.add_argument(
        "--process", type=str, choices=["sequential", "hierarchical"],
        default="sequential",
        help="执行模式: sequential=顺序执行, hierarchical=层级管理 (默认: sequential)"
    )
    parser.add_argument(
        "--output", type=str,
        help="将最终结果保存到指定文件"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="减少终端输出（非交互模式）"
    )

    args = parser.parse_args()

    if not args.quiet:
        print_header()
        print_agents_table()
        print_process_info()

    if args.demo:
        run_demo_mode(process=args.process)
    elif args.topic:
        console.print(f"\n[bold]指定需求:[/bold] {args.topic}")
        console.print(f"[bold]执行模式:[/bold] {args.process}")
        console.print("\n[bold cyan]🚀 启动软件开发团队...[/bold cyan]\n")
        try:
            result = run_software_team(args.topic, process=args.process)
            display_result(result)
        except Exception as e:
            console.print(f"\n[red]执行出错: {e}[/red]")
            sys.exit(1)
    else:
        run_interactive_mode(process=args.process)

    # 保存输出到文件
    if args.output and 'result' in locals():
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["result"])
        console.print(f"\n[green]✅ 结果已保存到: {args.output}[/green]")


if __name__ == "__main__":
    main()
