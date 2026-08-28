from __future__ import annotations

from src.research import NoticiaValidada
from src.sent_news import (
    SentNewsItem,
    SentNewsStore,
    filter_already_sent,
    normalize_news_url,
)


def test_normalize_news_url_strips_slash_and_host_case():
    assert normalize_news_url("HTTPS://Example.com/News/") == "https://example.com/News"


def test_store_marks_and_detects_sent_urls(tmp_path):
    store = SentNewsStore(tmp_path / "sent_news.json")
    store.mark_sent(
        [
            SentNewsItem(
                url="https://Example.com/a/", title="A", sent_at="2026-08-22T17:00:00"
            )
        ]
    )

    assert store.already_sent("https://example.com/a")
    assert not store.already_sent("https://example.com/b")


def test_filter_already_sent_drops_known_links(tmp_path):
    store = SentNewsStore(tmp_path / "sent_news.json")
    store.mark_sent(
        [
            SentNewsItem(
                url="https://example.com/old",
                title="Old",
                sent_at="2026-08-21T17:00:00",
            )
        ]
    )
    kept, dropped = filter_already_sent(
        [
            NoticiaValidada(titulo="Old", link="https://example.com/old"),
            NoticiaValidada(titulo="New", link="https://example.com/new"),
        ],
        store,
    )

    assert [item.titulo for item in kept] == ["New"]
    assert dropped == ["Old"]
