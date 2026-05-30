"""
检索模块。

对向量检索结果进行后处理，包括相似度过滤、重排序等。
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchResult:
    """单条检索结果"""
    text: str
    source: str
    score: float
    chunk_id: str = ""


class Retriever:
    """检索器：封装向量检索与后处理"""

    def __init__(
        self,
        store,
        embedder,
        top_k: int = 5,
        min_score: float = 0.0,
    ):
        self.store = store
        self.embedder = embedder
        self.top_k = top_k
        self.min_score = min_score

    def retrieve(self, query: str) -> List[SearchResult]:
        """执行检索并返回格式化结果"""
        # 1. 查询向量化
        query_vec = self.embedder.embed_query(query)

        # 2. 向量检索
        hits = self.store.search(
            query_embedding=query_vec.tolist(),
            top_k=self.top_k,
        )

        # 3. 后处理：相似度过滤
        results = []
        for hit in hits:
            if hit["score"] < self.min_score:
                continue
            results.append(SearchResult(
                text=hit["text"],
                source=hit["metadata"].get("source", "未知"),
                score=hit["score"],
                chunk_id=hit["id"],
            ))

        return results

    def format_context(self, results: List[SearchResult]) -> str:
        """将检索结果拼接为LLM上下文文本"""
        if not results:
            return "（未找到相关文档）"

        parts = []
        for i, r in enumerate(results, 1):
            parts.append(
                f"【文档{i}】(来源: {r.source}, 相关度: {r.score:.2f})\n{r.text}"
            )
        return "\n\n".join(parts)
