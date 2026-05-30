"""
答案生成模块。

支持 OpenAI 和 DeepSeek 两种 LLM 后端。
优先级: DEEPSEEK_API_KEY > OPENAI_API_KEY > 本地模式。
"""

import os
from typing import List
from .retriever import SearchResult


SYSTEM_PROMPT = """你是一个知识助手，请严格基于提供的参考文档来回答问题。

要求：
1. 只能使用参考文档中的信息来回答，禁止编造文档中没有的内容。
2. 充分利用所有提供的参考文档，提取关键信息组织成完整、详实的回答。
3. 使用结构化格式：先给出总结段落，再分点展开细节，每点标注来源文档。
4. 如果参考文档不足以回答问题，明确说明"根据现有资料无法回答"。
5. 回答字数不少于150字，确保覆盖问题的各个维度。"""


USER_PROMPT_TMPL = """以下是参考文档：

{context}

问题：{query}

请按照要求给出详细回答。"""


# LLM 后端配置
PROVIDERS = {
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "label": "LLM (DeepSeek)",
    },
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "base_url": None,
        "model": "gpt-4o-mini",
        "label": "LLM (OpenAI)",
    },
}


class Generator:
    """答案生成器，自动检测可用的 LLM 后端"""

    def __init__(self):
        self.provider = self._detect_provider()

    def _detect_provider(self) -> dict | None:
        for name in ["deepseek", "openai"]:
            cfg = PROVIDERS[name]
            if os.environ.get(cfg["env_key"]):
                return cfg
        return None

    @property
    def mode_label(self) -> str:
        if self.provider:
            return self.provider["label"]
        return "本地检索"

    @property
    def use_llm(self) -> bool:
        return self.provider is not None

    def generate(self, query: str, results: List[SearchResult], context: str) -> str:
        if self.provider:
            try:
                return self._generate_llm(query, context)
            except Exception as e:
                return (
                    f"⚠ LLM 调用失败: {e}\n\n"
                    f"{self._generate_local(query, results, context)}"
                )
        else:
            return self._generate_local(query, results, context)

    def _generate_llm(self, query: str, context: str) -> str:
        from openai import OpenAI

        cfg = self.provider
        kwargs = {"api_key": os.environ[cfg["env_key"]]}
        if cfg["base_url"]:
            kwargs["base_url"] = cfg["base_url"]

        client = OpenAI(**kwargs)
        user_content = USER_PROMPT_TMPL.format(context=context, query=query)

        response = client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=2048,
        )
        return response.choices[0].message.content

    def _generate_local(
        self, query: str, results: List[SearchResult], context: str
    ) -> str:
        if not results:
            return "（未找到相关文档）"

        lines = [
            "=" * 60,
            f"📝 问题: {query}",
            "=" * 60,
            "",
            f"🔍 检索到 {len(results)} 个相关文档片段：",
            "",
        ]
        for i, r in enumerate(results, 1):
            lines.append(f"--- 片段 {i} (来源: {r.source}, 相关度: {r.score:.4f}) ---")
            lines.append(r.text)
            lines.append("")

        lines.extend([
            "-" * 60,
            "💡 提示: 设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 可启用 LLM 智能回答。",
            '   $env:DEEPSEEK_API_KEY="sk-..." (PowerShell)',
        ])
        return "\n".join(lines)
