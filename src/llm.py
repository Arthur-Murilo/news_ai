import logging
from collections.abc import Mapping
from typing import Any

from src.settings import (
    DEFAULT_GOOGLE_MODEL,
    DEFAULT_OLLAMA_MODEL,
    SUPPORTED_PROVIDERS,
    load_settings,
)

logger = logging.getLogger(__name__)

# Re-exported for existing imports and tests.
__all__ = [
    "DEFAULT_GOOGLE_MODEL",
    "DEFAULT_OLLAMA_MODEL",
    "SUPPORTED_PROVIDERS",
    "create_chat_model",
]


def _get_ollama_client_kwargs(api_key: str, timeout: int = 300) -> Mapping[str, Any]:
    client_kwargs: dict[str, Any] = {"timeout": timeout}
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
