from __future__ import annotations

import logging
import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.llm import (
    call_with_retries,
    create_chat_model,
    describe_llm_error,
    is_transient_llm_error,
)
from src.prompts.agent_formatador_prompt import SYSTEM_PROMPT
from src.utils import extract_message_text

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = create_chat_model("MODEL_AGENT_FORMATER")
    return _model


def call_agent_formater(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("O agente formatador recebeu uma entrada vazia.")

    logger.info(
        "Agente formatador invocando LLM. entrada=%s caracteres",
        len(text),
    )
    started = time.perf_counter()

    def _invoke() -> AIMessage:
        result = _get_model().invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=text),
            ]
        )
        return result

    try:
        result = call_with_retries(_invoke, what="Agente formatador")
    except Exception as exc:
        if is_transient_llm_error(exc):
            raise RuntimeError(describe_llm_error(exc)) from exc
        raise

    content = extract_message_text(result.content)
    if not content:
        raise ValueError("O agente formatador retornou uma resposta vazia.")

    logger.info(
        "Agente formatador concluiu em %.1fs. resposta=%s caracteres",
        time.perf_counter() - started,
        len(content),
    )
    return content
