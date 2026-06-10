from datetime import date, datetime, timedelta
import os
import re
import unicodedata

from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

from src.security import is_safe_public_url

load_dotenv()

DEFAULT_BEFORE_DAYS = 7
DEFAULT_MAX_RESULTS = 15
MIN_BEFORE_DAYS = 1
MAX_BEFORE_DAYS = 30
MIN_MAX_RESULTS = 1
MAX_MAX_RESULTS = 20


def _read_int_env(name: str, default: int) -> int:
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


before_days = _validate_range(
    "BEFORE_DAYS",
    _read_int_env("BEFORE_DAYS", DEFAULT_BEFORE_DAYS),
    MIN_BEFORE_DAYS,
    MAX_BEFORE_DAYS,
)
default_max_results = _validate_range(
    "MAX_SEARCH_RESULTS",
    _read_int_env("MAX_SEARCH_RESULTS", DEFAULT_MAX_RESULTS),
    MIN_MAX_RESULTS,
    MAX_MAX_RESULTS,
)
client = TavilyClient(os.getenv("TAVILY_API_KEY"))

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


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value)
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

    match = re.search(
        r"\b(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\b",
        text.lower(),
    )
    if match:
        day = int(match.group(1))
        month = MONTHS_PT.get(_strip_accents(match.group(2)))
        year = int(match.group(3))
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                return None

    return None


def _extract_published_date(result: dict) -> date | None:
    for field in ("published_date", "date"):
        parsed = _parse_date(result.get(field))
        if parsed:
            return parsed

    searchable_text = "\n".join(
        str(result.get(field, ""))[:5000]
        for field in ("title", "content")
    )
    return _parse_date(searchable_text)


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


@tool
def search_new(
    query: str,
    today: str | None = None,
    before_days: int = before_days,
    max_results: int = default_max_results,
) -> dict:
    """
    Realiza buscas avancadas na internet via Tavily para obter noticias atuais.

    Args:
        query: Termo de busca ou pergunta especifica.
        today: Data base no formato 'YYYY-MM-DD'. Se omitido, usa a data atual.
        before_days: Janela de dias para olhar para tras a partir da data base.
        max_results: Quantidade maxima de resultados retornados pela busca.
    """

    before_days = _validate_range(
        "before_days",
        before_days,
        MIN_BEFORE_DAYS,
        MAX_BEFORE_DAYS,
    )
    max_results = _validate_range(
        "max_results",
        max_results,
        MIN_MAX_RESULTS,
        MAX_MAX_RESULTS,
    )

    if today is None:
        base_date = datetime.now()
    else:
        base_date = datetime.strptime(today, "%Y-%m-%d")

    start_date = (base_date - timedelta(days=before_days)).date()
    end_date = base_date.date()

    response = client.search(
        query=query,
        search_depth="advanced",
        topic="news",
        max_results=max_results,
        include_images=True,
        include_favicon=True,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    filtered_results = []
    filtered_out_by_date = []

    for result in response.get("results", []):
        sanitized_result = _sanitize_result(result)
        if sanitized_result is None:
            filtered_out_by_date.append(
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "reason": "unsafe_source_url",
                }
            )
            continue

        published_date = _extract_published_date(sanitized_result)
        if published_date and not (start_date <= published_date <= end_date):
            filtered_out_by_date.append(
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

    response["results"] = filtered_results
    response["images"] = _sanitize_url_list(response.get("images"))
    response["search_window"] = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "before_days": before_days,
        "date_filter_rule": "Reject explicit publication dates outside this window.",
    }
    response["filtered_out_by_date"] = filtered_out_by_date
    response["safety"] = {
        "allowed_url_schemes": ["http", "https"],
        "blocked_hosts": ["localhost", "private_ips", "loopback_ips"],
    }

    return response
