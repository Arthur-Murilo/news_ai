from datetime import date, datetime, timedelta
import os
import re
import unicodedata

from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

before_days = int(os.getenv("BEFORE_DAYS", "7"))
default_max_results = int(os.getenv("MAX_SEARCH_RESULTS", "15"))
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
        for field in ("title", "content", "raw_content")
    )
    return _parse_date(searchable_text)


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
        include_raw_content="markdown",
        include_images=True,
        include_favicon=True,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    filtered_results = []
    filtered_out_by_date = []

    for result in response.get("results", []):
        published_date = _extract_published_date(result)
        if published_date and not (start_date <= published_date <= end_date):
            filtered_out_by_date.append(
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "published_date": published_date.isoformat(),
                    "reason": "published_date_outside_search_window",
                }
            )
            continue

        if published_date:
            result["validated_published_date"] = published_date.isoformat()
        filtered_results.append(result)

    response["results"] = filtered_results
    response["search_window"] = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "before_days": before_days,
        "date_filter_rule": "Reject explicit publication dates outside this window.",
    }
    response["filtered_out_by_date"] = filtered_out_by_date

    return response
