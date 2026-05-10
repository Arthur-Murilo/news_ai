from tavily import TavilyClient
from langchain.tools import tool
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rich import print
import os

load_dotenv()

before_days = int(os.getenv("BEFORE_DAYS", "7"))
client = TavilyClient(os.getenv("TAVILY_API_KEY"))

@tool
def search_new(query: str, today: str | None = None ,before_days: int = before_days ) -> dict:
    """
    Realiza buscas avançadas na internet via Tavily para obter informações atualizadas e detalhadas.
    Ideal para pesquisas de notícias, artigos e contextos recentes, com foco em resultados do Brasil.

    Args:
        query: O termo de busca ou a pergunta específica para a qual deseja encontrar informações.
        today: Data base para a pesquisa no formato 'YYYY-MM-DD'. Se omitido, utiliza a data de hoje. 
               Útil para buscar notícias de um dia específico no passado.
        before_days: Janela de dias para olhar para trás a partir da data base (padrão definido no ambiente ou 7 dias).
    """
    
    if today is None:
        base_date = datetime.now()
    else:
        base_date = datetime.strptime(today, "%Y-%m-%d")

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        start_date=(base_date - timedelta(days=before_days)).strftime("%Y-%m-%d"),
        end_date=base_date.strftime("%Y-%m-%d"),
        country="brazil"
    )

    return response
