"""
RAG Demo 主入口 (轻量版)

纯 NumPy + TF-IDF 实现，零外部依赖下载。

用法:
    python main.py build              # 构建知识库
    python main.py search <query>     # 仅检索
    python main.py ask <query>        # 完整RAG问答
    python main.py info               # 查看知识库状态
    python main.py clear              # 清空知识库
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.loader import ChunkingPipeline
from src.embedder import Embedder
from src.store import VectorStore
from src.retriever import Retriever
from src.generator import Generator


# ============================================================
# 配置
# ============================================================
DATA_DIR = Path(__file__).parent / "data" / "documents"
STORE_PATH = Path(__file__).parent / "vector_store.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 5


def cmd_build():
    """构建知识库：加载文档 → 分块 → TF-IDF向量化 → 存储"""
    print("=" * 60)
    print("📦 RAG 知识库构建")
    print("=" * 60)

    # Step 1: 加载并分块
    print("\n[1/3] 加载文档并分块...")
    pipeline = ChunkingPipeline(
        data_dir=str(DATA_DIR),
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = pipeline.run()
    sources = set(c.metadata["source"] for c in chunks)
    print(f"  加载了 {len(sources)} 篇文档, 生成 {len(chunks)} 个文本块")
    print(f"  参数: 块大小={CHUNK_SIZE}, 重叠={CHUNK_OVERLAP}")

    if not chunks:
        print("  ⚠ 知识库目录下没有找到txt文档！")
        return

    # Step 2: TF-IDF 向量化
    print("\n[2/3] 构建 TF-IDF 向量...")
    texts = [c.text for c in chunks]
    embedder = Embedder()
    embeddings = embedder.fit(texts).embed(texts)
    print(f"  词表大小: {embedder.dimension} 个词")
    print(f"  向量维度: {embedder.dimension}")

    # Step 3: 存入向量存储
    print("\n[3/3] 存入向量存储...")
    store = VectorStore(persist_path=str(STORE_PATH))
    store.clear()

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [c.metadata for c in chunks]
    store.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"  已存入 {store.count()} 个文档块")
    print(f"  持久化文件: {STORE_PATH.resolve()}")
    print("\n✅ 知识库构建完成！")


def cmd_search(query: str):
    """检索：查询向量化 → 向量检索 → 输出结果"""
    _ensure_built()

    # 加载向量存储
    store = VectorStore(persist_path=str(STORE_PATH))

    # 用存储中的全部文档重建 TF-IDF 模型
    embedder = Embedder()
    embedder.fit(store.documents)

    retriever = Retriever(store=store, embedder=embedder, top_k=TOP_K)

    print(f"\n🔍 检索: \"{query}\"")
    print("-" * 60)
    results = retriever.retrieve(query)

    if not results:
        print("未找到相关文档。")
        return

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] 来源: {r.source}  |  相关度: {r.score:.4f}")
        preview = r.text[:200]
        print(f"    {preview}{'...' if len(r.text) > 200 else ''}")


def cmd_ask(query: str):
    """完整RAG问答：检索 → 生成答案"""
    _ensure_built()

    print(f"\n💬 问题: \"{query}\"")
    print("=" * 60)

    # 初始化各组件
    store = VectorStore(persist_path=str(STORE_PATH))
    embedder = Embedder()
    embedder.fit(store.documents)
    retriever = Retriever(store=store, embedder=embedder, top_k=TOP_K)
    generator = Generator()

    # Step 1: 检索
    results = retriever.retrieve(query)
    print(f"\n📚 检索到 {len(results)} 个相关片段:\n")

    context = retriever.format_context(results)
    for i, r in enumerate(results, 1):
        print(f"  [{i}] {r.source} (相关度: {r.score:.4f})")

    # Step 2: 生成
    print("\n" + "-" * 60)
    mode_label = generator.mode_label
    print(f"🤖 回答 (模式: {mode_label}):\n")
    answer = generator.generate(query, results, context)
    print(answer)


def cmd_info():
    """查看知识库信息"""
    if not STORE_PATH.exists():
        print("知识库尚未构建，请先运行: python main.py build")
        return

    store = VectorStore(persist_path=str(STORE_PATH))
    # 统计来源
    sources = set()
    for m in store.metadatas:
        if "source" in m:
            sources.add(m["source"])

    print(f"📊 知识库状态")
    print(f"  文档块总数: {store.count()}")
    print(f"  文档来源数: {len(sources)}")
    print(f"  存储文件: {STORE_PATH.resolve()}")
    if sources:
        print(f"  来源文件: {', '.join(sorted(sources))}")


def cmd_clear():
    """清空知识库"""
    store = VectorStore(persist_path=str(STORE_PATH))
    store.clear()
    print("✅ 知识库已清空")


def _ensure_built():
    """确保知识库已构建"""
    if not STORE_PATH.exists():
        print("⚠ 知识库尚未构建，正在自动构建...\n")
        cmd_build()
        print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="RAG (检索增强生成) Demo — 纯NumPy轻量实现",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py build
  python main.py search "什么是机器学习"
  python main.py ask "Python有哪些数据处理库"
  python main.py info
  python main.py clear
        """,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    sub.add_parser("build", help="构建知识库（文档→分块→TF-IDF→存储）")
    p_search = sub.add_parser("search", help="检索相关文档")
    p_search.add_argument("query", help="搜索查询")
    p_ask = sub.add_parser("ask", help="完整RAG问答")
    p_ask.add_argument("query", help="问题")
    sub.add_parser("info", help="查看知识库状态")
    sub.add_parser("clear", help="清空知识库")

    args = parser.parse_args()

    if args.command == "build":
        cmd_build()
    elif args.command == "search":
        cmd_search(args.query)
    elif args.command == "ask":
        cmd_ask(args.query)
    elif args.command == "info":
        cmd_info()
    elif args.command == "clear":
        cmd_clear()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
