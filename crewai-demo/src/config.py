"""
统一配置模块 —— 支持 OpenAI / DeepSeek / Anthropic 多 Provider 切换
用于 CrewAI 的 LLM 配置
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_llm(model_name: str = None, temperature: float = None):
    """
    获取 LLM 实例，供 CrewAI Agent 使用

    CrewAI 支持任何 LangChain 兼容的 LLM。
    通过环境变量 LLM_PROVIDER 切换 provider。

    返回:
        LangChain ChatModel 实例
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    temp = temperature if temperature is not None else float(os.getenv("TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("MAX_TOKENS", "4096"))

    if provider == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            temperature=temp,
            max_tokens=max_tokens,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=temp,
            max_tokens=max_tokens,
        )
    else:
        # 默认 OpenAI
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            temperature=temp,
            max_tokens=max_tokens,
        )


def get_crewai_config() -> dict:
    """获取 CrewAI 运行配置"""
    return {
        "process": os.getenv("CREWAI_PROCESS", "sequential"),
        "verbose": os.getenv("CREWAI_VERBOSE", "true").lower() == "true",
        "memory": os.getenv("CREWAI_MEMORY", "false").lower() == "true",
    }
