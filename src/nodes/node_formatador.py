from __future__ import annotations

import logging
import time

from langchain_core.messages import AIMessage

from src.agents.agent_formatador import call_agent_formater
from src.security import looks_like_html
from src.state import STATUS_ERRO, NewsletterState
from src.utils import extract_message_text, strip_markdown_code_fences

logger = logging.getLogger(__name__)


def node_formatador(state: NewsletterState):
    started = time.perf_counter()
    try:
        text = extract_message_text(state.get("research_text") or "")
        if not text:
            text = extract_message_text(state["messages"][-1].content)
        if not text:
            raise ValueError(
                "O no formatador recebeu uma mensagem vazia do passo anterior."
            )

        logger.info(
            "Etapa formatador iniciada. pesquisa=%s caracteres",
            len(text),
        )
        resposta_texto = strip_markdown_code_fences(
            extract_message_text(call_agent_formater(text))
        )
        if not looks_like_html(resposta_texto):
            raise ValueError("O agente formatador nao retornou HTML valido.")

        elapsed = time.perf_counter() - started
        logger.info(
            "Etapa formatador concluida em %.1fs. html=%s caracteres",
            elapsed,
            len(resposta_texto),
        )
        return {
            "messages": [AIMessage(content=resposta_texto)],
            "html": resposta_texto,
            "error": "",
        }
    except Exception as exc:
        message = str(exc)
        logger.exception(
            "Etapa formatador falhou apos %.1fs: %s",
            time.perf_counter() - started,
            message,
        )
        return {
            "messages": [AIMessage(content=message)],
            "status": STATUS_ERRO,
            "error": message,
        }
