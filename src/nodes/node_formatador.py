from langchain_core.messages import AIMessage

from src.agents.agent_formatador import call_agent_formater
from src.security import looks_like_html
from src.state import STATUS_ERRO, NewsletterState
from src.utils import extract_message_text


def node_formatador(state: NewsletterState):
    try:
        text = extract_message_text(state.get("research_text") or "")
        if not text:
            text = extract_message_text(state["messages"][-1].content)
        if not text:
            raise ValueError(
                "O no formatador recebeu uma mensagem vazia do passo anterior."
            )

        resposta_texto = call_agent_formater(text)
        if not looks_like_html(resposta_texto):
            raise ValueError("O agente formatador nao retornou HTML valido.")

        return {
            "messages": [AIMessage(content=resposta_texto)],
            "html": resposta_texto,
            "error": "",
        }
    except Exception as exc:
        message = str(exc)
        return {
            "messages": [AIMessage(content=message)],
            "status": STATUS_ERRO,
            "error": message,
        }
