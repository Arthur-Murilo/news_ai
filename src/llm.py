from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

from src.settings import (
    DEFAULT_GOOGLE_MODEL,
    DEFAULT_OLLAMA_MODEL,
    SUPPORTED_PROVIDERS,
    load_settings,
)

logger = logging.getLogger(__name__)

LLM_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 2.0

_TRANSIENT_TYPE_NAMES = frozenset(
    {
        "BrokenPipeError",
        "ConnectError",
        "ConnectTimeout",
        "ConnectionAbortedError",
        "ConnectionResetError",
        "LocalProtocolError",
        "NetworkError",
        "PoolTimeout",
        "ReadError",
        "ReadTimeout",
        "RemoteProtocolError",
        "TimeoutException",
        "WriteError",
        "WriteTimeout",
    }
)

# Re-exported for existing imports and tests.
__all__ = [
    "DEFAULT_GOOGLE_MODEL",
    "DEFAULT_OLLAMA_MODEL",
    "SUPPORTED_PROVIDERS",
    "call_with_retries",
    "create_chat_model",
    "describe_llm_error",
    "is_transient_llm_error",
]


def is_transient_llm_error(exc: BaseException) -> bool:
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        winerror = getattr(current, "winerror", None)
        errno = getattr(current, "errno", None)
        if winerror == 10054 or errno in {54, 104}:
            return True
        if type(current).__name__ in _TRANSIENT_TYPE_NAMES:
            return True
        message = str(current).lower()
        if (
            "10054" in message
            or "connection reset" in message
            or "forcado o cancelamento" in message
            or "forçado o cancelamento" in message
            or "connection aborted" in message
            or "server disconnected" in message
        ):
            return True
        current = current.__cause__ or current.__context__
    return False


def describe_llm_error(exc: BaseException) -> str:
    if is_transient_llm_error(exc):
        return (
            "A conexao com o LLM foi encerrada pelo host remoto "
            f"({type(exc).__name__}: {exc}). "
            "Tente novamente; se persistir, o modelo pode estar demorando demais "
            "na sintese final."
        )
    return str(exc)


def call_with_retries[T](
    operation: Callable[[], T],
    *,
    attempts: int = LLM_RETRY_ATTEMPTS,
    delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
    what: str = "LLM",
) -> T:
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_exc = exc
            if not is_transient_llm_error(exc) or attempt >= attempts:
                raise
            wait_for = delay_seconds * attempt
            logger.warning(
                "%s falhou por erro transiente (%s/%s): %s. Nova tentativa em %.1fs.",
                what,
                attempt,
                attempts,
                exc,
                wait_for,
            )
            if wait_for > 0:
                time.sleep(wait_for)
    assert last_exc is not None
    raise last_exc


def _get_ollama_client_kwargs(api_key: str, timeout: int = 300) -> Mapping[str, Any]:
    client_kwargs: dict[str, Any] = {
        "timeout": httpx.Timeout(
            connect=20.0,
            read=float(timeout),
            write=60.0,
            pool=20.0,
        )
    }
    if api_key:
        # Needed when using Ollama Cloud directly at https://ollama.com.
        client_kwargs["headers"] = {"Authorization": f"Bearer {api_key}"}
    return client_kwargs


def create_chat_model(model_env_var: str):
    settings = load_settings()
    settings.validate_for_workflow(skip_email=True)

    if model_env_var == "MODEL_AGENT_FORMATER":
        model_name = settings.model_agent_formater
    elif model_env_var == "MODEL_AGENT_SEARCH":
        model_name = settings.model_agent_search
    else:
        model_name = settings.model_agent_search

    max_output_tokens = settings.llm_max_output_tokens
    logger.info(
        "Criando modelo %s via %s (max_output_tokens=%s timeout=%ss)",
        model_name,
        settings.provider_llm,
        max_output_tokens,
        settings.llm_timeout_seconds,
    )

    if settings.provider_llm == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            max_tokens=max_output_tokens,
            timeout=float(settings.llm_timeout_seconds),
            max_retries=3,
        )

    from langchain_ollama import ChatOllama

    client_kwargs = dict(
        _get_ollama_client_kwargs(
            settings.ollama_api_key,
            timeout=settings.llm_timeout_seconds,
        )
    )
    kwargs: dict[str, Any] = {
        "model": model_name,
        "temperature": 0.3,
        "num_predict": max_output_tokens,
    }

    if settings.ollama_base_url:
        kwargs["base_url"] = settings.ollama_base_url.rstrip("/")

    if client_kwargs:
        kwargs["client_kwargs"] = client_kwargs

    return ChatOllama(**kwargs)
