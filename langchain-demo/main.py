"""
LangChain 学习 Demo -- 总入口

逐个运行 5 个 Demo，覆盖 LangChain 的核心应用场景:
  1. 基础: 模型调用、Prompt 模板、Output Parser
  2. Chains: LCEL 链式编排 (并行/透传/Lambda)
  3. RAG: 检索增强生成 (文档加载/向量存储/检索链)
  4. Agents: 智能体与工具调用
  5. Memory: 对话记忆管理

支持 OpenAI 和 DeepSeek 两种后端 -- 在 .env 中设置 LLM_PROVIDER 切换。

使用方式:
  python main.py                    # 菜单选择
  python main.py --guided           # 演示模式: 运行所有 Demo
  python main.py --guided 1 3       # 演示模式: 运行 Demo 01, 03
  python main.py --interactive 1    # 交互模式: 运行 Demo 01
  python main.py --interactive 3    # 交互模式: 运行 Demo 03 (RAG 问答)
"""

import os as _os
import sys
import importlib.util

sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "demos"))

from config import print_config, check_api_key

DEMOS = {
    "1": ("demo_01_basics",   "基础: 模型调用 / Prompt / OutputParser"),
    "2": ("demo_02_chains",   "Chains: LCEL 链式编排"),
    "3": ("demo_03_rag",      "RAG: 检索增强生成"),
    "4": ("demo_04_agents",   "Agents: 智能体与工具"),
    "5": ("demo_05_memory",   "Memory: 对话记忆"),
}


def run_demo_guided(num: str):
    """以演示模式运行单个 Demo"""
    if num not in DEMOS:
        print(f"未知的 Demo 编号: {num}")
        return

    module_name, description = DEMOS[num]
    print()
    print("*" * 60)
    print(f"  Demo {num} -- {description} (演示模式)")
    print("*" * 60)

    module = load_module(module_name)
    if hasattr(module, "run_guided"):
        module.run_guided()
    else:
        print(f"  (Demo {num} 暂无演示模式)")


def run_demo_interactive(num: str):
    """以交互模式运行单个 Demo"""
    if num not in DEMOS:
        print(f"未知的 Demo 编号: {num}")
        return

    module_name, description = DEMOS[num]
    print()
    print("*" * 60)
    print(f"  Demo {num} -- {description} (交互模式)")
    print("*" * 60)

    module = load_module(module_name)
    if hasattr(module, "interactive_mode"):
        module.interactive_mode()
    else:
        print(f"  (Demo {num} 暂无交互模式)")


def load_module(module_name: str):
    """动态加载 demo 模块"""
    spec = importlib.util.spec_from_file_location(
        module_name,
        _os.path.join(_os.path.dirname(__file__), "demos", f"{module_name}.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def show_menu():
    """显示主菜单 (未指定参数时)"""
    print()
    print("=" * 50)
    print("  选择运行模式:")
    print("=" * 50)
    print()
    for num, (_, desc) in DEMOS.items():
        print(f"  {num}      -- {desc}")
    print()
    print("  g      -- 演示模式: 运行所有 Demo")
    print("  g 1 3  -- 演示模式: 运行指定 Demo")
    print("  i 1    -- 交互模式: Demo 01 互动问答")
    print("  i 3    -- 交互模式: Demo 03 RAG 问答")
    print("  q      -- 退出")
    print()

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not cmd:
            continue
        if cmd.lower() in ("q", "quit", "exit"):
            print("再见!")
            break

        parts = cmd.split()
        if not parts:
            continue

        # g / g 1 3
        if parts[0].lower() == "g":
            nums = parts[1:] if len(parts) > 1 else list(DEMOS.keys())
            for n in nums:
                try:
                    run_demo_guided(n)
                except Exception as e:
                    print(f"\nDemo {n} 运行出错: {e}")
                    import traceback
                    traceback.print_exc()
            break

        # i 1 / i 3
        elif parts[0].lower() == "i":
            nums = parts[1:] if len(parts) > 1 else []
            if not nums:
                print("请指定 Demo 编号，如: i 1")
                continue
            for n in nums:
                try:
                    run_demo_interactive(n)
                except Exception as e:
                    print(f"\nDemo {n} 交互模式出错: {e}")
                    import traceback
                    traceback.print_exc()
            break

        # 直接输入数字
        elif parts[0] in DEMOS:
            nums = [p for p in parts if p in DEMOS]
            for n in nums:
                try:
                    run_demo_guided(n)
                except Exception as e:
                    print(f"\nDemo {n} 运行出错: {e}")
                    import traceback
                    traceback.print_exc()
            break

        else:
            print("未知命令。输入数字(1-5)、g(演示)、i N(交互)、q(退出)")


if __name__ == "__main__":
    ok, msg = check_api_key()
    if not ok:
        print(f"错误: {msg}")
        exit(1)

    print("=" * 60)
    print("  LangChain 学习 Demo")
    print_config()
    print("=" * 60)

    # 解析命令行参数
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if "--interactive" in sys.argv or "-i" in sys.argv:
        # 交互模式
        nums = args if args else None
        if nums:
            for n in nums:
                run_demo_interactive(n)
        else:
            print("请指定 Demo 编号，如: python main.py --interactive 1")
    elif "--guided" in sys.argv or "-g" in sys.argv:
        # 演示模式
        nums = args if args else list(DEMOS.keys())
        for n in nums:
            run_demo_guided(n)
    elif args:
        # 默认为演示模式
        for n in args:
            run_demo_guided(n)
    else:
        # 无参数: 显示菜单
        show_menu()

    print()
    print("=" * 60)
    print("  运行完毕!")
    print("=" * 60)
