"""
Demo 03 -- RAG: 检索增强生成

演示完整的 RAG 流程:
  1. 加载文档 (TextLoader)
  2. 切分文本 (RecursiveCharacterTextSplitter)
  3. 向量化 (Embeddings, 支持 OpenAI)
  4. 存储到向量数据库 (Chroma)
  5. 创建检索链 (Retrieval Chain)
  6. 提问并基于检索结果生成回答

运行前请设置 .env 文件中的 API Key。
"""

from config import get_llm, get_embeddings, check_api_key, print_config

import os as _os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# 全局向量存储实例 (初始化一次,复用)
_vectorstore = None
_rag_chain = None


def build_vectorstore(persist_dir="./chroma_rag_demo"):
    """构建向量存储: Load -> Split -> Embed -> Store"""
    print("Step 1: 加载文档...")
    loader = DirectoryLoader(
        _os.path.join(_os.path.dirname(__file__), "..", "data"),
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    docs = loader.load()
    print(f"  已加载 {len(docs)} 个文档")

    print("Step 2: 切分文本...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
    )
    splits = splitter.split_documents(docs)
    print(f"  已切分为 {len(splits)} 个文本块")

    print("Step 3: 向量化并存储...")
    embeddings = get_embeddings()

    if _os.path.exists(persist_dir):
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
        print("  从已有存储加载")
    else:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_dir
        )
        print(f"  已创建向量存储，持久化到 {persist_dir}")

    return vectorstore


def build_rag_chain(vectorstore):
    """构建 RAG 问答链"""
    llm = get_llm()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    template = """你是一个知识问答助手。请根据以下上下文回答问题。
如果上下文中没有相关信息，请如实说不知道。

上下文:
{context}

问题: {question}

回答:"""

    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join(
            f"[来源: {d.metadata.get('source', '?')}] {d.page_content}"
            for d in docs
        )

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain, retriever


def demo_retrieve(vectorstore):
    print()
    print("=" * 50)
    print("1. 向量相似度检索")
    print("=" * 50)
    query = "什么是列表推导式"
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    docs = retriever.invoke(query)
    print(f"查询: {query}")
    print(f"检索到 {len(docs)} 个相关片段:")
    for i, doc in enumerate(docs, 1):
        print(f"  [{i}] 来源: {doc.metadata.get('source', 'unknown')}")
        print(f"      内容: {doc.page_content[:100]}...")
        print()


def demo_rag_chain(vectorstore):
    rag_chain, _ = build_rag_chain(vectorstore)
    print("=" * 50)
    print("2. RAG 问答链")
    print("=" * 50)
    questions = [
        "什么是列表推导式?",
        "LangChain 有哪些核心概念?",
        "Python 的异步编程用什么库?"
    ]
    for q in questions:
        print(f"\nQ: {q}")
        answer = rag_chain.invoke(q)
        print(f"A: {answer}")


def demo_retriever_with_score(vectorstore):
    print()
    print("=" * 50)
    print("3. 带分数的检索")
    print("=" * 50)
    query = "装饰器是什么"
    results = vectorstore.similarity_search_with_score(query, k=3)
    print(f"查询: {query}")
    for i, (doc, score) in enumerate(results, 1):
        print(f"  [{i}] 距离: {score:.4f}")
        print(f"      内容: {doc.page_content[:80]}...")
        print()


def run_guided():
    global _vectorstore
    _vectorstore = build_vectorstore()
    demo_retrieve(_vectorstore)
    demo_rag_chain(_vectorstore)
    demo_retriever_with_score(_vectorstore)


# ================================================================
# 交互模式
# ================================================================

def interactive_mode():
    """交互模式: 自由提问,基于文档库的 RAG 问答"""
    global _vectorstore, _rag_chain

    if _vectorstore is None:
        print("正在初始化向量存储...")
        _vectorstore = build_vectorstore()

    rag_chain, retriever = build_rag_chain(_vectorstore)
    _rag_chain = rag_chain

    print()
    print("=" * 50)
    print("  交互模式 -- RAG 知识问答")
    print("=" * 50)
    print("知识库包含: LangChain 简介、Python 实用技巧")
    print()
    print("你可以:")
    print("  - 输入任何问题,我会从知识库中检索并回答")
    print("  - 输入 /sources  查看最后一次检索到的来源")
    print("  - 输入 /quit     退出")
    print()

    last_docs = []

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

        # 先检索,展示来源
        last_docs = retriever.invoke(user_input)
        print(f"\n[检索到 {len(last_docs)} 个相关片段]")

        if user_input == "/sources":
            for i, doc in enumerate(last_docs, 1):
                print(f"  [{i}] {doc.metadata.get('source', '?')}:")
                print(f"      {doc.page_content[:120]}...")
            continue

        # 执行 RAG 问答
        answer = rag_chain.invoke(user_input)
        print(f"A: {answer}")

        # 展示引用的来源
        if last_docs:
            print(f"\n(引用来源: {', '.join(set(d.metadata.get('source','?').split(chr(92))[-1] for d in last_docs))})")


if __name__ == "__main__":
    ok, msg = check_api_key()
    if not ok:
        print(f"错误: {msg}")
        exit(1)

    print_config()
    print()
    print("选择运行模式:")
    print("  [1] 演示模式 -- 自动运行 RAG 流程演示")
    print("  [2] 交互模式 -- 自由提问,基于知识库问答")
    choice = input("请输入 1 或 2 (默认 1): ").strip()

    if choice == "2":
        interactive_mode()
    else:
        run_guided()
