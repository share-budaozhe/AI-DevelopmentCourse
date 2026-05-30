"""
Demo 01 -- 基础: 模型调用、Prompt 模板、Output Parser

演示 LangChain 最核心的三件套:
  - Chat Model: 与 LLM 对话模型交互 (支持 OpenAI / DeepSeek)
  - Prompt Template: 构建结构化提示词
  - Output Parser: 将模型原始输出解析为结构化数据

运行前请设置 .env 文件中的 API Key。
"""

from config import get_llm, check_api_key, print_config

import os as _os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser


# ================================================================
# 演示函数 (引导式教学)
# ================================================================

def demo_simple_call():
    print()
    print("=" * 50)
    print("1. 直接调用 Chat Model")
    print("=" * 50)
    llm = get_llm(temperature=0.7)
    response = llm.invoke("用一句话介绍 Python 语言")
    print(f"回答: {response.content}")


def demo_prompt_template():
    print()
    print("=" * 50)
    print("2. ChatPromptTemplate")
    print("=" * 50)
    template = ChatPromptTemplate.from_messages([
        ("system", "你是一位{role}，请用{style}的风格回答问题。"),
        ("human", "{question}")
    ])
    prompt_value = template.invoke({
        "role": "Python 专家",
        "style": "简洁明了",
        "question": "什么是装饰器？"
    })
    print("渲染后的 Prompt:")
    print(prompt_value.to_string())
    print()
    llm = get_llm(temperature=0)
    response = llm.invoke(prompt_value)
    print(f"回答: {response.content}")


def demo_output_parser():
    print()
    print("=" * 50)
    print("3. 链式调用: Prompt -> Model -> OutputParser")
    print("=" * 50)
    parser = CommaSeparatedListOutputParser()
    template = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个列出编程概念的工具。只返回逗号分隔的列表，不要额外解释。\n{format_instructions}"),
        ("human", "列出 5 个 Python 的{category}")
    ])
    llm = get_llm(temperature=0)
    chain = template | llm | parser
    result = chain.invoke({
        "category": "内置数据结构",
        "format_instructions": parser.get_format_instructions()
    })
    print(f"结构化结果: {result}")


def demo_chain_vs_direct():
    print()
    print("=" * 50)
    print("4. LCEL 链对比手动调用")
    print("=" * 50)
    llm = get_llm(temperature=0)
    parser = StrOutputParser()
    template = ChatPromptTemplate.from_template(
        "将以下文本翻译成{language}:\n{text}"
    )
    chain = template | llm | parser
    result = chain.invoke({
        "language": "英文",
        "text": "人工智能正在改变世界"
    })
    print(f"翻译结果: {result}")


def run_guided():
    """引导式演示: 依次运行所有示例"""
    demo_simple_call()
    demo_prompt_template()
    demo_output_parser()
    demo_chain_vs_direct()


# ================================================================
# 交互模式
# ================================================================

def interactive_mode():
    """交互模式: 用户自由提问并观察 LLM 的响应"""
    print()
    print("=" * 50)
    print("  交互模式 -- Model I/O 实验")
    print("=" * 50)
    print("你可以:")
    print("  1) 自由提问 -- 直接向 LLM 提问")
    print("  2) 角色扮演 -- 指定角色和风格后提问")
    print("  3) 翻译     -- 输入文本和目标语言")
    print()
    print("输入 /menu 切换功能, /quit 退出")

    llm = get_llm(temperature=0.7)
    mode = "qa"

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("退出交互模式。")
            break
        if user_input == "/menu":
            print("\n功能: /qa (自由提问)  /role (角色扮演)  /trans (翻译)")
            continue
        if user_input == "/qa":
            mode = "qa"
            print("[已切换到自由提问模式]")
            continue
        if user_input == "/role":
            mode = "role"
            print("[已切换到角色扮演模式] 输入格式: 角色|风格|问题")
            print("  例如: Python专家|简洁|什么是装饰器")
            continue
        if user_input == "/trans":
            mode = "trans"
            print("[已切换到翻译模式] 输入格式: 目标语言|文本")
            print("  例如: 英文|人工智能正在改变世界")
            continue

        # 根据模式处理
        if mode == "qa":
            response = llm.invoke(user_input)
            print(f"AI: {response.content}")

        elif mode == "role":
            parts = user_input.split("|", 2)
            if len(parts) < 3:
                print("格式: 角色|风格|问题 (用 | 分隔)")
                continue
            role, style, question = parts[0].strip(), parts[1].strip(), parts[2].strip()
            template = ChatPromptTemplate.from_messages([
                ("system", f"你是一位{role}，请用{style}的风格回答问题。"),
                ("human", "{question}")
            ])
            chain = template | llm | StrOutputParser()
            response = chain.invoke({"role": role, "style": style, "question": question})
            print(f"AI ({role}, {style}): {response}")

        elif mode == "trans":
            parts = user_input.split("|", 1)
            if len(parts) < 2:
                print("格式: 目标语言|文本 (用 | 分隔)")
                continue
            lang, text = parts[0].strip(), parts[1].strip()
            template = ChatPromptTemplate.from_template(
                "将以下文本翻译成{language}:\n{text}"
            )
            chain = template | llm | StrOutputParser()
            response = chain.invoke({"language": lang, "text": text})
            print(f"翻译 ({lang}): {response}")


if __name__ == "__main__":
    ok, msg = check_api_key()
    if not ok:
        print(f"错误: {msg}")
        exit(1)

    print_config()
    print()
    print("选择运行模式:")
    print("  [1] 演示模式 -- 自动运行所有示例,观察效果")
    print("  [2] 交互模式 -- 自由提问,动手实验")
    choice = input("请输入 1 或 2 (默认 1): ").strip()

    if choice == "2":
        interactive_mode()
    else:
        run_guided()
