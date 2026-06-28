"""
统一配置模块 —— 支持 OpenAI 与 DeepSeek 切换
"""
import os
from dotenv import load_dotenv

load_dotenv()

def get_llm(model_name: str = None, temperature: float = None):
    """获取配置的 LLM 实例"""
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
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            temperature=temp,
            max_tokens=max_tokens,
        )
