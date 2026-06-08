"""
═══════════════════════════════════════════════════════════════
  📚 LlamaIndex 学习教程 — main.py（交互入口）
  8 个核心实验 + 启发式问答 + 详细文档导航
═══════════════════════════════════════════════════════════════

运行方式：
    cd llamaindex-demo
    python -m src.main
"""
from __future__ import annotations

import sys
import os

# ?? src ???????????????????
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import auto_setup, print_config_guide

# 确保 src 目录在路径中


def show_banner():
    print(r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     📚  LlamaIndex 学习教程 v1.0                              ║
║     从零掌握 RAG 与 LLM 数据框架                              ║
║                                                              ║
║     8 个核心实验 | 启发式问答 | 完整文档                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def show_menu():
    print("""
  📋 实验菜单：
  ┌──────────────────────────────────────────────────────────┐
  │ [1] 文档加载与节点解析  → Documents & Node Parsing        │
  │ [2] 索引类型对比        → VectorStore vs Summary          │
  │ [3] 检索器实验          → Retriever & Top-K              │
  │ [4] 查询引擎实验        → QueryEngine & Response Modes    │
  │ [5] 对话引擎实验        → ChatEngine & Memory            │
  │ [6] Agent 实验          → Tools & ReAct                  │
  │ [7] 持久化与存储        → Persist & Load                  │
  │ [8] 进阶特性            → Postprocessor & Pipelines      │
  ├──────────────────────────────────────────────────────────┤
  │ [9] 运行全部实验（顺序执行）                               │
  │ [h] 查看启发式问题与答案                                   │
  │ [d] 查看文档导航                                          │
  │ [r] 查看 README（运行说明）                                │
  │ [q] 退出                                                  │
  └──────────────────────────────────────────────────────────┘
""")


def run_experiment(choice: str):
    """运行指定实验。"""
    experiments = {
        "1": ("demo_documents", "文档加载与节点解析"),
        "2": ("demo_indexes", "索引类型对比"),
        "3": ("demo_retrievers", "检索器实验"),
        "4": ("demo_query", "查询引擎实验"),
        "5": ("demo_chat", "对话引擎实验"),
        "6": ("demo_agents", "Agent 智能体实验"),
        "7": ("demo_storage", "持久化与存储"),
        "8": ("demo_advanced", "进阶特性实验"),
    }

    if choice in experiments:
        module_name, title = experiments[choice]
        print(f"\n{'='*60}")
        print(f"  🚀 启动实验 {choice}：{title}")
        print(f"{'='*60}")
        mod = __import__(module_name)
        mod.run()
    elif choice == "9":
        print(f"\n{'='*60}")
        print(f"  🚀 运行全部实验")
        print(f"{'='*60}")
        for num in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            module_name, title = experiments[num]
            print(f"\n{'#'*60}")
            print(f"  实验 {num}：{title}")
            mod = __import__(module_name)
            mod.run()
        print(f"\n🎉 全部实验完成！")
    elif choice == "h":
        show_qa()
    elif choice == "d":
        show_docs_nav()
    elif choice == "c":
        print_config_guide()
    elif choice == "r":
        show_readme_guide()
    else:
        print(f"  ⚠️ 无效选择: {choice}")


def show_qa():
    """启发式问题与答案。"""
    qa = r"""
╔══════════════════════════════════════════════════════════════╗
║              💡 启发式问题与答案（7 个核心问题）               ║
╚══════════════════════════════════════════════════════════════╝

Q1: LlamaIndex 和 LangChain 到底什么关系？
─────────────────────────────────────────
A: 定位不同。LlamaIndex 专注「数据 → LLM」的桥梁——把各种
   格式的数据索引化，让 LLM 高效检索。LangChain 是通用框架，
   提供 Chain、Agent、Tool 等抽象来编排 LLM 应用。
   
   类比：LlamaIndex 像"搜索引擎的后端"，LangChain 像"应用
   编排框架"。两者可以组合用——在 LangChain 的 Agent 中把
   LlamaIndex 的 QueryEngine 作为 Tool 调用。

Q2: 为什么 RAG 需要切分文档（chunking）？
─────────────────────────────────────
A: 两个原因：
   ① LLM 的上下文窗口有限（虽然现在很大，但 token=$$$）
   ② 检索精度：整篇文档做向量嵌入会丢失细节，切成小块后
      每块的向量更能代表其语义，检索更精准。
   典型大小：256-1024 tokens，重叠 10-20%。

Q3: VectorStoreIndex 和 SummaryIndex 怎么选？
───────────────────────────────────────────
A: 看查询类型：
   - 事实查找型（"Python 是谁发明的？"）→ VectorStoreIndex
   - 总结概括型（"这些文档讲了什么？"）→ SummaryIndex
   - 大多数 RAG 场景用 VectorStoreIndex。
   - SummaryIndex 的优势：不需要嵌入模型，可以用于没有 GPU/
     API 密钥的场景。

Q4: similarity_top_k 设多少合适？
───────────────────────────────
A: 没有固定答案，取决于：
   - 文档库大小：库越大，k 可以适当大些
   - 问题复杂度：简单事实 k=3-5，复杂分析 k=5-10
   - LLM 窗口：k 越大 → context 越长 → token 消耗越多
   - 经验值：k=5 是不错的起点，再根据效果调整

Q5: compact / refine / tree_summarize 怎么区分？
──────────────────────────────────────────────
A: - compact（默认）：把检索到的所有片段打包成一条消息，
     一次性发给 LLM。适合片段少（≤5）的场景。
   - refine：逐条处理，先回答第 1 条，再用第 2 条修正，
     依次类推。适合需要深度融合的复杂查询。
   - tree_summarize：构建树形结构，自底向上总结。
     适合结果很多（>10）的场景，但 token 消耗最大。
   建议：先用 compact，效果不好再试 refine。

Q6: 生产环境该用哪个向量数据库？
─────────────────────────────
A: 看规模：
   - <10K 文档 → Chroma（免费、够用）
   - <1M 文档 → Qdrant（高性能、过滤强）
   - >1M 文档 → Milvus / Pinecone（分布式）
   - 已有 PG → pgvector（一站式，不用加新服务）
   对于 LlamaIndex，所有向量数据库的 API 几乎一样，
   切换只需改 vector_store 参数。

Q7: 如何评估 RAG 系统的质量？
───────────────────────────
A: 两个维度：
   ① 检索质量：检索到的内容是否相关？
      - 指标：Recall@K、MRR、NDCG
   ② 生成质量：生成的答案是否正确？
      - 指标：Faithfulness（忠实度）、Relevancy（相关性）
   LlamaIndex 内置了评估模块（llama_index.core.evaluation），
   可以自动打分。也可以用 RAGAS 等第三方框架。
"""
    print(qa)


def show_docs_nav():
    """文档导航。"""
    docs = r"""
╔══════════════════════════════════════════════════════════════╗
║              📖 文档导航                                      ║
╚══════════════════════════════════════════════════════════════╝

  docs/ 目录下的学习文档：

  ┌──────────────────────────────────────┬────────────────────┐
  │ 01-overview.md                       │ 项目总览与核心概念  │
  │ 02-documents.md                      │ 文档与节点详解     │
  │ 03-indexes.md                        │ 索引类型与原理     │
  │ 04-retrievers.md                     │ 检索器深入理解     │
  │ 05-query-engines.md                  │ 查询引擎全解析     │
  │ 06-chat-engines.md                   │ 对话引擎与记忆     │
  │ 07-agents.md                         │ Agent 与工具       │
  │ 08-advanced.md                       │ 进阶特性与最佳实践 │
  │ 09-faq.md                            │ 常见问题汇总       │
  ├──────────────────────────────────────┼────────────────────┤
  │ answers/                             │ 思考题参考答案     │
  │   └── thinking-questions.md          │ 12 道启发式思考题  │
  └──────────────────────────────────────┴────────────────────┘

  项目根目录：
  ├── README.md        → 项目说明 + 运行指南
  ├── requirements.txt → 依赖列表
  └── data/sample_docs/ → 示例文档（3 个 Markdown 文件）
"""
    print(docs)


def show_readme_guide():
    """运行说明。"""
    guide = r"""
╔══════════════════════════════════════════════════════════════╗
║              🚀 测试运行详细说明                              ║
╚══════════════════════════════════════════════════════════════╝

  1. 环境准备
  ────────────────────────────────────────
  # 创建虚拟环境（推荐）
  python -m venv .venv

  # 激活虚拟环境
  .venv\Scripts\activate        # Windows
  source .venv/bin/activate      # Mac/Linux

  # 安装依赖
  pip install -r requirements.txt


  2. 运行实验
  ────────────────────────────────────────
  # 交互式菜单（推荐）
  cd llamaindex-demo
  python -m src.main

  # 或单独运行某个实验
  python -m src.demo_documents   # 实验 1
  python -m src.demo_indexes     # 实验 2
  python -m src.demo_retrievers  # 实验 3
  python -m src.demo_query       # 实验 4
  python -m src.demo_chat        # 实验 5
  python -m src.demo_agents      # 实验 6
  python -m src.demo_storage     # 实验 7
  python -m src.demo_advanced    # 实验 8


  3. API 密钥配置
  ────────────────────────────────────────
  本项目使用 MockEmbedding 进行演示，
  索引创建和结构演示无需 API 密钥。

  如需实际查询（实验 4 的 query 功能），需要：
  # 创建 .env 文件
  echo OPENAI_API_KEY=sk-your-key > .env

  不需要 API 密钥也能完成 90% 的学习内容！


  4. 学习路径建议
  ────────────────────────────────────────
  初学者：实验 1 → 2 → 3 → 4 → 7
  进阶者：实验 5 → 6 → 8
  面试准备：全部实验 + 启发式问答 + docs/answers/


  5. 验证安装
  ────────────────────────────────────────
  python -c "import llama_index; print(llama_index.__version__)"
  # 预期输出: 0.12.x 或更高
"""
    print(guide)


def main():
    """主循环。"""
    show_banner()

    while True:
        show_menu()
        try:
            choice = input("  👉 请输入选项: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  👋 再见！")
            break

        if choice in ("q", "quit", "exit"):
            print("\n  👋 再见！祝你学习顺利！\n")
            break

        run_experiment(choice)

        # 每个实验后暂停
        if choice not in ("h", "d", "r", "q"):
            try:
                input("\n  按 Enter 返回菜单...")
            except (EOFError, KeyboardInterrupt):
                print()
                break


if __name__ == "__main__":
    main()
