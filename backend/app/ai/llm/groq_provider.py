import time
from typing import AsyncIterator, Optional
from groq import AsyncGroq
from groq import APIConnectionError, APITimeoutError, RateLimitError

from app.ai.llm.base import BaseLLMProvider, LLMConfig, LLMResponse
from app.ai.logging.logger import AILogger
from app.core.config import settings

logger = AILogger("llm.groq")


class GroqProvider(BaseLLMProvider):
    """
    Groq LLM provider.
    Implements BaseLLMProvider — agents never import this class directly.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or settings.GROQ_API_KEY
        if not key:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
        self._client = AsyncGroq(api_key=key)
        self._default_config = LLMConfig(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
            streaming=settings.LLM_STREAMING,
        )

    @property
    def provider_name(self) -> str:
        return "groq"

    def _cfg(self, config: Optional[LLMConfig]) -> LLMConfig:
        return config or self._default_config

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        cfg = self._cfg(config)
        start = time.perf_counter()
        logger.llm_call(model=cfg.model)

        response = await self._client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout=cfg.timeout,
            stream=False,
        )

        elapsed = (time.perf_counter() - start) * 1000
        usage = response.usage
        result = LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            finish_reason=response.choices[0].finish_reason,
        )
        logger.llm_response(
            model=cfg.model,
            completion_tokens=result.completion_tokens,
            elapsed_ms=elapsed,
        )
        return result

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[str]:
        cfg = self._cfg(config)
        logger.llm_call(model=cfg.model, streaming=True)

        response = await self._client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout=cfg.timeout,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def health_check(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self._default_config.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except (APIConnectionError, APITimeoutError, RateLimitError) as e:
            logger.error("Groq health check failed", error=str(e))
            return False
        except Exception as e:
            logger.error("Groq health check unexpected error", error=str(e))
            return False
