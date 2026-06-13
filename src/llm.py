import os
from collections.abc import Mapping
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEFAULT_GOOGLE_MODEL = "gemini-2.5-flash"
DEFAULT_OLLAMA_MODEL = "gpt-oss:120b"
SUPPORTED_PROVIDERS = {"google", "ollama"}


def _get_provider() -> str:
    provider = os.getenv("PROVIDER_LLM", "google").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        valid_providers = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(
            f"PROVIDER_LLM invalido: {provider!r}. Use um destes valores: {valid_providers}."
        )
    return provider


def _get_default_model(provider: str) -> str:
    if provider == "ollama":
        return DEFAULT_OLLAMA_MODEL
    return DEFAULT_GOOGLE_MODEL


def _get_model_name(model_env_var: str, provider: str) -> str:
    return os.getenv(
        model_env_var,
        os.getenv("AI_MODEL", _get_default_model(provider)),
    )


def _get_ollama_client_kwargs() -> Mapping[str, Any]:
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    if not api_key:
        return {}

    # Needed when using Ollama Cloud directly at https://ollama.com.
    return {"headers": {"Authorization": f"Bearer {api_key}"}}


def create_chat_model(model_env_var: str):
    provider = _get_provider()
    model_name = _get_model_name(model_env_var, provider)

    if provider == "google":
        if not os.getenv("GOOGLE_API_KEY", "").strip():
            raise ValueError(
                "GOOGLE_API_KEY nao configurada para PROVIDER_LLM=google."
            )

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            max_tokens=8000,
        )

    from langchain_ollama import ChatOllama

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
    client_kwargs = dict(_get_ollama_client_kwargs())

    kwargs: dict[str, Any] = {
        "model": model_name,
        "temperature": 0.3,
        "num_predict": 8000,
    }

    if base_url:
        kwargs["base_url"] = base_url.rstrip("/")

    if client_kwargs:
        kwargs["client_kwargs"] = client_kwargs

    return ChatOllama(**kwargs)
