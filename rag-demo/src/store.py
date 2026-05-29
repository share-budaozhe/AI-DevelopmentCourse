"""
向量存储模块 (轻量版)。

纯 NumPy 实现向量相似度检索，无需外部数据库。
支持持久化（JSON序列化）。
"""

import json
import os
from typing import List, Optional
import numpy as np


class VectorStore:
    """轻量级向量存储与检索"""

    def __init__(self, persist_path: str = "./vector_store.json"):
        self.persist_path = persist_path
        self.ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[dict] = []
        self.embeddings: np.ndarray = None  # (N, dim)

        # 尝试加载已有数据
        if os.path.exists(persist_path):
            self._load()

    def add(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        documents: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        """批量添加文档向量"""
        if metadatas is None:
            metadatas = [{}] * len(ids)

        self.ids.extend(ids)
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)

        if self.embeddings is None:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

        self._save()

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> List[dict]:
        """
        余弦相似度检索 top_k 个最相似文档。
        query_embedding: (dim,) 一维向量
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        # 余弦相似度 (假设向量已L2归一化)
        similarities = np.dot(self.embeddings, query_embedding)

        # 取 top_k
        if len(similarities) <= top_k:
            top_indices = np.argsort(similarities)[::-1]
        else:
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        hits = []
        for idx in top_indices:
            hits.append({
                "id": self.ids[idx],
                "text": self.documents[idx],
                "metadata": self.metadatas[idx],
                "score": round(float(similarities[idx]), 4),
            })
        return hits

    def count(self) -> int:
        """返回文档块总数"""
        return len(self.ids)

    def clear(self) -> None:
        """清空所有数据"""
        self.ids = []
        self.documents = []
        self.metadatas = []
        self.embeddings = None
        if os.path.exists(self.persist_path):
            os.remove(self.persist_path)

    def _save(self) -> None:
        """持久化到 JSON 文件"""
        data = {
            "ids": self.ids,
            "documents": self.documents,
            "metadatas": self.metadatas,
            "embeddings": self.embeddings.tolist() if self.embeddings is not None else [],
        }
        with open(self.persist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """从 JSON 文件加载"""
        with open(self.persist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.ids = data["ids"]
        self.documents = data["documents"]
        self.metadatas = data["metadatas"]
        self.embeddings = np.array(data["embeddings"]) if data["embeddings"] else None
