from __future__ import annotations

import pytest

from src.settings import load_settings


def test_load_settings_reads_ranges_and_domains(env_defaults, monkeypatch):
    monkeypatch.setenv("BEFORE_DAYS", "10")
    monkeypatch.setenv("NEWS_INCLUDE_DOMAINS", "techcrunch.com, theverge.com")
    monkeypatch.setenv("NEWS_EXCLUDE_DOMAINS", "wikipedia.org")

    settings = load_settings()

    assert settings.before_days == 10
    assert settings.include_domains == ("techcrunch.com", "theverge.com")
    assert settings.exclude_domains == ("wikipedia.org",)
    assert settings.data_dir == env_defaults


def test_invalid_provider_is_rejected(env_defaults, monkeypatch):
    monkeypatch.setenv("PROVIDER_LLM", "openai")

    with pytest.raises(ValueError, match="PROVIDER_LLM invalido"):
        load_settings()


def test_before_days_out_of_range(env_defaults, monkeypatch):
    monkeypatch.setenv("BEFORE_DAYS", "99")

    with pytest.raises(ValueError, match="BEFORE_DAYS"):
        load_settings()


def test_validate_for_workflow_requires_secrets(env_defaults, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "")
    settings = load_settings()

    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        settings.validate_for_workflow(skip_email=True)


def test_validate_for_workflow_skips_resend_on_dry_run(env_defaults, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "")
    settings = load_settings()

    settings.validate_for_workflow(skip_email=True)

    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        settings.validate_for_workflow(skip_email=False)


def test_formatter_model_accepts_corrected_env_name(env_defaults, monkeypatch):
    monkeypatch.setenv("MODEL_AGENT_FORMATTER", "gemini-custom")
    monkeypatch.delenv("MODEL_AGENT_FORMATER", raising=False)

    settings = load_settings()

    assert settings.model_agent_formater == "gemini-custom"


def test_load_settings_reads_llm_timeout_seconds(env_defaults, monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "450")
    settings = load_settings()
    assert settings.llm_timeout_seconds == 450
