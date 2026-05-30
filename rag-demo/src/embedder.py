"""
嵌入向量生成模块 (轻量版)。

使用 TF-IDF 将文本转换为稀疏向量表示。
不依赖任何外部模型下载，仅需 NumPy。
"""

import math
from typing import List, Dict
import numpy as np


class Embedder:
    """TF-IDF 嵌入器"""

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}       # word → index
        self.idf: np.ndarray = None                # 逆文档频率
        self._fitted = False

    @property
    def dimension(self) -> int:
        """返回向量维度（词表大小）"""
        return len(self.vocabulary) if self.vocabulary else 0

    def _tokenize(self, text: str) -> List[str]:
        """简单中文+英文分词"""
        import re
        # 提取中文字符和英文单词
        tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\d+', text.lower())
        return tokens

    def fit(self, documents: List[str]) -> "Embedder":
        """基于文档语料构建词表和IDF"""
        # 构建词表
        vocab_set = set()
        tokenized_docs = []
        for doc in documents:
            tokens = self._tokenize(doc)
            tokenized_docs.append(tokens)
            vocab_set.update(tokens)

        self.vocabulary = {word: i for i, word in enumerate(sorted(vocab_set))}
        vocab_size = len(self.vocabulary)
        doc_count = len(documents)

        # 计算 IDF
        df = np.zeros(vocab_size)
        for tokens in tokenized_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                if token in self.vocabulary:
                    df[self.vocabulary[token]] += 1

        # IDF = log((N+1)/(df+1)) + 1  (smooth)
        self.idf = np.log((doc_count + 1) / (df + 1)) + 1
        self._fitted = True
        return self

    def _tfidf_vector(self, tokens: List[str]) -> np.ndarray:
        """计算单个文档的 TF-IDF 向量"""
        vec = np.zeros(len(self.vocabulary))
        if not tokens:
            return vec

        # TF
        for token in tokens:
            if token in self.vocabulary:
                vec[self.vocabulary[token]] += 1

        # 归一化 TF
        vec = vec / len(tokens)

        # TF-IDF
        vec = vec * self.idf

        # L2 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec

    def embed(self, texts: List[str]) -> np.ndarray:
        """将文本列表转换为 TF-IDF 向量矩阵 (N, dim)"""
        if not self._fitted:
            self.fit(texts)

        if isinstance(texts, str):
            texts = [texts]

        vectors = []
        for text in texts:
            tokens = self._tokenize(text)
            vec = self._tfidf_vector(tokens)
            vectors.append(vec)

        return np.array(vectors)

    def embed_query(self, query: str) -> np.ndarray:
        """将单个查询转换为向量"""
        return self.embed([query])[0]
