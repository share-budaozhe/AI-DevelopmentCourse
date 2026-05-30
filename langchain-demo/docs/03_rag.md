# Demo 03 -- RAG: 检索增强生成

## 目标

完整走通 RAG 的全流程，理解每个环节的作用与实现。

## 涉及文件

- [demo_03_rag.py](../demos/demo_03_rag.py)
- [data/langchain_intro.txt](../data/langchain_intro.txt)
- [data/python_tips.txt](../data/python_tips.txt)

## 知识点

### RAG 全流程

```
文档 (txt)
  -> [TextLoader]   加载
  -> [RecursiveCharacterTextSplitter]  切分为 chunk
  -> [OpenAIEmbeddings]  向量化
  -> [Chroma]  存储到向量数据库
  -> [Retriever]  查询时检索 Top-K
  -> [Prompt + LLM]  增强生成
```

### 1. Document Loader -- 文档加载

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader

loader = DirectoryLoader("./data", glob="*.txt", loader_cls=TextLoader)
docs = loader.load()  # 返回 List[Document]
```

LangChain 内置 100+ 种 Loader，支持 PDF、网页、数据库等。这里用最简单的 `TextLoader`。

### 2. Text Splitter -- 文本切分

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300, chunk_overlap=50,
    separators=["\n\n", "\n", "。", " ", ""]
)
splits = splitter.split_documents(docs)
```

- `chunk_size=300`: 每个文本块最多 300 字符
- `chunk_overlap=50`: 相邻块重叠 50 字符，避免语义断裂
- `separators`: 按优先级尝试分割符

### 3. Embeddings -- 向量化

```python
embeddings = get_embeddings()  # text-embedding-3-small
```

将文本转换为固定维度的浮点向量 (1536 维)，
语义相近的文本在向量空间中距离更近。

### 4. Vector Store -- 向量存储

```python
from langchain_chroma import Chroma

vectorstore = Chroma.from_documents(
    documents=splits, embedding=embeddings,
    persist_directory="./chroma_rag_demo"
)
```

Chroma 是轻量级的开源向量数据库，支持本地持久化。
首次运行时创建向量库，后续可从磁盘加载。

### 5. Retrieval Chain -- 检索链

```python
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)
```

`retriever` 根据查询返回最相关的 k 个文档片段，
作为上下文注入 Prompt，让 LLM 基于真实内容回答。

## 设计要点

- `build_vectorstore()` 封装了 Load -> Split -> Embed -> Store 全流程
- `format_docs()` 将检索到的文档片段拼接为 LLM 可读的文本格式
- 向量存储支持持久化，避免每次运行都重新向量化
