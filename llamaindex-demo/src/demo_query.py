"""
═══════════════════════════════════════════════════════════════
  💬 LlamaIndex 学习教程 — src/demo_query.py
  实验 4：查询引擎深入实验

  支持 DeepSeek / OpenAI 进行真实的 LLM 查询
═══════════════════════════════════════════════════════════════

核心知识点：
- QueryEngine：端到端的问答接口
- 响应合成模式（compact / refine / tree_summarize）
- 自定义提示模板
- 引用溯源（显示答案来自哪些文档）
"""
from llama_index.core import (
    VectorStoreIndex, Settings, MockEmbedding,
)
from sample_data import DEMO_DOCUMENTS, load_all_documents
from config import auto_setup


def experiment_query_engine_basic():
    """🔬 实验 4.1：查询引擎 — 真实查询演示

    需要 DeepSeek 或 OpenAI API 密钥。
    无密钥时自动跳过。
    """
    print(f"\n{'='*60}")
    print(f"  🔬 实验 4.1：查询引擎 — 真实查询")
    print(f"{'='*60}")

    mode = auto_setup()

    if mode == "mock":
        print(f"\n  ⚠️ 未检测到 API 密钥，演示查询引擎结构。")
        print(f"  要体验真实查询，请在 .env 中设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        print(f"\n  以 DeepSeek 为例：")
        print(f"    echo DEEPSEEK_API_KEY=sk-xxx > .env")
        _demo_structure()
        return

    print(f"\n  当前模式: {mode}")

    # 用真实嵌入模型创建索引
    index = VectorStoreIndex.from_documents(DEMO_DOCUMENTS)

    query_engine = index.as_query_engine(
        similarity_top_k=3,
        response_mode="compact",
    )

    questions = [
        "Python 是什么？它的特点有哪些？",
        "LlamaIndex 和 LangChain 有什么区别？",
    ]

    for q in questions:
        print(f"\n  ❓ {q}")
        try:
            response = query_engine.query(q)
            print(f"  🤖 {response.response[:300]}")
            if response.source_nodes:
                print(f"  📎 来源数: {len(response.source_nodes)}")
        except Exception as e:
            print(f"  ❌ 查询失败: {e}")

    # 自定义提示的查询
    print(f"\n  --- 试试自定义提示 ---")
    from llama_index.core import PromptTemplate

    chinese_prompt = PromptTemplate(
        "你是一个专业的知识助手。请用简洁的中文回答。\n"
        "\n参考资料：\n{context_str}\n\n问题：{query_str}\n\n回答："
    )

    custom_engine = index.as_query_engine(
        similarity_top_k=3,
        text_qa_template=chinese_prompt,
    )
    try:
        response = custom_engine.query("Transformer 架构的核心创新是什么？")
        print(f"  🤖 {response.response[:300]}")
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")


def _demo_structure():
    """演示查询引擎的结构（无需 API）。"""
    Settings.embed_model = MockEmbedding(embed_dim=384)
    index = VectorStoreIndex.from_documents(DEMO_DOCUMENTS)

    print(f"\n  QueryEngine 配置示例：")
    print(f"  " + "-" * 50)
    print(f"  query_engine = index.as_query_engine(")
    print(f"      similarity_top_k=5,       # 检索 5 个最相关片段")
    print(f"      response_mode='compact',  # 打包发送给 LLM")
    print(f"  )")
    print(f"  response = query_engine.query('你的问题')")
    print(f"  print(response.response)      # 文本答案")
    print(f"  print(response.source_nodes)  # 参考来源")


def experiment_response_modes():
    """🔬 实验 4.2：响应合成模式对比"""
    print(f"\n{'='*60}")
    print(f"  🔬 实验 4.2：响应合成模式对比")
    print(f"{'='*60}")

    modes = [
        ("compact", "全部片段打包 → 一次性发给 LLM。快，适合 3-5 个片段。"),
        ("refine", "逐条处理：答第 1 条 → 用第 2 条修正 → 用第 3 条修正。适合深度融合。"),
        ("tree_summarize", "构建片段树 → 自底向上分层总结。适合 10+ 个片段。"),
        ("accumulate", "逐条追加到上下文 → 最后一次性生成。"),
    ]

    for name, desc in modes:
        print(f"\n  📍 {name}: {desc}")


def run():
    """运行实验 4：查询引擎深入实验。"""
    experiment_query_engine_basic()
    experiment_response_modes()
    print(f"\n  ✅ 实验 4 完成\n")


if __name__ == "__main__":
    run()
