"""
多智能体协作 Demo —— 主入口

一个基于 LangGraph 的多智能体协作系统演示。
五个智能体（研究、分析、写作、审核、汇总）协同完成从调研到交付的全流程。

用法:
    python main.py                          # 交互模式
    python main.py --demo                   # 演示模式（内置示例）
    python main.py --topic "你的课题"       # 直接指定课题
"""

import sys
import argparse
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt

from src.workflow.collaboration_graph import run_collaboration
from src.tools.tools import shared_context

console = Console()

# ──────────────────────────────────────────────
# 示例话题
# ──────────────────────────────────────────────
DEMO_TOPICS = [
    "多智能体系统在智能制造中的应用",
    "大语言模型在企业知识管理中的实践",
    "AI Agent 在自动化运维中的前景",
    "基于 LangChain 的 RAG 系统设计与优化",
]

WELCOME_ART = """
╔═══════════════════════════════════════════════════╗
║          🤖 多智能体协作系统 Demo                 ║
║     Multi-Agent Collaboration Demonstration       ║
╚═══════════════════════════════════════════════════╝
"""


def print_header():
    console.print(WELCOME_ART, style="bold cyan")
    console.print(Panel.fit(
        "本 Demo 展示了 5 个 AI Agent 如何协作完成一项任务：\n"
        "🔍 研究 Agent → 📊 分析 Agent → ✍️ 写作 Agent → 📋 审核 Agent → 📦 汇总 Agent",
        title="🤝 多智能体协作流程",
        border_style="blue",
    ))


def print_agents_table():
    table = Table(title="🤖 Agent 角色说明", show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="bold yellow")
    table.add_column("角色", style="bold green")
    table.add_column("核心职责")
    table.add_column("输出")

    table.add_row("🔍 Research", "研究员", "信息搜集与课题调研", "研究笔记")
    table.add_row("📊 Analysis", "分析师", "深度分析与洞察", "分析报告")
    table.add_row("✍️  Writer", "写作专员", "内容创作", "文章初稿")
    table.add_row("📋 Reviewer", "审核官", "质量审查", "审阅意见")
    table.add_row("📦 Summarizer", "汇总官", "综合产出", "最终交付物")

    console.print(table)


def show_demo_menu(topics: list) -> Optional[int]:
    """显示演示话题菜单"""
    console.print("\n[bold]请选择一个演示话题:[/bold]")
    for i, topic in enumerate(topics, 1):
        console.print(f"  [cyan]{i}.[/cyan] {topic}")
    console.print(f"  [cyan]0.[/cyan] 自定义话题")
    console.print(f"  [cyan]q.[/cyan] 退出")

    choice = Prompt.ask("\n请输入选项", default="1")

    if choice.lower() == "q":
        return None
    if choice == "0":
        return -1

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(topics):
            return idx
    except ValueError:
        pass

    console.print("[red]无效选项，请重新输入[/red]")
    return show_demo_menu(topics)


def show_result(result: dict):
    """展示最终结果"""
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]🎉 多智能体协作完成！[/bold green]",
        border_style="green",
    ))

    # 展示各阶段摘要
    table = Table(title="📊 协作过程统计", show_header=True, header_style="bold cyan")
    table.add_column("阶段", style="bold yellow")
    table.add_column("状态")
    table.add_column("输出长度")

    stages = [
        ("🔍 研究", result.get("research_output", ""), "research_output"),
        ("📊 分析", result.get("analysis_output", ""), "analysis_output"),
        ("✍️  写作", result.get("draft_output", ""), "draft_output"),
        ("📋 审核", result.get("review_output", ""), "review_output"),
        ("📦 汇总", result.get("final_output", ""), "final_output"),
    ]

    for name, output, key in stages:
        status = "✅" if output else "❌"
        length = len(output) if output else 0
        table.add_row(name, status, f"{length} 字符")

    console.print(table)

    # 显示最终交付物
    if result.get("final_output"):
        console.print("\n[bold]📄 最终交付物:[/bold]")
        console.print(Panel(result["final_output"][:2000], border_style="green"))
        if len(result["final_output"]) > 2000:
            console.print("[dim]...(内容较长，已截断)[/dim]")

    # 显示审核反馈摘要
    if result.get("review_output"):
        console.print("\n[bold]📋 审核反馈:[/bold]")
        console.print(Panel(result["review_output"][:1000], border_style="yellow"))
        if len(result["review_output"]) > 1000:
            console.print("[dim]...(内容较长，已截断)[/dim]")


def run_demo_mode():
    """演示模式：自动运行示例"""
    console.print("[bold yellow]\n📢 演示模式启动[/bold yellow]")
    topic = DEMO_TOPICS[0]
    console.print(f"[cyan]使用内置示例话题:[/cyan] {topic}\n")

    result = run_collaboration(topic)
    show_result(result)


def run_interactive_mode():
    """交互模式：用户选择或输入话题"""
    while True:
        choice = show_demo_menu(DEMO_TOPICS)

        if choice is None:
            console.print("[yellow]感谢使用，再见！[/yellow]")
            break

        if choice == -1:
            topic = Prompt.ask("\n请输入要研究的课题")
            if not topic.strip():
                console.print("[red]课题不能为空[/red]")
                continue
        else:
            topic = DEMO_TOPICS[choice]

        style_prompt = Prompt.ask(
            "\n选择文章风格",
            choices=["技术博客", "科普文章", "研究报告", "商业分析"],
            default="技术博客",
        )

        console.print(f"\n[bold]开始协作流程:[/bold]")
        console.print(f"  课题: {topic}")
        console.print(f"  风格: {style_prompt}")
        console.print(f"  流程: 研究 → 分析 → 写作 → 审核 → 汇总")

        result = run_collaboration(topic, style_prompt)
        show_result(result)

        # 询问是否继续
        again = Prompt.ask("\n是否继续体验？", choices=["y", "n"], default="n")
        if again.lower() != "y":
            console.print("[yellow]感谢使用，再见！[/yellow]")
            break


def main():
    parser = argparse.ArgumentParser(
        description="多智能体协作系统 Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                          交互模式
  python main.py --demo                   演示模式
  python main.py --topic "机器学习"      直接指定课题
        """,
    )

    parser.add_argument("--demo", action="store_true", help="演示模式（使用内置示例）")
    parser.add_argument("--topic", type=str, help="直接指定研究课题")

    args = parser.parse_args()

    print_header()
    print_agents_table()

    if args.demo:
        run_demo_mode()
    elif args.topic:
        console.print(f"\n[bold]指定课题:[/bold] {args.topic}")
        style = Prompt.ask("选择文章风格", choices=["技术博客", "科普文章", "研究报告", "商业分析"], default="技术博客")
        result = run_collaboration(args.topic, style)
        show_result(result)
    else:
        run_interactive_mode()


if __name__ == "__main__":
    main()
