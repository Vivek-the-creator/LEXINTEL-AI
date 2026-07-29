from typing import Optional
from app.ai.llm.base import BaseLLMProvider
from app.core.config import settings

_provider: Optional[BaseLLMProvider] = None


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory that returns the configured LLM provider singleton.
    Agents call this — never instantiate providers directly.
    Adding a new provider only requires updating this factory.
    """
    global _provider
    if _provider is not None:
        return _provider

    name = settings.LLM_PROVIDER.lower()

    if name == "groq":
        from app.ai.llm.groq_provider import GroqProvider
        _provider = GroqProvider()
        return _provider

    # Future providers:
    # if name == "openai":
    #     from app.ai.llm.openai_provider import OpenAIProvider
    #     _provider = OpenAIProvider()
    #     return _provider

    raise ValueError(f"Unsupported LLM provider: '{name}'")


def reset_llm_provider() -> None:
    """Force re-initialization on next call. Useful for config changes."""
    global _provider
    _provider = None
