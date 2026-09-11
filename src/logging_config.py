from __future__ import annotations

import logging
import os
import sys

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
APP_LOGGER_NAME = "src"

_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "urllib3",
    "openai",
    "langchain",
    "langchain_core",
    "langchain_google_genai",
    "langchain_ollama",
    "langgraph",
    "google",
    "tavily",
)


def resolve_log_level(level: str | None = None) -> int:
    raw_value = (level or os.getenv("LOG_LEVEL") or DEFAULT_LOG_LEVEL).strip().upper()
    numeric = getattr(logging, raw_value, None)
    if not isinstance(numeric, int):
        return logging.INFO
    return numeric


def setup_logging(level: str | None = None) -> None:
    numeric = resolve_log_level(level)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=numeric,
            format=DEFAULT_FORMAT,
            datefmt=DATE_FORMAT,
            stream=sys.stdout,
        )
    else:
        root.setLevel(numeric)

    logging.getLogger(APP_LOGGER_NAME).setLevel(numeric)

    library_level = logging.DEBUG if numeric <= logging.DEBUG else logging.WARNING
    for logger_name in _NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(library_level)
