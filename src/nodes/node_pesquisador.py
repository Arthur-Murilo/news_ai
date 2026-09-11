from __future__ import annotations

import logging
import time

from langchain_core.messages import AIMessage

from src.agents.agent_pesquisador import call_agent
from src.research import parse_research_result, render_research_text
from src.sent_news import SentNewsStore, filter_already_sent
from src.state import STATUS_APTO, STATUS_ERRO, STATUS_NAO_APTO, NewsletterState
from src.utils import extract_message_text

logger = logging.getLogger(__name__)


def node_pesquisador(state: NewsletterState):
    started = time.perf_counter()
    try:
        subject = extract_message_text(state.get("subject") or "")
        if not subject:
            subject = extract_message_text(state["messages"][-1].content)
        if not subject:
            raise ValueError("O no pesquisador recebeu um tema vazio.")

        logger.info("Etapa pesquisador iniciada. tema=%s", subject)
        resposta_texto = call_agent(subject)
        logger.info(
            "Pesquisador devolveu resposta com %s caracteres",
            len(resposta_texto),
        )
        resultado = parse_research_result(resposta_texto)
        resultado.noticias, dropped = filter_already_sent(
            resultado.noticias,
            SentNewsStore(),
        )
        if dropped:
            logger.info("Omitidas %s noticias ja enviadas", len(dropped))
            resultado.pontos_atencao.append(
                "Noticias omitidas porque ja foram enviadas: " + "; ".join(dropped)
            )
        if resultado.status == STATUS_APTO and not resultado.noticias:
            resultado.status = STATUS_NAO_APTO
            resultado.pontos_atencao.append(
                "Nenhuma noticia nova restou apos remover itens ja enviados."
            )

        research_text = render_research_text(resultado)
        status = STATUS_APTO if resultado.apto else STATUS_NAO_APTO
        elapsed = time.perf_counter() - started
        logger.info(
            "Etapa pesquisador concluida em %.1fs. status=%s noticias=%s apto=%s",
            elapsed,
            status,
            len(resultado.noticias),
            resultado.apto,
        )
        return {
            "messages": [AIMessage(content=research_text)],
            "subject": subject,
            "status": status,
            "research_text": research_text,
            "research_payload": resultado.to_payload(),
            "error": "",
        }
    except Exception as exc:
        message = str(exc)
        logger.exception(
            "Etapa pesquisador falhou apos %.1fs: %s",
            time.perf_counter() - started,
            message,
        )
        return {
            "messages": [AIMessage(content=message)],
            "status": STATUS_ERRO,
            "error": message,
        }
