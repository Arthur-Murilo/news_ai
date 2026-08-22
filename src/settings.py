from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import os

from dotenv import load_dotenv

load_dotenv()

APP_TIMEZONE = ZoneInfo("America/Sao_Paulo")
SUPPORTED_PROVIDERS = {"google", "ollama"}
ALLOWED_SCHEDULE_FREQUENCIES = {"daily", "weekly", "monthly"}

DEFAULT_GOOGLE_MODEL = "gemini-2.5-flash"
DEFAULT_OLLAMA_MODEL = "gpt-oss:120b"
DEFAULT_BEFORE_DAYS = 7
DEFAULT_MAX_RESULTS = 15
MIN_BEFORE_DAYS = 1
MAX_BEFORE_DAYS = 30
MIN_MAX_RESULTS = 1
MAX_MAX_RESULTS = 20
DEFAULT_SUBJECT = "Inteligencia Artificial"


def _read_optional(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"A variavel de ambiente {name} deve ser um numero inteiro."
        ) from exc


def _validate_range(name: str, value: int, minimum: int, maximum: int) -> int:
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} deve estar entre {minimum} e {maximum}.")
    return value


def _split_csv(raw_value: str) -> tuple[str, ...]:
    if not raw_value.strip():
        return ()
    return tuple(
        part.strip()
        for part in raw_value.split(",")
        if part.strip()
    )


@dataclass(frozen=True)
class Settings:
    provider_llm: str
    google_api_key: str
    ollama_base_url: str
    ollama_api_key: str
    model_agent_search: str
    model_agent_formater: str
    subject: str
    before_days: int
    max_search_results: int
    tavily_api_key: str
    resend_api_key: str
    newsletter_from_email: str
    newsletter_to_email: str
    data_dir: Path
    preview_path: Path
    include_domains: tuple[str, ...]
    exclude_domains: tuple[str, ...]
    schedule_frequency: str
    schedule_hour: int
    schedule_weekday: int
    schedule_day: int

    def validate_for_workflow(self, *, skip_email: bool = False) -> None:
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY e obrigatoria.")

        if self.provider_llm == "google" and not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY nao configurada para PROVIDER_LLM=google."
            )

        if self.provider_llm == "ollama" and not self.ollama_base_url:
            raise ValueError(
                "OLLAMA_BASE_URL nao configurada para PROVIDER_LLM=ollama."
            )

        if skip_email:
            return

        if not self.resend_api_key:
            raise ValueError("RESEND_API_KEY e obrigatoria.")
        if not self.newsletter_from_email:
            raise ValueError("NEWSLETTER_FROM_EMAIL e obrigatoria.")
        if not self.newsletter_to_email:
            raise ValueError("NEWSLETTER_TO_EMAIL e obrigatoria.")


def _default_model(provider: str) -> str:
    if provider == "ollama":
        return DEFAULT_OLLAMA_MODEL
    return DEFAULT_GOOGLE_MODEL


def load_settings() -> Settings:
    provider = _read_optional("PROVIDER_LLM", "google").lower()
    if provider not in SUPPORTED_PROVIDERS:
        valid_providers = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(
            f"PROVIDER_LLM invalido: {provider!r}. Use um destes valores: {valid_providers}."
        )

    fallback_model = _read_optional("AI_MODEL", _default_model(provider))
    data_dir = Path(_read_optional("DATA_DIR", ".data"))
    preview_path = Path(
        _read_optional("NEWSLETTER_PREVIEW_PATH", str(data_dir / "preview.html"))
    )

    frequency = _read_optional("SCHEDULE_FREQUENCY", "daily").lower()
    if frequency not in ALLOWED_SCHEDULE_FREQUENCIES:
        raise ValueError("SCHEDULE_FREQUENCY deve ser daily, weekly ou monthly.")

    hour = _validate_range("SCHEDULE_HOUR", _read_int("SCHEDULE_HOUR", 17), 0, 23)
    weekday = _validate_range(
        "SCHEDULE_WEEKDAY",
        _read_int("SCHEDULE_WEEKDAY", 1),
        1,
        7,
    )
    day = _validate_range("SCHEDULE_DAY", _read_int("SCHEDULE_DAY", 1), 1, 31)

    return Settings(
        provider_llm=provider,
        google_api_key=_read_optional("GOOGLE_API_KEY"),
        ollama_base_url=_read_optional("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_api_key=_read_optional("OLLAMA_API_KEY"),
        model_agent_search=_read_optional("MODEL_AGENT_SEARCH", fallback_model),
        model_agent_formater=_read_optional(
            "MODEL_AGENT_FORMATTER",
            _read_optional("MODEL_AGENT_FORMATER", fallback_model),
        ),
        subject=_read_optional("SUBJECT", DEFAULT_SUBJECT),
        before_days=_validate_range(
            "BEFORE_DAYS",
            _read_int("BEFORE_DAYS", DEFAULT_BEFORE_DAYS),
            MIN_BEFORE_DAYS,
            MAX_BEFORE_DAYS,
        ),
        max_search_results=_validate_range(
            "MAX_SEARCH_RESULTS",
            _read_int("MAX_SEARCH_RESULTS", DEFAULT_MAX_RESULTS),
            MIN_MAX_RESULTS,
            MAX_MAX_RESULTS,
        ),
        tavily_api_key=_read_optional("TAVILY_API_KEY"),
        resend_api_key=_read_optional("RESEND_API_KEY"),
        newsletter_from_email=_read_optional("NEWSLETTER_FROM_EMAIL"),
        newsletter_to_email=_read_optional("NEWSLETTER_TO_EMAIL"),
        data_dir=data_dir,
        preview_path=preview_path,
        include_domains=_split_csv(_read_optional("NEWS_INCLUDE_DOMAINS")),
        exclude_domains=_split_csv(_read_optional("NEWS_EXCLUDE_DOMAINS")),
        schedule_frequency=frequency,
        schedule_hour=hour,
        schedule_weekday=weekday,
        schedule_day=day,
    )
