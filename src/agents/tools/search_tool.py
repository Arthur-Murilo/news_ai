from tavily import TavilyClient
from langchain.tools import tool
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

before_days = int(os.getenv("BEFORE_DAYS", "7"))

client = TavilyClient(os.getenv("TAVILY_API_KEY"))
@tool
def search_new(query: str, today: datetime=datetime.now(), before_days: int = before_days ) -> dict:
    """
    Realiza buscas avançadas na internet via Tavily para obter informações atualizadas e detalhadas.
    Ideal para pesquisas de notícias, artigos e contextos recentes, com foco em resultados do Brasil.

    Args:
        query: O termo de busca ou a pergunta específica para a qual deseja encontrar informações.
    """
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        start_date=datetime.now().strftime("%Y-%m-%d"),
        end_date=(today - timedelta(days=before_days)).strftime("%Y-%m-%d"),
        include_raw_content="text",
        country="brazil"
    )

    return response