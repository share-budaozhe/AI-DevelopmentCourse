"""
LangChain Demo 统一配置模块

支持 OpenAI 和 DeepSeek 两种 LLM 后端:
  - 默认使用 OpenAI (model: gpt-4o-mini)
  - 设置 LLM_PROVIDER=deepseek 即可切换到 DeepSeek

环境变量:
  LLM_PROVIDER       -- 选择后端: openai (默认) / deepseek
  OPENAI_API_KEY     -- OpenAI API Key
  OPENAI_BASE_URL    -- OpenAI 接口地址 (默认 https://api.openai.com/v1)
  DEEPSEEK_API_KEY   -- DeepSeek API Key
  DEEPSEEK_BASE_URL  -- DeepSeek 接口地址 (默认 https://api.deepseek.com)
  OPENAI_MODEL       -- 模型名 (默认 gpt-4o-mini)
  DEEPSEEK_MODEL     -- DeepSeek 模型名 (默认 deepseek-chat)
"""

import os as _os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

# ==== 配置项 ====
PROVIDER = _os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI 配置
OPENAI_API_KEY = _os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = _os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = _os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# DeepSeek 配置 (兼容 OpenAI API 协议)
DEEPSEEK_API_KEY = _os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = _os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = _os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def get_llm(temperature=0, **kwargs):
    """获取 LLM 实例，根据 LLM_PROVIDER 自动选择后端。

    使用示例:
        llm = get_llm()                  # 使用默认 temperature
        llm = get_llm(temperature=0.7)   # 指定 temperature
    """
    if PROVIDER == "deepseek":
        api_key = DEEPSEEK_API_KEY
        base_url = DEEPSEEK_BASE_URL
        model = DEEPSEEK_MODEL
    else:
        api_key = OPENAI_API_KEY
        base_url = OPENAI_BASE_URL
        model = OPENAI_MODEL

    if not api_key:
        raise RuntimeError(
            f"未设置 {PROVIDER.upper()}_API_KEY 环境变量。"
            f"请在 .env 文件中配置。"
        )

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=api_key,
        base_url=base_url,
        **kwargs
    )


def get_embeddings(model=None, **kwargs):
    """获取 Embeddings 实例。

    注意: DeepSeek 目前不提供 Embedding API，
    使用 DeepSeek 时仍会调用 OpenAI Embedding API。
    """
    if model is None:
        model = "text-embedding-3-small"

    # Embedding 目前只支持 OpenAI (DeepSeek 无 Embedding API)
    api_key = OPENAI_API_KEY
    base_url = OPENAI_BASE_URL

    if not api_key:
        raise RuntimeError(
            "未设置 OPENAI_API_KEY 环境变量。Embedding 需要 OpenAI API。"
        )

    return OpenAIEmbeddings(
        model=model,
        openai_api_key=api_key,
        base_url=base_url,
        **kwargs
    )


def check_api_key():
    """检查必需的 API Key 是否已配置，返回 (is_ok, message)"""
    if PROVIDER == "deepseek":
        if not DEEPSEEK_API_KEY:
            return False, "请设置 DEEPSEEK_API_KEY"
    else:
        if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your-"):
            return False, "请设置 OPENAI_API_KEY"
    return True, "OK"


def print_config():
    """打印当前配置信息 (隐藏 Key)"""
    print(f"LLM 后端: {PROVIDER}")
    if PROVIDER == "deepseek":
        print(f"模型: {DEEPSEEK_MODEL}")
        key_preview = DEEPSEEK_API_KEY[:10] + "..." if DEEPSEEK_API_KEY else "(未设置)"
        print(f"Key:  {key_preview}")
    else:
        print(f"模型: {OPENAI_MODEL}")
        key_preview = OPENAI_API_KEY[:10] + "..." if OPENAI_API_KEY else "(未设置)"
        print(f"Key:  {key_preview}")
    print(f"Embedding 模型: text-embedding-3-small")
