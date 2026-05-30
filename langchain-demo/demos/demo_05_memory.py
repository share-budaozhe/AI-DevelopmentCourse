"""
Demo 05 -- Memory: 对话记忆

演示 LangChain 中的对话记忆管理:
  - 使用 RunnableWithMessageHistory 管理对话历史
  - ChatMessageHistory 在内存中存储历史
  - 多轮对话的上下文保持
  - 多会话隔离

运行前请设置 .env 文件中的 API Key。
"""

from config import get_llm, check_api_key, print_config

import os as _os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage


store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """获取或创建指定会话的历史记录"""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def create_chain_with_memory():
    """创建带记忆的对话链"""
    llm = get_llm(temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的助手。请用中文回答，保持简洁。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    chain = prompt | llm | StrOutputParser()
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    return chain_with_history


# ================================================================
# 演示函数
# ================================================================

def demo_basic_memory():
    print()
    print("=" * 50)
    print("1. 多轮对话记忆")
    print("=" * 50)
    chain = create_chain_with_memory()
    config = {"configurable": {"session_id": "user_001"}}
    conversations = [
        "我叫小明，是一名程序员",
        "我最喜欢 Python",
        "你还记得我叫什么名字吗?",
        "那我喜欢什么编程语言?"
    ]
    for msg in conversations:
        print(f"\nUser: {msg}")
        response = chain.invoke({"input": msg}, config=config)
        print(f"AI:   {response}")


def demo_multi_session():
    print()
    print("=" * 50)
    print("2. 多会话隔离")
    print("=" * 50)
    chain = create_chain_with_memory()

    print("\n-- 会话 A --")
    r = chain.invoke(
        {"input": "我叫 Alice"},
        config={"configurable": {"session_id": "session_a"}}
    )
    print(f"User: 我叫 Alice\nAI:   {r}")

    print("\n-- 会话 B --")
    r = chain.invoke(
        {"input": "我叫 Bob"},
        config={"configurable": {"session_id": "session_b"}}
    )
    print(f"User: 我叫 Bob\nAI:   {r}")

    print("\n-- 回到会话 A --")
    r = chain.invoke(
        {"input": "还记得我叫什么吗?"},
        config={"configurable": {"session_id": "session_a"}}
    )
    print(f"User: 还记得我叫什么吗?\nAI:   {r}")


def demo_history_inspection():
    print()
    print("=" * 50)
    print("3. 查看对话历史")
    print("=" * 50)
    chain = create_chain_with_memory()
    config = {"configurable": {"session_id": "inspect_demo"}}
    chain.invoke({"input": "你好!"}, config=config)
    chain.invoke({"input": "请用三句话介绍 Python"}, config=config)
    chain.invoke({"input": "谢谢!"}, config=config)
    history = store.get("inspect_demo")
    if history:
        print(f"共 {len(history.messages)} 条消息:")
        for i, msg in enumerate(history.messages):
            role = "User" if isinstance(msg, HumanMessage) else "AI"
            print(f"  [{i+1}] {role}: {msg.content[:60]}...")


def run_guided():
    demo_basic_memory()
    demo_multi_session()
    demo_history_inspection()


# ================================================================
# 交互模式
# ================================================================

def interactive_mode():
    """交互模式: 多轮对话,支持会话切换和历史查看"""
    chain = create_chain_with_memory()
    current_session = "default"
    config = {"configurable": {"session_id": current_session}}

    print()
    print("=" * 50)
    print("  交互模式 -- 多轮对话实验")
    print("=" * 50)
    print("当前会话: default")
    print()
    print("命令:")
    print("  /switch <id>  -- 切换到指定会话 (如 /switch alice)")
    print("  /history      -- 查看当前会话的对话历史")
    print("  /clear        -- 清除当前会话历史")
    print("  /sessions     -- 列出所有活跃会话")
    print("  /quit         -- 退出")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("退出交互模式。")
            break

        # 命令处理
        if user_input.startswith("/switch "):
            new_session = user_input[8:].strip()
            if new_session:
                current_session = new_session
                config = {"configurable": {"session_id": current_session}}
                print(f"[已切换到会话: {current_session}]")
            continue

        if user_input == "/sessions":
            active = list(store.keys())
            if active:
                print(f"活跃会话 ({len(active)}): {', '.join(active)}")
            else:
                print("暂无活跃会话。")
            continue

        if user_input == "/history":
            history = store.get(current_session)
            if not history or not history.messages:
                print("当前会话无历史记录。")
                continue
            print(f"\n--- 会话 '{current_session}' 的历史 ({len(history.messages)} 条) ---")
            for i, msg in enumerate(history.messages):
                role = "You" if isinstance(msg, HumanMessage) else "AI"
                content = msg.content
                if len(content) > 80:
                    content = content[:80] + "..."
                print(f"  [{i+1}] {role}: {content}")
            print("--- 结束 ---")
            continue

        if user_input == "/clear":
            store[current_session] = InMemoryChatMessageHistory()
            config = {"configurable": {"session_id": current_session}}
            print(f"[会话 '{current_session}' 历史已清除]")
            continue

        # 正常对话
        try:
            response = chain.invoke({"input": user_input}, config=config)
            print(f"AI:  {response}")
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
    print("  [1] 演示模式 -- 自动运行记忆管理示例")
    print("  [2] 交互模式 -- 多轮对话,支持会话切换")
    choice = input("请输入 1 或 2 (默认 1): ").strip()

    if choice == "2":
        interactive_mode()
    else:
        run_guided()
