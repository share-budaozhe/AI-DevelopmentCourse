"""
文档加载与分块模块。

负责从文件系统读取文档，进行文本清洗，并按语义边界将
长文档分割为适合嵌入和检索的等长文本块。
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Chunk:
    """文档块的数据结构"""
    text: str
    metadata: dict = field(default_factory=dict)


class DocumentLoader:
    """文档加载器：读取目录下所有txt文件"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_all(self) -> List[dict]:
        """加载目录下所有txt文件，返回原始文档列表"""
        documents = []
        for filepath in self.data_dir.glob("*.txt"):
            content = filepath.read_text(encoding="utf-8")
            documents.append({
                "source": filepath.name,
                "content": content,
            })
        return documents


class TextSplitter:
    """文本分块器：按段落和字符数将文档切分为重叠的块"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        separators: List[str] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", " ", ""]

    def split(self, text: str) -> List[str]:
        """递归地使用分隔符切分文本，确保每块不超过chunk_size"""
        # 如果文本本身很短，直接返回
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # 按当前分隔符切分
        separator = self.separators[0]
        splits = text.split(separator) if separator else list(text)

        chunks = []
        current_chunk = ""
        for split in splits:
            piece = split + (separator if separator else "")
            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                # 如果单个片段超过chunk_size，递归使用下一级分隔符
                if len(piece.strip()) > self.chunk_size and len(self.separators) > 1:
                    sub_splitter = TextSplitter(
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap,
                        separators=self.separators[1:],
                    )
                    chunks.extend(sub_splitter.split(piece.strip()))
                    current_chunk = ""
                else:
                    current_chunk = piece

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def split_with_overlap(self, text: str) -> List[str]:
        """在分块基础上添加滑动窗口重叠"""
        chunks = self.split(text)
        if self.chunk_overlap <= 0 or len(chunks) <= 1:
            return chunks

        overlapped = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                prev_tail = chunks[i - 1][-self.chunk_overlap:]
                chunk = prev_tail + "\n" + chunk
            overlapped.append(chunk)
        return overlapped


class ChunkingPipeline:
    """分块流水线：加载 → 清洗 → 分块"""

    def __init__(
        self,
        data_dir: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        self.loader = DocumentLoader(data_dir)
        self.splitter = TextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def run(self) -> List[Chunk]:
        """执行完整的分块流水线"""
        documents = self.loader.load_all()
        all_chunks: List[Chunk] = []

        for doc in documents:
            # 清洗文本：合并多余空白
            cleaned = re.sub(r'\n{3,}', '\n\n', doc["content"])
            cleaned = re.sub(r'[ \t]+', ' ', cleaned)

            text_chunks = self.splitter.split_with_overlap(cleaned)
            for i, chunk_text in enumerate(text_chunks):
                all_chunks.append(Chunk(
                    text=chunk_text,
                    metadata={
                        "source": doc["source"],
                        "chunk_index": i,
                    },
                ))

        return all_chunks
