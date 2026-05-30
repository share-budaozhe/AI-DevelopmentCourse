"""
Demo 02 -- Chains: LCEL 链式编排

演示 LangChain Expression Language (LCEL) 的核心能力:
  - 管式链 (|) 串联 Runnable
  - RunnableParallel 并行执行多个分支
  - RunnablePassthrough 透传数据
  - RunnableLambda 嵌入自定义函数
  - itemgetter 从字典中提取字段

运行前请设置 .env 文件中的 API Key。
"""

from config import get_llm, check_api_key, print_config

import os as _os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from operator import itemgetter


# ================================================================
# 演示函数
# ================================================================

def demo_simple_chain():
    print()
    print("=" * 50)
    print("1. 最简 LCEL 链")
    print("=" * 50)
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(
        "将以下文本翻译成{language}:\n{text}"
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"language": "日文", "text": "你好，世界"})
    print(f"结果: {result}")


def demo_runnable_parallel():
    print()
    print("=" * 50)
    print("2. RunnableParallel -- 并行执行")
    print("=" * 50)
    llm = get_llm()
    joke_chain = (
        ChatPromptTemplate.from_template("讲一个关于{topic}的冷笑话")
        | llm | StrOutputParser()
    )
    fact_chain = (
        ChatPromptTemplate.from_template("用一句话介绍关于{topic}的冷知识")
        | llm | StrOutputParser()
    )
    parallel_chain = RunnableParallel(joke=joke_chain, fact=fact_chain)
    result = parallel_chain.invoke({"topic": "编程"})
    print(f"笑话: {result['joke']}")
    print(f"冷知识: {result['fact']}")


def demo_runnable_passthrough():
    print()
    print("=" * 50)
    print("3. RunnablePassthrough -- 透传 + 增强")
    print("=" * 50)
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(
        "根据以下内容写一个{style}总结:\n{text}"
    )
    chain = RunnablePassthrough.assign(
        summary=prompt | llm | StrOutputParser()
    )
    result = chain.invoke({
        "text": "Python 是一种解释型、面向对象的高级编程语言，"
                "具有动态语义，适合快速应用开发。",
        "style": "一句话"
    })
    print(f"原文: {result['text']}")
    print(f"摘要: {result['summary']}")


def demo_itemgetter():
    print()
    print("=" * 50)
    print("4. itemgetter -- 字段提取")
    print("=" * 50)
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(
        "请用{target_lang}介绍{word}的意思"
    )
    chain = (
        {"word": itemgetter("word"), "target_lang": itemgetter("target_lang")}
        | prompt | llm | StrOutputParser()
    )
    result = chain.invoke({
        "word": "Machine Learning",
        "target_lang": "中文",
        "extra_field": "这个字段会被忽略"
    })
    print(f"结果: {result}")


def demo_runnable_lambda():
    print()
    print("=" * 50)
    print("5. RunnableLambda -- 自定义处理函数")
    print("=" * 50)

    def word_count(text: str) -> dict:
        return {"word_count": len(text), "text": text}

    def format_output(data: dict) -> str:
        return f"原文共 {data['word_count']} 字: {data['text'][:50]}..."

    chain = RunnableLambda(word_count) | RunnableLambda(format_output)
    result = chain.invoke(
        "LangChain 是一个强大的 LLM 应用开发框架，"
        "它提供了丰富的抽象来简化开发流程。"
    )
    print(result)


def run_guided():
    demo_simple_chain()
    demo_runnable_parallel()
    demo_runnable_passthrough()
    demo_itemgetter()
    demo_runnable_lambda()


# ================================================================
# 交互模式
# ================================================================

def interactive_mode():
    """交互模式: 选择链条类型,自定义输入"""
    llm = get_llm()

    print()
    print("=" * 50)
    print("  交互模式 -- 链条实验台")
    print("=" * 50)
    print("功能菜单:")
    print("  /trans   -- 翻译链  (输入: 目标语言|文本)")
    print("  /joke    -- 笑话+冷知识并行链 (输入: 主题)")
    print("  /summary -- 摘要链  (输入: 总结风格|文本)")
    print("  /explain -- 词汇解释 (输入: 解释语言|词汇)")
    print("  /count   -- 字数统计 (输入: 文本)")
    print("  /quit    -- 退出")
    print()

    mode = "trans"

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("退出交互模式。")
            break

        # 切换模式
        if user_input.startswith("/"):
            mode_name = user_input[1:].strip()
            if mode_name in ("trans", "joke", "summary", "explain", "count"):
                mode = mode_name
                names = {"trans": "翻译", "joke": "笑话+冷知识", "summary": "摘要",
                         "explain": "词汇解释", "count": "字数统计"}
                print(f"[已切换到 {names.get(mode, mode)} 模式]")
            else:
                print("可用: /trans /joke /summary /explain /count")
            continue

        # 执行对应链
        if mode == "trans":
            parts = user_input.split("|", 1)
            if len(parts) < 2:
                print("格式: 目标语言|文本")
                continue
            lang, text = parts[0].strip(), parts[1].strip()
            prompt = ChatPromptTemplate.from_template("将以下文本翻译成{language}:\n{text}")
            chain = prompt | llm | StrOutputParser()
            r = chain.invoke({"language": lang, "text": text})
            print(f"翻译 ({lang}): {r}")

        elif mode == "joke":
            joke_c = ChatPromptTemplate.from_template("讲一个关于{topic}的冷笑话") | llm | StrOutputParser()
            fact_c = ChatPromptTemplate.from_template("用一句话介绍关于{topic}的冷知识") | llm | StrOutputParser()
            chain = RunnableParallel(joke=joke_c, fact=fact_c)
            r = chain.invoke({"topic": user_input})
            print(f"笑话: {r['joke']}\n冷知识: {r['fact']}")

        elif mode == "summary":
            parts = user_input.split("|", 1)
            style = "一段话"
            if len(parts) >= 2:
                style, text = parts[0].strip(), parts[1].strip()
            else:
                text = parts[0].strip()
            prompt = ChatPromptTemplate.from_template("根据以下内容写一个{style}总结:\n{text}")
            chain = RunnablePassthrough.assign(summary=prompt | llm | StrOutputParser())
            r = chain.invoke({"text": text, "style": style})
            print(f"摘要 ({style}): {r['summary']}")

        elif mode == "explain":
            parts = user_input.split("|", 1)
            if len(parts) < 2:
                lang, word = "中文", parts[0].strip()
            else:
                lang, word = parts[0].strip(), parts[1].strip()
            prompt = ChatPromptTemplate.from_template("请用{target_lang}介绍{word}的意思")
            chain = (
                {"word": itemgetter("word"), "target_lang": itemgetter("target_lang")}
                | prompt | llm | StrOutputParser()
            )
            r = chain.invoke({"word": word, "target_lang": lang})
            print(f"解释 ({lang}): {r}")

        elif mode == "count":
            def wc(t):
                return {"len": len(t), "text": t}
            def fmt(d):
                return f"共 {d['len']} 字: {d['text'][:60]}..."
            chain = RunnableLambda(wc) | RunnableLambda(fmt)
            print(chain.invoke(user_input))


if __name__ == "__main__":
    ok, msg = check_api_key()
    if not ok:
        print(f"错误: {msg}")
        exit(1)

    print_config()
    print()
    print("选择运行模式:")
    print("  [1] 演示模式 -- 自动运行所有链条示例")
    print("  [2] 交互模式 -- 选择链条类型,自定义输入实验")
    choice = input("请输入 1 或 2 (默认 1): ").strip()

    if choice == "2":
        interactive_mode()
    else:
        run_guided()
