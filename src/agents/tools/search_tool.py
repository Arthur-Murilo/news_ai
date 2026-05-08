from tavily import TavilyClient
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

client = TavilyClient(os.getenv("TAVILY_API_KEY"))
@tool
def search_new(query: str) -> dict:
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
        start_date="2026-04-07",
        end_date="2026-05-07",
        include_raw_content="text",
        country="brazil"
    )

    return response