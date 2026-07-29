import logging
import time
import json
from contextlib import contextmanager
from typing import Any, Optional
from functools import wraps


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger


def get_ai_logger(name: str) -> logging.Logger:
    return _build_logger(f"lexintel.ai.{name}")


class AILogger:
    """Structured logger for AI components with timing and metadata support."""

    def __init__(self, component: str):
        self._log = get_ai_logger(component)
        self.component = component

    def _fmt(self, msg: str, **kwargs) -> str:
        if kwargs:
            return f"{msg} | {json.dumps(kwargs, default=str)}"
        return msg

    def info(self, msg: str, **kwargs):
        self._log.info(self._fmt(msg, **kwargs))

    def debug(self, msg: str, **kwargs):
        self._log.debug(self._fmt(msg, **kwargs))

    def warning(self, msg: str, **kwargs):
        self._log.warning(self._fmt(msg, **kwargs))

    def error(self, msg: str, **kwargs):
        self._log.error(self._fmt(msg, **kwargs))

    def agent_start(self, agent: str, session_id: str, **kwargs):
        self.info("Agent started", agent=agent, session_id=session_id, **kwargs)

    def agent_end(self, agent: str, session_id: str, elapsed_ms: float, **kwargs):
        self.info("Agent finished", agent=agent, session_id=session_id, elapsed_ms=round(elapsed_ms, 2), **kwargs)

    def agent_error(self, agent: str, session_id: str, error: str, **kwargs):
        self.error("Agent failed", agent=agent, session_id=session_id, error=error, **kwargs)

    def llm_call(self, model: str, prompt_tokens: Optional[int] = None, **kwargs):
        self.debug("LLM invoked", model=model, prompt_tokens=prompt_tokens, **kwargs)

    def llm_response(self, model: str, completion_tokens: Optional[int] = None, elapsed_ms: float = 0, **kwargs):
        self.debug("LLM responded", model=model, completion_tokens=completion_tokens, elapsed_ms=round(elapsed_ms, 2), **kwargs)

    def retry(self, attempt: int, max_attempts: int, reason: str):
        self.warning("Retrying", attempt=attempt, max_attempts=max_attempts, reason=reason)

    def node_enter(self, node: str, session_id: str):
        self.debug("Graph node entered", node=node, session_id=session_id)

    def node_exit(self, node: str, session_id: str, elapsed_ms: float):
        self.debug("Graph node exited", node=node, session_id=session_id, elapsed_ms=round(elapsed_ms, 2))

    @contextmanager
    def timer(self, label: str, **kwargs):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            self.debug(f"{label} completed", elapsed_ms=round(elapsed, 2), **kwargs)


ai_logger = AILogger("core")
