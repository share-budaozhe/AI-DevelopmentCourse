# Loader — 文档加载与分块模块

## 文件位置

[src/loader.py](../src/loader.py)

## 在 RAG 中的角色

`Loader` 是 RAG 流水线的**入口**，负责将原始文档从文件系统加载进内存，清洗格式，并按策略切分为适合后续处理的小块（chunk）。它是整个"索引阶段（离线）"的第一步。

```
文件系统的 .txt 文件
        │
   [DocumentLoader]     ← 读取 + 元数据提取
        │
   [文本清洗]           ← 合并多余空白、统一格式
        │
   [TextSplitter]       ← 按语义边界切分
        │
   [滑动窗口重叠]       ← 防止边界处信息丢失
        │
   输出: List[Chunk]    ← 每个 Chunk = {text, metadata}
        │
        ↓
   送入 Embedder 向量化
```

---

## 核心概念：为什么需要分块（Chunking）？

### 问题一：LLM 的上下文窗口限制

大语言模型一次能处理的文本长度是有限的（即上下文窗口）。一篇几千字的文档无法直接塞给 LLM，必须切成小段。

### 问题二：检索精度

如果把整本书变成一个向量，"这本书讲机器学习"——这个向量太粗糙了，无法精确检索到"支持向量机的核函数"这种细粒度问题。

```
不分块：整本书 → 一个向量 → 检索时只能判断"这本书是否相关" → 太粗糙
分块后：每 500 字 → 一个向量 → 检索时能精确定位到具体段落 → 更精准
```

### 问题三：噪声控制

如果块太大，检索到的块中包含大量与查询无关的内容（噪声），会降低 LLM 的回答质量。

---

## 类结构总览

```
DocumentLoader         — 从磁盘读取原始文档
    ↓
TextSplitter           — 递归分块引擎
    ↓
ChunkingPipeline       — 编排三者：加载 → 清洗 → 分块
    ↓
Chunk (dataclass)      — 数据结构：{text, metadata}
```

---

## DocumentLoader — 文档加载器（第 22-37 行）

```python
class DocumentLoader:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_all(self) -> List[dict]:
        documents = []
        for filepath in self.data_dir.glob("*.txt"):
            content = filepath.read_text(encoding="utf-8")
            documents.append({
                "source": filepath.name,    # 来源文件名
                "content": content,          # 原始文本内容
            })
        return documents
```

### 知识点

**`pathlib.Path` vs `os.path`**：

- `Path(data_dir)` 是 Python 3.4+ 推荐的面向对象路径操作方式
- `.glob("*.txt")` 匹配目录下所有 txt 文件
- `.read_text(encoding="utf-8")` 一次性读取整个文件内容
- 要求文件必须是 **UTF-8 编码**，否则会报错（生产环境应加 `errors='ignore'` 或自动检测编码）

**局限性**：
- 只支持 `.txt` 格式，不支持 PDF、Word、HTML 等
- 不递归遍历子目录（需改用 `**/*.txt`）
- 没有异常处理（文件被占用、编码错误等场景）

---

## TextSplitter — 文本分块器（第 40-101 行）

### 分块三参数

```python
def __init__(self, chunk_size=500, chunk_overlap=100, separators=None):
```

| 参数 | 默认值 | 含义 |
|---|---|---|
| `chunk_size` | 500 | 每块最大字符数 |
| `chunk_overlap` | 100 | 相邻块之间的重叠字符数 |
| `separators` | `["\n\n", "\n", "。", ".", " ", ""]` | 分隔符优先级（从粗到细） |

### 分隔符优先级策略（Recursive Character Splitting）

```
["\n\n", "\n", "。", ".", " ", ""]
   ↑       ↑      ↑    ↑    ↑   ↑
 段落    行    句号  英文句号 空格 逐字符（兜底）
```

**核心思想**：优先在**自然的语义边界**上切分，而不是硬生生在字符数上限处截断。

```
示例文档：
"第一段内容...\n\n第二段内容...\n\n第三段内容..."

切分过程：
1. 先用 "\n\n" 切 → 得到三个段落块
2. 检查每块是否 ≤ 500 字符 → 超过的继续用下一级分隔符 "\n" 切
3. 再超 → 用 "。" 切
4. 一直递归，直到每块 ≤ 500 字符
5. 兜底：逐字符切（separator=""）
```

### `split()` 方法详解（第 53-87 行）

```python
def split(self, text: str) -> List[str]:
    # 基本情况：文本已经很短，直接返回
    if len(text) <= self.chunk_size:
        return [text] if text.strip() else []

    # 用当前级别的分隔符切分
    separator = self.separators[0]
    splits = text.split(separator) if separator else list(text)

    chunks = []
    current_chunk = ""
    for split in splits:
        piece = split + (separator if separator else "")
        if len(current_chunk) + len(piece) <= self.chunk_size:
            current_chunk += piece       # 还能装下，继续添加
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())   # 满了，保存当前块
            # 如果单个片段本身就超过 chunk_size，递归用下一级分隔符
            if len(piece.strip()) > self.chunk_size and len(self.separators) > 1:
                sub_splitter = TextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=self.separators[1:],    # ← 注意：去掉第一级分隔符
                )
                chunks.extend(sub_splitter.split(piece.strip()))
                current_chunk = ""
            else:
                current_chunk = piece     # 开始新的块
```

**递归分块的过程**：

```
原始文本 1200 字符
  │
  ├─ split by "\n\n" → 得到一个 1200 字符的段（没切动）
  │
  ├─ 该段 > 500 → 递归，split by "\n"
  │     ├─ 得到一个 700 字符的段（还是太大）
  │     ├─ 递归，split by "。" → 得到 350 + 350
  │     └─ ✓ 两块都满足 ≤ 500
  │
  └─ 最终：3 个块，每个 ≤ 500 字符
```

### 知识点：滑动窗口重叠（Overlapping）

**代码位置**：`split_with_overlap()` 第 89-101 行

```python
def split_with_overlap(self, text: str) -> List[str]:
    chunks = self.split(text)
    if self.chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            prev_tail = chunks[i - 1][-self.chunk_overlap:]   # 前一快的尾部
            chunk = prev_tail + "\n" + chunk                  # 拼接到当前块头部
        overlapped.append(chunk)
    return overlapped
```

**为什么需要重叠？**

```
文档：...在前一节我们讨论了监督学习。[关键结论：数据质量比模型复杂度更重要。]
接下来我们探讨无监督学习的方法...

如果没有重叠：
  块1: "...在前一节我们讨论了监督学习。[关键结论：数据质量比"  ← 被截断了！
  块2: "接下来我们探讨无监督学习的方法..."                  ← 缺失了前半句

查询："数据质量和模型复杂度哪个更重要" → 两个块都无法完整回答！

如果有重叠（100 字符）：
  块1: "...在前一节我们讨论了监督学习。[关键结论：数据质量比模型复杂度更重要。]接下来..."
  块2: "[关键结论：数据质量比模型复杂度更重要。]接下来我们探讨无监督学习..."  ← 完整保留了关键信息！
```

重叠让**跨块边界的语义信息**至少在一个块中保持完整。

---

## ChunkingPipeline — 分块流水线（第 104-139 行）

```python
class ChunkingPipeline:
    def run(self) -> List[Chunk]:
        documents = self.loader.load_all()
        all_chunks = []

        for doc in documents:
            # 清洗
            cleaned = re.sub(r'\n{3,}', '\n\n', doc["content"])  # 3个以上换行合并为2个
            cleaned = re.sub(r'[ \t]+', ' ', cleaned)             # 多余空格合并为单个空格

            text_chunks = self.splitter.split_with_overlap(cleaned)
            for i, chunk_text in enumerate(text_chunks):
                all_chunks.append(Chunk(
                    text=chunk_text,
                    metadata={
                        "source": doc["source"],        # 来源文件名
                        "chunk_index": i,               # 在该文件中的块序号
                    },
                ))
        return all_chunks
```

**文本清洗规则**：

| 正则 | 作用 | 示例 |
|---|---|---|
| `\n{3,} → \n\n` | 合并过多空行 | `"段落1\n\n\n\n段落2"` → `"段落1\n\n段落2"` |
| `[ \t]+ → " "` | 合并多余空格/Tab | `"Hello     World"` → `"Hello World"` |

**元数据追踪**：每个 Chunk 都记录了 `source`（来自哪个文件）和 `chunk_index`（在该文件的第几个块），这使得最终检索结果可以**溯源**——用户可以知道答案来自哪个文档的哪个段落。

---

## Chunk 数据结构（第 15-19 行）

```python
@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
```

### 知识点：`dataclass` vs 普通类

```python
# 使用 dataclass（推荐）
@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)

# 等价的手写代码
class Chunk:
    def __init__(self, text: str, metadata: dict = None):
        self.text = text
        self.metadata = metadata if metadata is not None else {}
    def __eq__(self, other): ...  # 自动生成
    def __repr__(self): ...        # 自动生成
```

- `@dataclass` 自动生成 `__init__`、`__repr__`、`__eq__` 等方法
- `field(default_factory=dict)` 是必需的，不能用 `metadata: dict = {}`（这是 Python 的一个经典陷阱：可变默认参数会被所有实例共享）

---

## 分块策略的选择指南

| chunk_size | 适用场景 | 优缺点 |
|---|---|---|
| 100-200 | 精细检索、FAQ 匹配 | 精确但缺乏上下文 |
| **500（本项目的选择）** | 通用场景 | 平衡精度和上下文 |
| 1000-2000 | 长文档问答、论文分析 | 上下文丰富但噪声多 |
| >2000 | 长文生成、摘要 | 检索颗粒度太粗 |

| chunk_overlap | 适用场景 |
|---|---|
| 0 | 文档结构清晰、段落独立 |
| chunk_size 的 10%-20% | 通用场景 |
| **100（本项目，即 20%）** | 标准选择 |
| chunk_size 的 50% | 信息密度极高、担心丢失语义 |

---

## 知识扩展：更高级的分块策略

| 策略 | 原理 | 优点 |
|---|---|---|
| **Semantic Chunking** | 用 Embedding 模型判断句子间的语义断点 | 按语义而非字符数分块 |
| **Sentence-based** | 用句号/问号/感叹号分句，按句子数凑块 | 句子完整性好 |
| **Markdown/HTML-aware** | 识别标题层级，按章节分块 | 结构信息保留 |
| **Agentic Chunking** | 用 LLM 分析文档后主动决定分块策略 | 最智能但最慢 |
| **Small-to-big Retrieval** | 用小块检索，检索后展开为大块给 LLM | 兼顾精度和上下文 |
