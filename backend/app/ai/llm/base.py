from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class LLMConfig:
    model: str
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 60
    streaming: bool = False


class BaseLLMProvider(ABC):
    """
    Abstract interface for all LLM providers.
    Agents only depend on this interface — never on a concrete provider.
    Swap Groq → OpenAI → Ollama by implementing this class.
    """

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """Single-turn completion."""

    @abstractmethod
    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[str]:
        """Streaming completion — yields text chunks."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Returns True if the provider is reachable."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
