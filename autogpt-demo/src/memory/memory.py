"""
记忆系统实现
布道者

AutoGPT 的三层记忆架构：
1. 短期记忆 (ShortTermMemory) — 当前任务的对话上下文（环形缓冲）
2. 长期记忆 (LongTermMemory) — 跨任务的持久化知识（ChromaDB 向量存储）
3. 工作记忆 (WorkingMemory)  — 当前任务的执行状态和中间结果

设计理念:
    - 短期记忆保持 Agent 对当前任务的专注度
    - 长期记忆让 Agent 从过往经验中学习
    - 记忆分层避免了上下文的 Token 爆炸问题
"""
import os
import json
import time
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# 短期记忆
# 布道者: 环形缓冲区，保留最近 N 轮对话，自动淘汰旧内容
# ═══════════════════════════════════════════════════════════════

class ShortTermMemory:
    """
    短期记忆

    布道者:
        基于环形缓冲区的对话历史管理。
        只保留最近 max_size 条记录，避免 Token 消耗过大。
        同时维护一个摘要字段，记录关键信息。
    """

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self.history: List[Dict[str, Any]] = []
        self.summary: str = ""
        self.key_facts: List[str] = []

    def add(self, role: str, content: str, metadata: Dict = None) -> None:
        """添加一条记忆"""
        entry = {
            "role": role,           # system / user / agent / tool
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.history.append(entry)

        # 环形缓冲: 超过上限时移除最旧的
        if len(self.history) > self.max_size:
            removed = self.history.pop(0)
            # 将被移除的内容关键信息合并到摘要
            if len(removed["content"]) > 50:
                self.summary += f"[{removed['role']}] {removed['content'][:100]}...\n"

    def add_user(self, content: str) -> None:
        self.add("user", content)

    def add_agent(self, content: str, metadata: Dict = None) -> None:
        self.add("agent", content, metadata)

    def add_tool_result(self, content: str) -> None:
        self.add("tool", content)

    def add_system(self, content: str) -> None:
        self.add("system", content)

    def get_recent(self, n: int = None) -> List[Dict[str, Any]]:
        """获取最近 N 条记录"""
        n = n or self.max_size
        return self.history[-n:]

    def get_context_for_llm(self, max_entries: int = 10) -> str:
        """格式化为 LLM 上下文"""
        recent = self.get_recent(max_entries)
        lines = []
        if self.summary:
            lines.append(f"## 历史摘要\n{self.summary}\n")
        for entry in recent:
            role_label = {
                "user": "用户", "agent": "Agent", "tool": "工具结果",
                "system": "系统",
            }.get(entry["role"], entry["role"])
            content = entry["content"][:500]
            lines.append(f"[{role_label}] {content}")
        return "\n\n".join(lines)

    def add_key_fact(self, fact: str) -> None:
        """添加关键事实"""
        if fact not in self.key_facts:
            self.key_facts.append(fact)

    def clear(self) -> None:
        """清空短期记忆"""
        self.history.clear()
        self.summary = ""
        self.key_facts.clear()


# ═══════════════════════════════════════════════════════════════
# 长期记忆
# 布道者: 基于 ChromaDB 的向量存储，支持语义搜索和持久化
# ═══════════════════════════════════════════════════════════════

class LongTermMemory:
    """
    长期记忆

    布道者:
        使用 ChromaDB 作为向量数据库后端。
        每次 Agent 完成任务后，将关键发现和经验存入长期记忆。
        下次任务时可通过语义搜索检索相关历史经验。

        存储内容:
        - 任务总结
        - 关键发现
        - 成功策略
        - 失败教训
    """

    def __init__(self, persist_dir: str = "./workspace/chroma_db"):
        self.persist_dir = persist_dir
        self.collection = None
        self._enabled = False
        self._init_chroma()

    def _init_chroma(self) -> None:
        """初始化 ChromaDB 连接"""
        try:
            import chromadb
            os.makedirs(self.persist_dir, exist_ok=True)
            client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = client.get_or_create_collection(
                name="autogpt_memory",
                metadata={"hnsw:space": "cosine"},
            )
            self._enabled = True
        except ImportError:
            self._enabled = False
        except Exception:
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def store(self, content: str, metadata: Dict = None, doc_id: str = None) -> Optional[str]:
        """
        存储一条长期记忆

        参数:
            content: 记忆内容
            metadata: 附加元数据（task_id, category, tags 等）
            doc_id: 可选的文档 ID，不提供则自动生成

        返回:
            doc_id 或 None（如果存储不可用）
        """
        if not self._enabled or not self.collection:
            return None

        doc_id = doc_id or hashlib.md5(
            f"{content}{time.time()}".encode()
        ).hexdigest()[:16]

        meta = metadata or {}
        meta["timestamp"] = datetime.now().isoformat()
        meta["content_preview"] = content[:200]

        try:
            self.collection.add(
                documents=[content],
                metadatas=[meta],
                ids=[doc_id],
            )
            return doc_id
        except Exception:
            return None

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        语义搜索长期记忆

        参数:
            query: 搜索关键词
            top_k:  返回的最大结果数

        返回:
            搜索结果列表，每项包含 content / metadata / similarity
        """
        if not self._enabled or not self.collection:
            return self._fallback_search(query, top_k)

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            memories = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    dist = results["distances"][0][i] if results.get("distances") else 0
                    memories.append({
                        "content": doc,
                        "metadata": meta,
                        "similarity": round(1.0 - float(dist), 4) if dist else 1.0,
                    })
            return memories
        except Exception:
            return self._fallback_search(query, top_k)

    def _fallback_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """降级: 提示安装 ChromaDB"""
        return [{
            "content": f"（长期记忆不可用——安装 chromadb 可启用语义搜索功能）",
            "metadata": {"source": "fallback"},
            "similarity": 0,
        }]


# ═══════════════════════════════════════════════════════════════
# 工作记忆
# 布道者: 存储当前任务执行过程中的临时状态
# ═══════════════════════════════════════════════════════════════

class WorkingMemory:
    """
    工作记忆

    布道者:
        类似人脑的"工作台"——暂存当前任务相关的数据。
        任务完成后自动清空，避免信息泄露到下一任务。

        包含:
        - goal: 当前目标
        - plan: 任务计划（子任务列表）
        - current_task_index: 当前执行到第几步
        - intermediate_results: 中间结果
        - checkpoint: 检查点数据（支持断点续跑）
    """

    def __init__(self):
        self.goal: str = ""
        self.plan: List[Dict[str, Any]] = []
        self.current_task_index: int = 0
        self.intermediate_results: Dict[str, Any] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.aborted: bool = False

    def set_goal(self, goal: str) -> None:
        self.goal = goal
        self.current_task_index = 0
        self.plan = []
        self.intermediate_results = {}
        self.execution_log = []
        self.aborted = False

    def set_plan(self, tasks: List[Dict[str, Any]]) -> None:
        """设置任务计划"""
        self.plan = tasks
        self.current_task_index = 0

    def current_task(self) -> Optional[Dict[str, Any]]:
        """获取当前需要执行的任务"""
        if 0 <= self.current_task_index < len(self.plan):
            return self.plan[self.current_task_index]
        return None

    def advance_task(self) -> bool:
        """推进到下一个子任务"""
        self.current_task_index += 1
        return self.current_task_index < len(self.plan)

    def log_action(self, thought: str, action: str, result: str) -> None:
        """记录一次行动"""
        self.execution_log.append({
            "step": len(self.execution_log) + 1,
            "thought": thought[:300],
            "action": action,
            "result": result[:500],
            "timestamp": datetime.now().isoformat(),
        })

    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度"""
        return {
            "goal": self.goal,
            "total_tasks": len(self.plan),
            "completed_tasks": self.current_task_index,
            "current_task": self.current_task(),
            "total_actions": len(self.execution_log),
        }

    def save_checkpoint(self, path: str) -> None:
        """保存检查点"""
        checkpoint = {
            "goal": self.goal,
            "plan": self.plan,
            "current_task_index": self.current_task_index,
            "intermediate_results": self.intermediate_results,
            "execution_log": self.execution_log,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

    def load_checkpoint(self, path: str) -> bool:
        """加载检查点"""
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.goal = data.get("goal", "")
            self.plan = data.get("plan", [])
            self.current_task_index = data.get("current_task_index", 0)
            self.intermediate_results = data.get("intermediate_results", {})
            self.execution_log = data.get("execution_log", [])
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """清空工作记忆"""
        self.goal = ""
        self.plan = []
        self.current_task_index = 0
        self.intermediate_results = {}
        self.execution_log = []
        self.aborted = False
