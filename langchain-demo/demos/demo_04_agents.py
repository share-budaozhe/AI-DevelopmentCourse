"""
Demo 04 -- Agents: 智能体与工具调用

演示 LangChain Agent 的核心能力:
  - 自定义 Tool 的定义与注册
  - Agent 根据用户问题自主选择工具
  - Agent 的推理-行动-观察 (ReAct) 循环
  - 多工具协同

运行前请设置 .env 文件中的 API Key。
"""

from config import get_llm, check_api_key, print_config

import os as _os
import math
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


# ============================================================
# 定义自定义工具
# ============================================================

@tool
def calculator(expression: str) -> str:
    """执行数学计算。输入一个数学表达式，如 '2 + 3 * 4' 或 'sqrt(16)'。
    支持的函数: sqrt, sin, cos, tan, log, log10, pow, abs, round, pi, e
    """
    try:
        namespace = {
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "log10": math.log10,
            "pow": pow, "abs": abs, "round": round,
            "pi": math.pi, "e": math.e,
        }
        result = eval(expression, {"__builtins__": {}}, namespace)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算出错: {e}"


@tool
def word_length(word: str) -> str:
    """返回一个词或短语的字符数。"""
    return f"'{word}' 有 {len(word)} 个字符"


@tool
def current_time() -> str:
    """获取当前日期和时间。"""
    from datetime import datetime
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def reverse_string(text: str) -> str:
    """反转输入的字符串。"""
    return f"反转结果: {text[::-1]}"


# ============================================================
# 创建 Agent (全局单例)
# ============================================================

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        tools = [calculator, word_length, current_time, reverse_string]
        llm = get_llm()
        _agent = create_react_agent(model=llm, tools=tools)
    return _agent


# ============================================================
# 演示函数
# ============================================================

def demo_single_tool():
    print()
    print("=" * 50)
    print("1. Agent 单工具调用")
    print("=" * 50)
    agent = get_agent()
    questions = [
        "计算 (3 + 5) * 7 的结果",
        "LangChain 这个词有多少个字符?",
        "现在是什么时间?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        result = agent.invoke({"messages": [("user", q)]})
        last_msg = result["messages"][-1]
        print(f"A: {last_msg.content}")


def demo_multi_tool():
    print()
    print("=" * 50)
    print("2. Agent 多工具协同")
    print("=" * 50)
    agent = get_agent()
    q = "请把 'Hello World' 反转，然后告诉我反转后的字符串有多长"
    print(f"\nQ: {q}")
    result = agent.invoke({"messages": [("user", q)]})
    last_msg = result["messages"][-1]
    print(f"A: {last_msg.content}")


def demo_agent_no_tool():
    print()
    print("=" * 50)
    print("3. Agent 无需工具的问答")
    print("=" * 50)
    agent = get_agent()
    q = "Python 是什么时候发明的?"
    print(f"\nQ: {q}")
    result = agent.invoke({"messages": [("user", q)]})
    last_msg = result["messages"][-1]
    print(f"A: {last_msg.content}")


def run_guided():
    demo_single_tool()
    demo_multi_tool()
    demo_agent_no_tool()


# ================================================================
# 交互模式
# ================================================================

def interactive_mode():
    """交互模式: 自由向 Agent 提问,观察工具调用过程"""
    agent = get_agent()

    print()
    print("=" * 50)
    print("  交互模式 -- Agent 智能助手")
    print("=" * 50)
    print("可用工具:")
    print("  - calculator:   数学计算 (如: 计算 2+3*4)")
    print("  - word_length:  字符统计 (如: LangChain 有几个字符)")
    print("  - current_time: 当前时间")
    print("  - reverse_string: 字符串反转")
    print()
    print("提示:")
    print("  - 输入 /trace 查看上轮工具调用详情")
    print("  - 输入 /tools 查看可用工具列表")
    print("  - 输入 /quit 退出")
    print()

    last_result = None

    while True:
        try:
            user_input = input("Q: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("退出交互模式。")
            break
        if user_input == "/tools":
            print("\n可用工具: calculator | word_length | current_time | reverse_string")
            continue

        if user_input == "/trace":
            if last_result is None:
                print("还没有进行过提问。")
                continue
            print("\n--- 上一轮工具调用记录 ---")
            for i, msg in enumerate(last_result["messages"]):
                role = type(msg).__name__
                content = getattr(msg, "content", "")
                tool_calls = getattr(msg, "tool_calls", None)
                if content:
                    print(f"  [{i}] {role}: {str(content)[:100]}")
                if tool_calls:
                    for tc in tool_calls:
                        print(f"       -> 调用工具: {tc.get('name', '?')}({tc.get('args', {})})")
            print("--- 记录结束 ---")
            continue

        # 执行 Agent
        print("(Agent 思考中...)")
        try:
            result = agent.invoke({"messages": [("user", user_input)]})
            last_result = result
            last_msg = result["messages"][-1]

            # 统计工具调用
            tool_calls_count = sum(
                1 for m in result["messages"]
                if hasattr(m, "tool_calls") and m.tool_calls
            )
            if tool_calls_count > 0:
                print(f"[Agent 调用了 {tool_calls_count} 次工具]")

            print(f"A: {last_msg.content}")
        except Exception as e:
            print(f"出错: {e}")


if __name__ == "__main__":
    ok, msg = check_api_key()
    if not ok:
        print(f"错误: {msg}")
        exit(1)

    print_config()
    print()
    print("选择运行模式:")
    print("  [1] 演示模式 -- 自动运行 Agent 示例")
    print("  [2] 交互模式 -- 自由向 Agent 提问,观察工具调用")
    choice = input("请输入 1 或 2 (默认 1): ").strip()

    if choice == "2":
        interactive_mode()
    else:
        run_guided()
