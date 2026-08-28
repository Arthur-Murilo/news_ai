from __future__ import annotations

from src.agents.tools.search_tool import (
    _official_published_date,
    _parse_date,
    search_new,
)


def test_parse_date_supports_iso_and_portuguese():
    assert str(_parse_date("2026-08-20T13:00:00Z")) == "2026-08-20"
    assert str(_parse_date("20/08/2026")) == "2026-08-20"
    assert str(_parse_date("Publicado em 20 de agosto de 2026")) == "2026-08-20"
    assert _parse_date("sem data") is None


def test_official_published_date_ignores_body_text():
    result = {
        "title": "Algo aconteceu em 12 de maio de 2023",
        "content": "Publicado em 12 de maio de 2023, mas isso e historico.",
        "url": "https://example.com/news",
    }
    assert _official_published_date(result) is None

    result["published_date"] = "2026-08-20"
    assert str(_official_published_date(result)) == "2026-08-20"


def test_search_filters_unsafe_urls_without_leaking_them(env_defaults, monkeypatch):
    captured = {}

    class FakeClient:
        def search(self, **kwargs):
            captured.update(kwargs)
            return {
                "results": [
                    {
                        "title": "Interno",
                        "url": "http://127.0.0.1/admin",
                        "published_date": "2026-08-20",
                    },
                    {
                        "title": "Fora da janela",
                        "url": "https://example.com/old",
                        "published_date": "2026-01-01",
                    },
                    {
                        "title": "Sem data oficial",
                        "url": "https://example.com/today",
                        "content": "Publicado em 01 de janeiro de 2020",
                    },
                    {
                        "title": "Atual",
                        "url": "https://example.com/fresh",
                        "published_date": "2026-08-20",
                    },
                ],
                "images": ["http://localhost/x.png", "https://example.com/img.png"],
            }

    monkeypatch.setattr(
        "src.agents.tools.search_tool._get_client",
        lambda: FakeClient(),
    )

    response = search_new.invoke(
        {
            "query": "IA",
            "today": "2026-08-22",
            "before_days": 7,
            "max_results": 10,
        }
    )

    titles = [item["title"] for item in response["results"]]
    assert titles == ["Sem data oficial", "Atual"]
    assert response["images"] == ["https://example.com/img.png"]
    assert any(
        item["reason"] == "unsafe_source_url"
        for item in response["filtered_out_by_date"]
    )
    assert all(
        "url" not in item
        for item in response["filtered_out_by_date"]
        if item["reason"] == "unsafe_source_url"
    )
    assert captured["start_date"] == "2026-08-15"
    assert captured["end_date"] == "2026-08-22"


def test_search_passes_optional_domain_filters(env_defaults, monkeypatch):
    monkeypatch.setenv("NEWS_INCLUDE_DOMAINS", "example.com")
    monkeypatch.setenv("NEWS_EXCLUDE_DOMAINS", "spam.test")
    captured = {}

    class FakeClient:
        def search(self, **kwargs):
            captured.update(kwargs)
            return {"results": [], "images": []}

    monkeypatch.setattr(
        "src.agents.tools.search_tool._get_client",
        lambda: FakeClient(),
    )

    search_new.invoke({"query": "IA", "today": "2026-08-22"})

    assert captured["include_domains"] == ["example.com"]
    assert captured["exclude_domains"] == ["spam.test"]
