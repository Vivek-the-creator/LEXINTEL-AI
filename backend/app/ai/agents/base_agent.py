import time
import re
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, AsyncIterator

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.ai.llm.base import BaseLLMProvider, LLMConfig, LLMResponse
from app.ai.llm.service import get_llm_provider
from app.ai.prompts.registry import prompt_registry, Prompt
from app.ai.orchestrator.state import LexIntelState, AgentError, AgentExecutionMeta
from app.ai.logging.logger import AILogger
from app.core.config import settings


class AgentExecutionError(Exception):
    """Raised when an agent fails after all retries."""
    def __init__(self, agent: str, message: str, recoverable: bool = True):
        super().__init__(message)
        self.agent = agent
        self.recoverable = recoverable


class BaseAgent(ABC):
    """
    Abstract base for every LexIntel AI agent.

    Subclasses implement only `execute()` — all infrastructure
    (logging, retries, timing, error isolation, state management) is here.
    """

    # Override in subclass
    agent_name: str = "base_agent"
    prompt_name: str = ""

    def __init__(
        self,
        llm: Optional[BaseLLMProvider] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        self._llm = llm or get_llm_provider()
        self._llm_config = llm_config or LLMConfig(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
            streaming=settings.LLM_STREAMING,
        )
        self._logger = AILogger(f"agent.{self.agent_name}")

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self, state: LexIntelState) -> LexIntelState:
        """
        Called by LangGraph. Wraps execute() with full observability.
        Never override this — override execute() instead.
        """
        session_id = state["session_id"]
        start = time.perf_counter()
        self._logger.agent_start(self.agent_name, session_id)

        meta: AgentExecutionMeta = {
            "agent": self.agent_name,
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": None,
            "elapsed_ms": None,
            "status": "running",
        }
        state["agent_executions"] = [*state.get("agent_executions", []), meta]

        try:
            state = await self._execute_with_retry(state)
            elapsed = (time.perf_counter() - start) * 1000
            meta.update(
                finished_at=datetime.utcnow().isoformat(),
                elapsed_ms=round(elapsed, 2),
                status="done",
            )
            self._logger.agent_end(self.agent_name, session_id, elapsed)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            recoverable = getattr(exc, "recoverable", True)
            meta.update(
                finished_at=datetime.utcnow().isoformat(),
                elapsed_ms=round(elapsed, 2),
                status="failed",
            )
            error: AgentError = {
                "agent": self.agent_name,
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
                "recoverable": recoverable,
            }
            state["errors"] = [*state.get("errors", []), error]
            self._logger.agent_error(self.agent_name, session_id, str(exc))

            if not recoverable:
                raise

        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    # ── Retry wrapper ─────────────────────────────────────────────────────────

    async def _execute_with_retry(self, state: LexIntelState) -> LexIntelState:
        max_attempts = settings.LLM_MAX_RETRIES
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                return await self.execute(state)
            except AgentExecutionError:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts:
                    self._logger.retry(attempt, max_attempts, str(exc))
                    await self._sleep(attempt)
        raise AgentExecutionError(self.agent_name, str(last_exc), recoverable=True)

    async def _sleep(self, attempt: int):
        import asyncio
        await asyncio.sleep(min(2 ** attempt, 30))

    # ── Abstract method ───────────────────────────────────────────────────────

    @abstractmethod
    async def execute(self, state: LexIntelState) -> LexIntelState:
        """Agent-specific logic. Receives and returns the shared state."""

    # ── Helpers available to all subclasses ───────────────────────────────────

    def get_prompt(self) -> Prompt:
        return prompt_registry.get(self.prompt_name)

    async def invoke_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        return await self._llm.complete(system_prompt, user_prompt, config or self._llm_config)

    async def stream_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[str]:
        async for chunk in self._llm.stream(system_prompt, user_prompt, config or self._llm_config):
            yield chunk

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Basic input sanitization before sending to LLM."""
        text = text.strip()
        # Remove null bytes and control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Truncate to 32k chars to avoid token overflow
        return text[:32_000]

    @staticmethod
    def parse_json_response(content: str) -> Dict[str, Any]:
        """Safely extract JSON from LLM response."""
        # Try direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        # Try extracting from markdown code block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # Try finding first {...} block
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {"raw_response": content}
