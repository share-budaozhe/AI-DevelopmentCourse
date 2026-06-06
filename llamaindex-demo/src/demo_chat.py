"""
═══════════════════════════════════════════════════════════════
  💬 LlamaIndex 学习教程 — src/demo_chat.py
  实验 5：对话引擎深入实验
═══════════════════════════════════════════════════════════════

核心知识点：
- ChatEngine：带记忆的多轮对话接口
- ChatMemory：对话历史管理
- CondenseQuestionChatEngine：压缩问题模式
- ContextChatEngine：上下文模式
"""
from llama_index.core import (
    VectorStoreIndex, Settings, MockEmbedding,
)
from llama_index.core.memory import ChatMemoryBuffer
from sample_data import DEMO_DOCUMENTS


def setup():
    Settings.embed_model = MockEmbedding(embed_dim=384)


def experiment_chat_modes():
    """🔬 实验 5.1：对话引擎模式对比

    知识点：
    - CondenseQuestionChatEngine：将对话历史压缩为独立问题再检索
    - ContextChatEngine：每次都使用完整上下文
    - SimpleChatEngine：无检索，纯对话
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 5.1：对话引擎模式对比")
    print(f"{'='*60}")

    modes_table = """
  三种对话引擎模式：

  ┌──────────────────────────┬─────────────────────────────────────────┐
  │ CondenseQuestionChatEngine │ 将聊天历史+当前问题压缩成独立问题      │
  │                            │ → 用压缩后的问题检索                    │
  │                            │ → 基于检索结果 + 历史生成回答           │
  │                            │ 优点：节省 token，检索精准              │
  ├──────────────────────────┼─────────────────────────────────────────┤
  │ ContextChatEngine         │ 将检索结果 + 聊天历史一起发给 LLM       │
  │                            │ 优点：上下文完整，回答连贯              │
  │                            │ 缺点：token 消耗大                     │
  ├──────────────────────────┼─────────────────────────────────────────┤
  │ SimpleChatEngine          │ 纯对话，不检索文档                      │
  │                            │ 优点：简单直接，响应快                  │
  │                            │ 适用：不需要知识库的聊天场景            │
  └──────────────────────────┴─────────────────────────────────────────┘
"""
    print(modes_table)


def experiment_chat_memory():
    """🔬 实验 5.2：对话记忆管理

    知识点：
    - ChatMemoryBuffer：存储对话历史
    - token_limit：控制记忆的 token 上限
    - 记忆管理策略：最近 N 条 vs 摘要压缩
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 5.2：对话记忆管理")
    print(f"{'='*60}")

    # 演示 ChatMemoryBuffer
    memory = ChatMemoryBuffer.from_defaults(token_limit=2000)

    print(f"\n  ChatMemoryBuffer 配置：")
    print(f"    token_limit: 2000")
    print(f"    当前消息数: {len(memory.get_all())}")

    # 模拟添加对话
    print(f"\n  模拟对话流程：")
    messages = [
        ("user", "什么是 LlamaIndex？"),
        ("assistant", "LlamaIndex 是一个数据框架，用于连接 LLM 与外部数据..."),
        ("user", "它和 LangChain 有什么区别？"),
        ("assistant", "LlamaIndex 专注于数据索引和检索，而 LangChain 是通用框架..."),
    ]

    for role, content in messages:
        memory.put(role, content)
        print(f"    [{role}] {content[:40]}...")

    print(f"\n  对话后：")
    print(f"    当前消息数: {len(memory.get_all())}")

    history = memory.get()
    print(f"    获取的历史（给 LLM 用）: {history[:100]}...")


def experiment_chat_workflow():
    """🔬 实验 5.3：对话引擎完整工作流

    知识点：
    - 多轮对话中如何维护检索上下文
    - Condense 问题如何帮助精准检索
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 5.3：对话引擎完整工作流")
    print(f"{'='*60}")

    print(f"""
  CondenseQuestionChatEngine 工作流：

  第 1 轮：
    用户: "什么是 RAG？"
    → 问题独立，直接检索 → 生成答案

  第 2 轮：
    用户: "它有什么优点？"（代词指代）
    → LLM 将对话历史 + "它有什么优点" 压缩为：
      "RAG（检索增强生成）有什么优点？"
    → 用压缩后的问题精准检索 → 生成答案

  第 3 轮：
    用户: "能举个例子吗？"
    → LLM 压缩为："RAG 的应用示例"
    → 检索 → 生成答案

  这个机制巧妙解决了代词的指代消解问题，
  同时避免了把整个对话历史都用于检索（检索不需要知道"你好"之类的对话）。
""")


def run():
    """运行实验 5：对话引擎深入实验。"""
    experiment_chat_modes()
    experiment_chat_memory()
    experiment_chat_workflow()
    print(f"\n  ✅ 实验 5 完成\n")


if __name__ == "__main__":
    run()
