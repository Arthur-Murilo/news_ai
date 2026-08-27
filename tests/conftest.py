from __future__ import annotations

import pytest


@pytest.fixture
def env_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("PROVIDER_LLM", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("NEWSLETTER_FROM_EMAIL", "from@example.com")
    monkeypatch.setenv("NEWSLETTER_TO_EMAIL", "to@example.com")
    monkeypatch.setenv("SUBJECT", "Inteligencia Artificial")
    monkeypatch.setenv("BEFORE_DAYS", "7")
    monkeypatch.setenv("MAX_SEARCH_RESULTS", "15")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NEWSLETTER_PREVIEW_PATH", str(tmp_path / "preview.html"))
    monkeypatch.setenv("SCHEDULE_FREQUENCY", "daily")
    monkeypatch.setenv("SCHEDULE_HOUR", "17")
    return tmp_path
