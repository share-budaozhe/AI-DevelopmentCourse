"""
═══════════════════════════════════════════════════════════════
  🔧 LlamaIndex 学习教程 — src/config.py
  LLM 与 Embedding 配置中心

  支持:
  - DeepSeek (LLM) + MockEmbedding (演示)
  - DeepSeek (LLM) + HuggingFace (本地嵌入)
  - OpenAI (LLM + Embedding)
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(Path(__file__).parent.parent / ".env")


def get_deepseek_llm():
    """获取 DeepSeek LLM（兼容 OpenAI API）。

    DeepSeek 模型:
    - deepseek-chat      （通用对话，性价比最高）
    - deepseek-reasoner  （推理增强，DeepSeek-R1）

    需要在 .env 中设置：
    DEEPSEEK_API_KEY=sk-xxx
    """
    from llama_index.llms.openai import OpenAI

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    return OpenAI(
        model="deepseek-chat",
        api_key=api_key,
        api_base="https://api.deepseek.com",
        temperature=0.1,
        max_tokens=1024,
    )


def get_openai_llm():
    """获取 OpenAI LLM。

    需要在 .env 中设置：
    OPENAI_API_KEY=sk-xxx
    """
    from llama_index.llms.openai import OpenAI

    return OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY", ""),
        temperature=0.1,
        max_tokens=1024,
    )


def get_openai_embedding():
    """获取 OpenAI 嵌入模型。

    需要在 .env 中设置：
    OPENAI_API_KEY=sk-xxx
    """
    from llama_index.embeddings.openai import OpenAIEmbedding

    return OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )


def get_mock_embedding():
    """获取 Mock 嵌入模型（零成本演示）。"""
    from llama_index.core import MockEmbedding
    return MockEmbedding(embed_dim=384)


def get_local_embedding():
    """获取本地 HuggingFace 嵌入模型（免费，无需 API 密钥）。

    首次运行会自动下载模型（约 90MB）。
    推荐模型：
    - BAAI/bge-small-zh-v1.5   （中文专用，轻量）
    - sentence-transformers/all-MiniLM-L6-v2 （英文轻量）
    """
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(
        model_name="BAAI/bge-small-zh-v1.5",
    )


def setup_deepseek():
    """配置 DeepSeek + Mock Embedding（演示模式，零嵌入成本）。

    使用场景：只想体验 LLM 对话，不需要真实向量检索。
    """
    from llama_index.core import Settings

    Settings.llm = get_deepseek_llm()
    Settings.embed_model = get_mock_embedding()
    print("[config] ✅ DeepSeek LLM + MockEmbedding 已配置")


def setup_deepseek_full():
    """配置 DeepSeek + 本地 HuggingFace 嵌入（全功能，免费）。

    使用场景：完整的 RAG 体验，包括真实的向量检索。
    LLM 用 DeepSeek（便宜），嵌入用本地模型（免费）。
    """
    from llama_index.core import Settings

    Settings.llm = get_deepseek_llm()
    Settings.embed_model = get_local_embedding()
    print("[config] ✅ DeepSeek LLM + HuggingFace Embedding 已配置")


def setup_openai():
    """配置 OpenAI LLM + OpenAI 嵌入（全托管，最省心）。"""
    from llama_index.core import Settings

    Settings.llm = get_openai_llm()
    Settings.embed_model = get_openai_embedding()
    print("[config] ✅ OpenAI LLM + OpenAI Embedding 已配置")


def setup_mock():
    """纯 Mock 模式（不需要任何 API 密钥）。

    索引创建和结构演示完全可用，但 LLM 查询不可用。
    """
    from llama_index.core import Settings

    Settings.embed_model = get_mock_embedding()
    Settings.llm = None  # LLM 查询不可用
    print("[config] ✅ Mock 模式已配置（无 API 需求）")


def auto_setup():
    """自动检测环境变量并配置。

    优先级：DeepSeek > OpenAI > Mock
    """
    if os.getenv("DEEPSEEK_API_KEY"):
        if os.getenv("USE_LOCAL_EMBEDDING"):
            setup_deepseek_full()
        else:
            setup_deepseek()
        return "deepseek"
    elif os.getenv("OPENAI_API_KEY"):
        setup_openai()
        return "openai"
    else:
        setup_mock()
        return "mock"


# ═══════════════════════════════════════════════════════════════
# 使用示例
# ═══════════════════════════════════════════════════════════════

def print_config_guide():
    """打印配置指南。"""
    guide = """
╔══════════════════════════════════════════════════════════════╗
║              🔧 API 配置指南                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  方案 1：DeepSeek（推荐，最便宜）                             ║
║  ─────────────────────────────────────                       ║
║  创建 .env 文件，写入：                                       ║
║    DEEPSEEK_API_KEY=sk-xxx                                   ║
║                                                              ║
║  LLM 费用：DeepSeek ≈ ￥1/百万 token                         ║
║  嵌入方案：本地 HuggingFace 模型（免费）                      ║
║                                                              ║
║  方案 2：OpenAI                                               ║
║  ─────────────────────────────────────                       ║
║  创建 .env 文件，写入：                                       ║
║    OPENAI_API_KEY=sk-xxx                                     ║
║                                                              ║
║  方案 3：无 API（仅结构演示）                                 ║
║  ─────────────────────────────────────                       ║
║  无需任何配置，MockEmbedding 模式自动启用                      ║
║                                                              ║
║  切换本地嵌入（免费）：                                       ║
║    USE_LOCAL_EMBEDDING=true                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(guide)


if __name__ == "__main__":
    print_config_guide()
    mode = auto_setup()
    print(f"\n  当前模式: {mode}")
