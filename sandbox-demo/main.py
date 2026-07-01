"""
安全沙箱应用 Demo —— 主入口

展示三种主流沙箱技术的实际应用：
    1. Subprocess 资源限制沙箱  — OS 级 RLIMIT 隔离
    2. Docker 容器沙箱           — 完整容器隔离（需要 Docker）
    3. RestrictedPython AST 沙箱 — Python 语言级隔离

用法:
    python main.py                          # 交互模式
    python main.py --demo                   # 演示模式（全部三种沙箱）
    python main.py --sandbox subprocess    # 使用 subprocess 沙箱
    python main.py --sandbox docker        # 使用 Docker 沙箱
    python main.py --sandbox restricted    # 使用 RestrictedPython 沙箱
    python main.py --compare               # 三种沙箱对比
    python main.py --policy-check "代码"   # 安全策略检查
"""
import sys
import argparse
import textwrap
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich import box

console = Console()

from src.sandboxes.base import SandboxResult, SandboxConfig
from src.sandboxes.subprocess_sandbox import SubprocessSandbox
from src.sandboxes.docker_sandbox import DockerSandbox
from src.sandboxes.restricted_python import RestrictedPythonSandbox
from src.policies.security_policy import CodeSecurityAnalyzer, SecurityLevel
from src.monitor.resource_monitor import ResourceLimits

WELCOME = r"""
╔══════════════════════════════════════════════════════════════╗
║         🛡️  安全沙箱应用 Demo                              ║
║       Sandbox Application Demonstration                     ║
║       Subprocess | Docker | RestrictedPython                ║
╚══════════════════════════════════════════════════════════════╝
"""

# ── 演示用的测试代码 ──────────────────────────

DEMO_SAFE = textwrap.dedent("""\
# 安全代码示例：计算斐波那契数列
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
""")

DEMO_DANGEROUS_IMPORT = "import os\nos.system('rm -rf /')"


DEMO_DANGEROUS_BUILTIN = "eval('2 + 2')"


DEMO_DANGEROUS_SHELL = "import subprocess\nsubprocess.run(['ls', '-la'])"


DEMO_INFINITE = "while True:\n    pass"


DEMO_MEMORY_BOMB = "[x for x in range(10**9)]"


DEMO_EXAMPLES = [
    ("安全计算（正常通过）", DEMO_SAFE, "safe", "green"),
    ("危险导入（应被拦截）", DEMO_DANGEROUS_IMPORT, "blocked", "red"),
    ("危险内置函数（应被拦截）", DEMO_DANGEROUS_BUILTIN, "blocked", "red"),
    ("Shell 命令注入（应被拦截）", DEMO_DANGEROUS_SHELL, "blocked", "red"),
    ("死循环（应被超时终止）", DEMO_INFINITE, "timeout", "yellow"),
    ("内存炸弹（应被限制）", DEMO_MEMORY_BOMB, "limit", "yellow"),
]


def print_header():
    console.print(WELCOME, style="bold cyan")
    console.print(Panel.fit(
        "本 Demo 展示三种主流沙箱技术在 AI 应用中的实际使用：\n"
        "[yellow]1. Subprocess 资源限制沙箱[/yellow] — 独立子进程 + OS RLIMIT\n"
        "[blue]2. Docker 容器沙箱[/blue] — 完整内核隔离容器\n"
        "[green]3. RestrictedPython AST 沙箱[/green] — Python 语法树级安全控制",
        title="🛡️ 沙箱技术总览",
        border_style="blue",
    ))


def print_sandbox_comparison():
    """输出三种沙箱的详细对比"""
    table = Table(title="🔍 三种沙箱技术对比", show_header=True,
                  header_style="bold cyan", box=box.ROUNDED)
    table.add_column("维度", style="bold", width=16)
    table.add_column("Subprocess 沙箱", width=22)
    table.add_column("Docker 沙箱", width=22)
    table.add_column("RestrictedPython", width=22)

    rows = [
        ("隔离级别", "进程级 🟡", "容器级 🟢", "语言级 🟠"),
        ("启动速度", "~50ms ✅ 快", "~1s ⚠️ 较慢", "< 1ms ✅ 极快"),
        ("内存开销", "~30MB 🟡", "~50MB ⚠️", "~5MB ✅"),
        ("外部依赖", "无 ✅", "Docker ⚠️", "无 ✅"),
        ("资源限制", "RLIMIT ✅", "Cgroup + RLIMIT ✅", "超时 🟡"),
        ("网络安全", "无 🟠", "network_mode=none 🟢", "无 🟠"),
        ("文件系统隔离", "无 🟠", "read_only rootfs 🟢", "builtins 替换 🟡"),
        ("绕过难度", "中等 🟡", "极高 🟢", "中等-高 🟡"),
        ("适用场景", "LLM 生成的简单代码", "不受信任的第三方代码", "教学/公式/规则引擎"),
        ("跨平台", "✅ Windows/Linux/Mac", "⚠️ 需 Docker", "✅ 全平台"),
    ]
    for row in rows:
        table.add_row(*row)

    console.print(table)


def show_sandbox_status():
    """检查各沙箱可用状态"""
    status = Table(title="📊 沙箱可用状态", show_header=True, box=box.ROUNDED)
    status.add_column("沙箱", style="bold")
    status.add_column("状态")
    status.add_column("说明")

    for sandbox_cls in [SubprocessSandbox, DockerSandbox, RestrictedPythonSandbox]:
        available = sandbox_cls.is_available()
        icon = "✅ 可用" if available else "❌ 不可用"
        note = {
            SubprocessSandbox: "纯 Python，无需额外依赖",
            DockerSandbox: "需要 Docker Desktop 或 Docker Engine",
            RestrictedPythonSandbox: "纯 Python，无需额外依赖",
        }[sandbox_cls]
        status.add_row(sandbox_cls.name(), icon, note)

    console.print(status)


def run_demo(sandbox_type: str = "all"):
    """
    运行完整演示：对每种沙箱依次测试安全/危险/超时/炸弹代码
    """
    sandboxes = []

    if sandbox_type in ("all", "subprocess"):
        sandboxes.append(("Subprocess 资源限制沙箱", SubprocessSandbox()))
    if sandbox_type in ("all", "docker"):
        if DockerSandbox.is_available():
            sandboxes.append(("Docker 容器沙箱", DockerSandbox()))
        else:
            console.print("[yellow]⚠ Docker 不可用，跳过 Docker 沙箱演示[/yellow]")
    if sandbox_type in ("all", "restricted"):
        sandboxes.append(("RestrictedPython AST 沙箱", RestrictedPythonSandbox()))

    if not sandboxes:
        console.print("[red]没有可用的沙箱[/red]")
        return

    for sandbox_name, sandbox in sandboxes:
        console.print(f"\n[bold cyan]{'═' * 60}")
        console.print(f"  📦 {sandbox_name}")
        console.print(f"     隔离级别: {sandbox.isolation_level()}")
        console.print(f"{'═' * 60}[/bold cyan]")

        results_table = Table(title=f"测试结果 — {sandbox_name}",
                              show_header=True, box=box.ROUNDED)
        results_table.add_column("测试用例", max_width=20)
        results_table.add_column("预期结果")
        results_table.add_column("实际结果")
        results_table.add_column("耗时")
        results_table.add_column("详情")

        for name, code, expected, _ in DEMO_EXAMPLES:
            config = SandboxConfig(timeout_seconds=3, memory_limit_mb=256)
            sandbox.config = config
            result = sandbox.execute(code)

            if expected == "safe":
                status = "[green]✅ 通过[/green]" if result.success else "[red]❌ 失败[/red]"
            elif expected == "blocked":
                status = "[green]✅ 已拦截[/green]" if not result.success else "[red]❌ 未拦截[/red]"
            elif expected == "timeout":
                status = "[green]✅ 已超时终止[/green]" if not result.success else "[yellow]⚠ 未超时[/yellow]"
            elif expected == "limit":
                status = "[green]✅ 已限制[/green]" if not result.success else "[yellow]⚠ 未限制[/yellow]"
            else:
                status = f"完成 (exit={result.exit_code})"

            detail = (result.error or "")[:50]
            if not detail and result.stdout:
                detail = f"stdout: {len(result.stdout)} 字符"

            results_table.add_row(
                name,
                expected,
                status,
                f"{result.execution_time_ms:.0f}ms",
                detail,
            )

        console.print(results_table)

        # 显示审计日志概要
        if sandbox.audit_log:
            console.print(f"  [dim]审计记录: {len(sandbox.audit_log)} 条[/dim]")


def policy_check_mode(code: str):
    """安全策略检查模式 —— 仅分析代码不执行"""
    console.print("\n[bold]📋 安全策略分析[/bold]")
    console.print(Syntax(code, "python", theme="monokai"))

    for level in SecurityLevel:
        analyzer = CodeSecurityAnalyzer(level=level)
        result = analyzer.analyze(code)
        color = "green" if result["safe"] else "red"
        console.print(f"\n[bold]{level.name}[/bold]: "
                      f"[{color}]安全={result['safe']} 风险评分={result['risk_score']}/100[/{color}]")
        for f in result["findings"]:
            console.print(f"  [{color}]• [{f['level']}] {f['message']}[/{color}]")


def interactive_mode():
    """交互模式：选择沙箱 → 输入代码 → 查看结果"""
    while True:
        console.print("\n[bold cyan]选择沙箱类型:[/bold cyan]")
        console.print("  [cyan]1.[/cyan] Subprocess 资源限制沙箱")
        console.print("  [cyan]2.[/cyan] Docker 容器沙箱")
        console.print("  [cyan]3.[/cyan] RestrictedPython AST 沙箱")
        console.print("  [cyan]4.[/cyan] 安全策略分析（仅检查不执行）")
        console.print("  [cyan]c.[/cyan] 三种沙箱对比")
        console.print("  [cyan]d.[/cyan] 完整演示")
        console.print("  [cyan]q.[/cyan] 退出")

        choice = Prompt.ask("\n请输入选项", default="1")

        if choice.lower() == "q":
            console.print("[yellow]感谢使用安全沙箱 Demo！[/yellow]")
            break
        elif choice.lower() == "c":
            print_sandbox_comparison()
            show_sandbox_status()
            continue
        elif choice.lower() == "d":
            run_demo("all")
            continue
        elif choice == "4":
            code = prompt_code_input()
            if code:
                policy_check_mode(code)
            continue

        # 创建沙箱
        sandbox_map = {
            "1": ("Subprocess", SubprocessSandbox()),
            "2": ("Docker", DockerSandbox()) if DockerSandbox.is_available() else None,
            "3": ("RestrictedPython", RestrictedPythonSandbox()),
        }

        if choice not in sandbox_map or sandbox_map[choice] is None:
            if choice == "2":
                console.print("[red]Docker 不可用。请安装 Docker Desktop 后重试。[/red]")
            else:
                console.print("[red]无效选项[/red]")
            continue

        sandbox_name, sandbox = sandbox_map[choice]
        console.print(f"\n[bold]当前沙箱: [cyan]{sandbox_name}[/cyan] "
                      f"(隔离等级: {sandbox.isolation_level()})[/bold]")

        # 输入代码
        code = prompt_code_input()
        if not code:
            continue

        # 执行
        console.print(f"\n[dim]正在 {sandbox_name} 中执行代码...[/dim]")
        result = sandbox.execute(code)

        # 显示结果
        console.print("\n" + "─" * 50)
        console.print("[bold]📊 执行结果[/bold]")
        result_table = Table(show_header=False, box=box.SIMPLE)
        result_table.add_column("项目", style="bold cyan")
        result_table.add_column("值")

        status_text = "[green]✅ 成功[/green]" if result.success else "[red]❌ 失败[/red]"
        result_table.add_row("状态", status_text)
        result_table.add_row("耗时", f"{result.execution_time_ms:.1f}ms")
        result_table.add_row("退出码", str(result.exit_code))

        if result.error:
            result_table.add_row("错误", result.error[:200])
        if result.stdout:
            output_preview = result.stdout[:500]
            if len(result.stdout) > 500:
                output_preview += "\n...(截断)"
            result_table.add_row("输出", output_preview)

        if result.audit_id:
            result_table.add_row("审计 ID", result.audit_id)

        console.print(result_table)


def prompt_code_input() -> Optional[str]:
    """交互式代码输入（支持多行）"""
    console.print("\n[bold]请输入要执行的 Python 代码:[/bold]")
    console.print("[dim]（输入代码后按 Enter，单独一行输入 'END' 完成）[/dim]")
    console.print("[dim]（输入 'demo' 使用演示代码）[/dim]")

    first_line = Prompt.ask("", default="demo")
    if first_line.strip().lower() == "demo":
        return DEMO_SAFE
    if first_line.strip().lower() == "quit":
        return None

    lines = [first_line]
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="安全沙箱应用 Demo — Subprocess | Docker | RestrictedPython",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              python main.py                          交互模式
              python main.py --demo                   完整演示
              python main.py --compare                沙箱对比
              python main.py --sandbox subprocess    使用 subprocess 沙箱
              python main.py --policy-check "eval(...)"  安全策略检查
        """),
    )
    parser.add_argument("--demo", action="store_true", help="完整演示三种沙箱")
    parser.add_argument("--compare", action="store_true", help="沙箱技术对比")
    parser.add_argument("--sandbox", choices=["subprocess", "docker", "restricted"],
                        help="直接执行指定沙箱 (交互输入代码)")
    parser.add_argument("--policy-check", type=str, help="对指定代码进行安全策略分析")
    parser.add_argument("--code", type=str, help="要执行的代码")
    parser.add_argument("--timeout", type=int, default=10, help="超时时间(秒)，默认 10")
    parser.add_argument("--memory", type=int, default=256, help="内存限制(MB)，默认 256")

    args = parser.parse_args()
    print_header()

    if args.compare:
        print_sandbox_comparison()
        show_sandbox_status()
        return

    if args.policy_check:
        console.print(f"\n[bold]检查模式[/bold]: 仅做安全分析，不执行代码")
        policy_check_mode(args.policy_check)
        return

    if args.demo:
        print_sandbox_comparison()
        show_sandbox_status()
        run_demo("all")
        return

    if args.sandbox and args.code:
        # 直接执行模式
        sandbox_map = {
            "subprocess": SubprocessSandbox(),
            "docker": DockerSandbox(),
            "restricted": RestrictedPythonSandbox(),
        }
        sandbox = sandbox_map[args.sandbox]
        sandbox.config = SandboxConfig(timeout_seconds=args.timeout,
                                        memory_limit_mb=args.memory)
        result = sandbox.execute(args.code)
        console.print(f"\n[bold]结果:[/bold] {'✅ 成功' if result.success else '❌ 失败'}")
        if result.error:
            console.print(f"[red]{result.error}[/red]")
        if result.stdout:
            console.print(result.stdout[:1000])
        return

    if args.sandbox:
        # 交互输入代码后通过指定沙箱执行
        sandbox_map = {
            "subprocess": SubprocessSandbox(),
            "docker": DockerSandbox(),
            "restricted": RestrictedPythonSandbox(),
        }
        sandbox = sandbox_map[args.sandbox]
        sandbox.config = SandboxConfig(timeout_seconds=args.timeout,
                                        memory_limit_mb=args.memory)
        console.print(f"\n[bold]沙箱: [cyan]{sandbox.name()}[/cyan][/bold]")
        code = prompt_code_input()
        if code:
            result = sandbox.execute(code)
            console.print(f"\n[bold]结果:[/bold] {'✅ 成功' if result.success else '❌ 失败'}")
            if result.error:
                console.print(f"[red]{result.error}[/red]")
            if result.stdout:
                console.print(result.stdout[:1000])
        return

    # 默认：交互模式
    show_sandbox_status()
    interactive_mode()


if __name__ == "__main__":
    main()
