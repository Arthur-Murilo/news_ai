from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from src.settings import APP_TIMEZONE, load_settings


def normalize_news_url(url: str) -> str:
    candidate = (url or "").strip()
    if not candidate:
        return ""

    parsed = urlsplit(candidate)
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        return candidate.rstrip("/")

    path = parsed.path.rstrip("/") or "/"
    scheme = parsed.scheme.lower() or "https"
    return urlunsplit((scheme, host, path, parsed.query, ""))


def _store_path(path: Path | None = None) -> Path:
    if path is not None:
        return path
    return load_settings().data_dir / "sent_news.json"


def _read_store(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"items": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"items": []}
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        return {"items": []}
    return payload


@dataclass(frozen=True)
class SentNewsItem:
    url: str
    title: str
    sent_at: str


class SentNewsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = _store_path(path)

    def _items(self) -> list[dict[str, Any]]:
        return list(_read_store(self.path).get("items", []))

    def known_urls(self) -> set[str]:
        return {
            normalize_news_url(str(item.get("url", "")))
            for item in self._items()
            if item.get("url")
        }

    def already_sent(self, url: str) -> bool:
        normalized = normalize_news_url(url)
        if not normalized:
            return False
        return normalized in self.known_urls()

    def mark_sent(self, items: list[SentNewsItem]) -> None:
        if not items:
            return

        current = _read_store(self.path)
        known = {
            normalize_news_url(str(item.get("url", "")))
            for item in current["items"]
            if item.get("url")
        }
        changed = False

        for item in items:
            normalized = normalize_news_url(item.url)
            if not normalized or normalized in known:
                continue
            current["items"].append(
                {
                    "url": normalized,
                    "title": item.title,
                    "sent_at": item.sent_at,
                }
            )
            known.add(normalized)
            changed = True

        if not changed:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(current, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def filter_already_sent(
    noticias: list[Any], store: SentNewsStore | None = None
) -> tuple[list[Any], list[str]]:
    news_store = store or SentNewsStore()
    kept = []
    dropped: list[str] = []

    for noticia in noticias:
        link = getattr(noticia, "link", "") or ""
        titulo = getattr(noticia, "titulo", "") or ""
        if link and news_store.already_sent(link):
            dropped.append(titulo or link)
            continue
        kept.append(noticia)

    return kept, dropped


def mark_research_as_sent(
    payload: dict[str, Any], store: SentNewsStore | None = None
) -> None:
    news_store = store or SentNewsStore()
    sent_at = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    items = []

    for raw in payload.get("noticias", []):
        if not isinstance(raw, dict):
            continue
        url = str(raw.get("link", "")).strip()
        title = str(raw.get("titulo", "")).strip()
        if url:
            items.append(SentNewsItem(url=url, title=title, sent_at=sent_at))

    news_store.mark_sent(items)
