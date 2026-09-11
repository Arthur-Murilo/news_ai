import logging
import re
import unicodedata
from datetime import date, datetime, timedelta

from langchain.tools import tool
from tavily import TavilyClient

from src.security import is_safe_public_url
from src.settings import (
    APP_TIMEZONE,
    DEFAULT_BEFORE_DAYS,
    DEFAULT_MAX_RESULTS,
    MAX_BEFORE_DAYS,
    MAX_MAX_RESULTS,
    MIN_BEFORE_DAYS,
    MIN_MAX_RESULTS,
    load_settings,
)

logger = logging.getLogger(__name__)

_client: TavilyClient | None = None
MAX_RESULT_CONTENT_CHARS = 800
MAX_SEARCH_IMAGES = 5
MAX_FILTERED_OUT_ITEMS = 8
_RESULT_KEYS = (
    "title",
    "url",
    "content",
    "published_date",
    "date",
    "validated_published_date",
    "score",
    "source",
)

MONTHS_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def _validate_range(name: str, value: int, minimum: int, maximum: int) -> int:
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} deve estar entre {minimum} e {maximum}.")
    return value


def _get_client() -> TavilyClient:
    global _client
    api_key = load_settings().tavily_api_key
    if not api_key:
        raise ValueError("TAVILY_API_KEY e obrigatoria.")
    if _client is None:
        _client = TavilyClient(api_key)
    return _client


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def _parse_date(value: object) -> date | None:
    if not value:
        return None

    text = str(value).strip()

    try:
        return datetime.fromisoformat(text[:10]).date()
    except ValueError:
        pass

    match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if match:
        day, month, year = map(int, match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None

    match_named = re.search(
        r"\b(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\b",
        text.lower(),
    )
    if match_named:
        d = int(match_named.group(1))
        m = MONTHS_PT.get(_strip_accents(match_named.group(2)))
        y = int(match_named.group(3))
        if m is not None:
            try:
                return date(y, m, d)
            except ValueError:
                return None

    return None


def _official_published_date(result: dict) -> date | None:
    for field in ("published_date", "date"):
        parsed = _parse_date(result.get(field))
        if parsed:
            return parsed
    return None


def _sanitize_url_list(urls: object) -> list[str]:
    if not isinstance(urls, list):
        return []
    return [url for url in urls if isinstance(url, str) and is_safe_public_url(url)]


def _sanitize_result(result: dict) -> dict | None:
    source_url = result.get("url")
    if not isinstance(source_url, str) or not is_safe_public_url(source_url):
        return None

    sanitized = dict(result)
    sanitized["url"] = source_url

    favicon = sanitized.get("favicon")
    if isinstance(favicon, str) and not is_safe_public_url(favicon):
        sanitized.pop("favicon", None)

    image = sanitized.get("image")
    if isinstance(image, str) and not is_safe_public_url(image):
        sanitized.pop("image", None)

    if "images" in sanitized:
        sanitized["images"] = _sanitize_url_list(sanitized.get("images"))

    return sanitized


def _truncate_text(value: object, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _compact_result(result: dict) -> dict:
    compacted: dict = {}
    for key in _RESULT_KEYS:
        if key not in result:
            continue
        value = result[key]
        if key == "content":
            compacted[key] = _truncate_text(value, MAX_RESULT_CONTENT_CHARS)
        else:
            compacted[key] = value

    image = result.get("image")
    if isinstance(image, str) and is_safe_public_url(image):
        compacted["image"] = image
    return compacted


def _compact_search_response(
    *,
    query: str,
    results: list[dict],
    images: list[str],
    start_date: date,
    end_date: date,
    before_days: int,
    filtered_out: list[dict],
) -> dict:
    return {
        "query": query,
        "results": [_compact_result(item) for item in results],
        "images": images[:MAX_SEARCH_IMAGES],
        "search_window": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "before_days": before_days,
            "date_filter_rule": (
                "Reject only official published_date/date fields outside this window."
            ),
        },
        "filtered_out_by_date": filtered_out[:MAX_FILTERED_OUT_ITEMS],
    }


@tool
def search_new(
    query: str,
    today: str | None = None,
    before_days: int | None = None,
    max_results: int | None = None,
) -> dict:
    """
    Realiza buscas avancadas na internet via Tavily para obter noticias atuais.

    Args:
        query: Termo de busca ou pergunta especifica.
        today: Data base no formato 'YYYY-MM-DD'. Se omitido, usa a data atual.
        before_days: Janela de dias para olhar para tras a partir da data base.
        max_results: Quantidade maxima de resultados retornados pela busca.
    """

    settings = load_settings()
    resolved_before_days = _validate_range(
        "before_days",
        before_days if before_days is not None else settings.before_days,
        MIN_BEFORE_DAYS,
        MAX_BEFORE_DAYS,
    )
    resolved_max_results = _validate_range(
        "max_results",
        max_results if max_results is not None else settings.max_search_results,
        MIN_MAX_RESULTS,
        MAX_MAX_RESULTS,
    )

    if today is None:
        base_date = datetime.now(APP_TIMEZONE)
    else:
        parsed_today = datetime.strptime(today, "%Y-%m-%d")
        base_date = parsed_today.replace(tzinfo=APP_TIMEZONE)

    start_date = (base_date - timedelta(days=resolved_before_days)).date()
    end_date = base_date.date()

    search_kwargs: dict = {
        "query": query,
        "search_depth": "advanced",
        "topic": "news",
        "max_results": resolved_max_results,
        "include_images": True,
        "include_favicon": False,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    if settings.include_domains:
        search_kwargs["include_domains"] = list(settings.include_domains)
    if settings.exclude_domains:
        search_kwargs["exclude_domains"] = list(settings.exclude_domains)

    logger.info(
        "Buscando noticias. query=%r janela=%s..%s max=%s",
        query,
        start_date.isoformat(),
        end_date.isoformat(),
        resolved_max_results,
    )

    response = None
    last_exc = None
    for attempt in range(2):
        try:
            response = _get_client().search(**search_kwargs)
            break
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Falha na consulta Tavily (tentativa %s/2): %s",
                attempt + 1,
                exc,
            )
            if attempt == 0:
                import time

                time.sleep(1)

    if response is None:
        logger.error("Busca Tavily esgotou as tentativas: %s", last_exc)
        payload = _compact_search_response(
            query=query,
            results=[],
            images=[],
            start_date=start_date,
            end_date=end_date,
            before_days=resolved_before_days,
            filtered_out=[],
        )
        payload["error"] = f"Falha na consulta da API de busca: {last_exc}"
        return payload

    filtered_results = []
    filtered_out = []

    for result in response.get("results", []):
        sanitized_result = _sanitize_result(result)
        if sanitized_result is None:
            filtered_out.append(
                {
                    "title": result.get("title"),
                    "reason": "unsafe_source_url",
                }
            )
            continue

        published_date = _official_published_date(sanitized_result)
        if published_date and not (start_date <= published_date <= end_date):
            filtered_out.append(
                {
                    "title": sanitized_result.get("title"),
                    "url": sanitized_result.get("url"),
                    "published_date": published_date.isoformat(),
                    "reason": "published_date_outside_search_window",
                }
            )
            continue

        if published_date:
            sanitized_result["validated_published_date"] = published_date.isoformat()
        filtered_results.append(sanitized_result)

    payload = _compact_search_response(
        query=query,
        results=filtered_results,
        images=_sanitize_url_list(response.get("images")),
        start_date=start_date,
        end_date=end_date,
        before_days=resolved_before_days,
        filtered_out=filtered_out,
    )
    payload_chars = sum(
        len(str(item.get("content", ""))) for item in payload["results"]
    )
    logger.info(
        "Busca concluida. query=%r resultados=%s filtrados=%s conteudo=%s caracteres",
        query,
        len(payload["results"]),
        len(filtered_out),
        payload_chars,
    )
    return payload


# Kept for older imports and tests that want the default env window.
before_days = DEFAULT_BEFORE_DAYS
default_max_results = DEFAULT_MAX_RESULTS
