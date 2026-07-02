"""
AutoGPT 自主 Agent Demo —— 主入口
布道者

用法:
    python main.py                              # 交互模式
    python main.py --demo                       # 演示模式（内置示例目标）
    python main.py --goal "你的目标"             # 直接指定目标
    python main.py --goal "..." --live          # 使用真实 LLM
    python main.py --goal "..." --max-iter 15   # 自定义最大迭代次数
    python main.py --goal "..." --resume        # 从检查点恢复
"""
import sys
import os
import argparse
import textwrap
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

from src.config import AgentConfig, get_config
from src.agent.core import AutoGPTAgent

# ═══════════════════════════════════════════
# 演示目标
# 布道者: 预置的示例目标展示 AutoGPT 的核心能力
# ═══════════════════════════════════════════

DEMO_GOALS = [
    {
        "title": "调研 Python 异步编程最佳实践",
        "goal": "调研 Python asyncio 的最新最佳实践，包括 async/await 的使用模式、常见陷阱和性能优化技巧",
        "icon": "🔍",
    },
    {
        "title": "开发一个 Markdown 解析器",
        "goal": "开发一个简单的 Python Markdown 解析器，支持标题、列表、链接、代码块和表格的解析",
        "icon": "💻",
    },
    {
        "title": "分析新冠后全球远程工作趋势",
        "goal": "调研和分析新冠疫情后全球远程工作的数据趋势，包括各行业的远程工作占比、生产力变化和未来发展预测",
        "icon": "📊",
    },
    {
        "title": "构建 RESTful API 设计规范",
        "goal": "研究 RESTful API 设计的最佳实践，整理出一份包含 URL 规范、状态码使用、认证方案、版本控制等内容的完整设计规范",
        "icon": "📋",
    },
]

WELCOME = r"""
╔══════════════════════════════════════════════════════════════╗
║       🤖 AutoGPT 自主 Agent Demo                           ║
║     Autonomous Task Execution Agent                        ║
║     Plan → Think → Act → Observe → Learn                  ║
╚══════════════════════════════════════════════════════════════╝
"""


def print_header():
    console.print(WELCOME, style="bold cyan")
    console.print(Panel.fit(
        "[bold]AutoGPT[/bold] 是一个自主 AI Agent，能够:\n"
        "  📋 [yellow]规划[/yellow] — 将大目标分解为可执行的子任务\n"
        "  🧠 [yellow]思考[/yellow] — 基于上下文和历史推理下一步行动\n"
        "  ⚡ [yellow]行动[/yellow] — 调用工具（搜索/代码/文件）执行操作\n"
        "  👁️ [yellow]观察[/yellow] — 分析工具返回结果，评估进展\n"
        "  💾 [yellow]学习[/yellow] — 将经验存储到长期记忆\n\n"
        "本 Demo 展示了完整的自主 Agent 循环流程。\n"
        "[dim]布道者出品 | 模拟模式无需 API Key | --live 启用真实 LLM[/dim]",
        title="🤖 什么是 AutoGPT?",
        border_style="blue",
    ))


def print_architecture():
    """输出 AutoGPT 架构说明"""
    arch = Table(title="🏗️ AutoGPT Demo 架构", show_header=True,
                 header_style="bold cyan", box=box.ROUNDED)
    arch.add_column("层级", style="bold", width=12)
    arch.add_column("模块", width=20)
    arch.add_column("职责")
    arch.add_column("关键组件")

    arch.add_row("用户接口", "CLI (main.py)", "接收目标、展示执行过程", "Rich UI / 交互菜单")
    arch.add_row("Agent 核心", "agent/core.py", "自主任务规划与执行循环", "Plan→Think→Act→Observe")
    arch.add_row("工具层", "tools/tools.py", "提供搜索/代码/文件/网页能力", "WebSearch / CodeExec / FileOps")
    arch.add_row("记忆层", "memory/memory.py", "短期+长期+工作记忆管理", "环形缓冲 / ChromaDB / 检查点")
    arch.add_row("配置层", "config.py", "统一配置与 Prompt 模板", "AgentConfig / SYSTEM_PROMPT")
    console.print(arch)


def print_tools_table():
    """输出工具列表"""
    config = get_config()
    tools = Table(title="🔧 可用工具", show_header=True, header_style="bold green", box=box.ROUNDED)
    tools.add_column("工具", style="bold")
    tools.add_column("命令")
    tools.add_column("描述")
    tools.add_column("状态")

    tool_list = [
        ("🌐 网络搜索", "web_search", "搜索互联网获取最新信息", config.allow_search),
        ("📁 文件操作", "file_ops", "读写 workspace 目录中的文件", config.allow_file_ops),
        ("💻 代码执行", "code_exec", "在隔离子进程中执行 Python 代码", config.allow_code_execution),
        ("🌍 网页浏览", "web_browse", "抓取并解析网页内容", config.allow_web_browse),
    ]
    for name, cmd, desc, enabled in tool_list:
        status = "[green]✅ 启用[/green]" if enabled else "[red]❌ 禁用[/red]"
        tools.add_row(name, cmd, desc, status)

    console.print(tools)


def show_demo_menu() -> int:
    """显示演示目标菜单"""
    console.print("\n[bold]请选择演示目标:[/bold]\n")
    for i, item in enumerate(DEMO_GOALS, 1):
        console.print(f"  [cyan]{i}.[/cyan] {item['icon']} [bold]{item['title']}[/bold]")
        console.print(f"      [dim]{item['goal'][:100]}...[/dim]")
    console.print(f"  [cyan]0.[/cyan] 自定义目标")
    console.print(f"  [cyan]q.[/cyan] 退出")

    choice = Prompt.ask("\n请输入选项", default="1")
    if choice.lower() == "q":
        return -1
    if choice == "0":
        return 0
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(DEMO_GOALS):
            return idx + 1  # 1-indexed positive
    except ValueError:
        pass
    return 1


def run_agent_with_display(goal: str, use_live: bool = False, max_iter: int = 10,
                           resume: bool = False):
    """运行 Agent 并美化显示结果"""
    config = get_config()
    config.max_iterations = max_iter

    agent = AutoGPTAgent(config=config)

    # 如果从检查点恢复
    if resume:
        checkpoint_path = os.path.join(config.workspace_dir, f"checkpoint_{hash(goal) % 10000}.json")
        if os.path.exists(checkpoint_path):
            console.print(f"[yellow]📂 从检查点恢复: {checkpoint_path}[/yellow]")
            agent.working.load_checkpoint(checkpoint_path)
        else:
            console.print(f"[yellow]⚠️  检查点不存在，从头开始[/yellow]")

    # 确认执行
    console.print(f"\n[bold cyan]目标:[/bold cyan] {goal}")
    console.print(f"[bold cyan]模式:[/bold cyan] {'🟢 LLM 驱动' if use_live else '🟡 模拟推理'}")

    if not use_live:
        console.print("[dim]提示: 添加 --live 参数可使用真实 LLM 驱动 Agent[/dim]")

    if not Confirm.ask("\n开始执行?", default=True):
        console.print("[yellow]已取消[/yellow]")
        return

    # 执行
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task(description="Agent 执行中...", total=None)
        result = agent.run(goal, use_live_llm=use_live)
        progress.remove_task(task_id)

    # 显示结果
    display_result(result)


def display_result(result: dict):
    """美化显示执行结果"""
    console.print("\n" + "─" * 60)
    console.print(Panel.fit("[bold green]🎉 任务完成！[/bold green]", border_style="green"))

    # 执行统计
    stats = Table(title="📊 执行统计", show_header=False, box=box.SIMPLE)
    stats.add_column("项目", style="bold cyan")
    stats.add_column("值")

    plan = result.get("plan", [])
    log = result.get("execution_log", [])
    stats.add_row("目标", result["goal"][:80])
    stats.add_row("模式", result["mode"])
    stats.add_row("子任务数", str(len(plan)))
    stats.add_row("总迭代数", str(result["iterations"]))
    stats.add_row("操作步骤数", str(len(log)))
    success_count = sum(1 for e in log if "✅" in str(e) or "成功" in str(e))
    stats.add_row("成功操作", f"{success_count}/{len(log)}")
    console.print(stats)

    # 任务计划
    if plan:
        plan_table = Table(title="📋 任务分解", show_header=True, box=box.ROUNDED)
        plan_table.add_column("#", width=4)
        plan_table.add_column("子任务")
        plan_table.add_column("工具")
        plan_table.add_column("完成标准")
        for i, task in enumerate(plan, 1):
            plan_table.add_row(str(i), task.get("title", "N/A")[:40],
                               task.get("tool", ""), task.get("criteria", "")[:50])
        console.print(plan_table)

    # 执行日志摘要
    if log:
        console.print("\n[bold]📝 执行日志摘要:[/bold]")
        for entry in log[-6:]:  # 最近 6 步
            action = entry.get("action", "?")
            result_text = entry.get("result", "")[:100]
            console.print(f"  [cyan]步骤 {entry['step']}[/cyan] | {action} | {result_text}...")

    # 最终总结
    if result.get("summary"):
        console.print("\n[bold]📄 最终总结:[/bold]")
        console.print(Panel(result["summary"][:1500], border_style="green"))


def interactive_mode():
    """交互式模式"""
    while True:
        choice = show_demo_menu()
        if choice == -1:
            console.print("[yellow]感谢使用 AutoGPT Demo！布道者出品[/yellow]")
            break

        if choice == 0:
            console.print("\n[bold]请输入你的目标（可以详细描述）:[/bold]")
            console.print("[dim]（输入完成后按 Enter）[/dim]")
            goal = Prompt.ask("")
            if not goal.strip():
                console.print("[red]目标不能为空[/red]")
                continue
        else:
            item = DEMO_GOALS[choice - 1]
            goal = item["goal"]
            console.print(f"\n[bold]已选择:[/bold] {item['icon']} {item['title']}")

        use_live = Confirm.ask("是否使用真实 LLM?（需要配置 API Key）", default=False)

        max_iter = Prompt.ask("最大迭代次数", default="10")
        try:
            max_iter = int(max_iter)
        except ValueError:
            max_iter = 10

        run_agent_with_display(goal, use_live=use_live, max_iter=max_iter)

        again = Confirm.ask("\n是否继续执行其他目标?", default=False)
        if not again:
            console.print("[yellow]感谢使用 AutoGPT Demo！布道者出品[/yellow]")
            break


def main():
    parser = argparse.ArgumentParser(
        description="AutoGPT 自主 Agent Demo —— 布道者",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              python main.py                                 交互模式
              python main.py --demo                          演示模式（内置示例）
              python main.py --goal "调研 Python 最佳实践"   指定目标（模拟模式）
              python main.py --goal "..." --live             真实 LLM 驱动
              python main.py --goal "..." --max-iter 15      自定义迭代次数
              python main.py --goal "..." --resume           从检查点恢复
        """),
    )
    parser.add_argument("--demo", action="store_true", help="演示模式")
    parser.add_argument("--goal", type=str, help="要执行的目标")
    parser.add_argument("--live", action="store_true", help="使用真实 LLM")
    parser.add_argument("--max-iter", type=int, default=10, help="最大迭代次数")
    parser.add_argument("--resume", action="store_true", help="从检查点恢复")
    parser.add_argument("--list-tools", action="store_true", help="列出可用工具")
    parser.add_argument("--config", action="store_true", help="显示当前配置")

    args = parser.parse_args()
    print_header()

    if args.config:
        config = get_config()
        cfg_table = Table(title="⚙️ 当前配置", show_header=False, box=box.SIMPLE)
        cfg_table.add_column("参数", style="bold cyan")
        cfg_table.add_column("值")
        for field, value in config.__dict__.items():
            cfg_table.add_row(field, str(value))
        console.print(cfg_table)
        return

    if args.list_tools:
        print_tools_table()
        return

    if args.demo:
        print_architecture()
        print_tools_table()
        item = DEMO_GOALS[0]
        console.print(f"\n[bold]演示目标:[/bold] {item['icon']} {item['title']}")
        run_agent_with_display(item["goal"], use_live=args.live, max_iter=args.max_iter)
        return

    if args.goal:
        print_tools_table()
        run_agent_with_display(args.goal, use_live=args.live,
                               max_iter=args.max_iter, resume=args.resume)
        return

    # 默认: 交互模式
    print_architecture()
    print_tools_table()
    interactive_mode()


if __name__ == "__main__":
    main()
