from __future__ import annotations

import logging
import time

from langchain.agents import create_agent
from rich import print

from src.agents.tools.search_tool import search_new
from src.llm import create_chat_model
from src.prompts.agent_pesquisador_prompt import get_system_prompt
from src.utils import extract_message_text

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = create_chat_model("MODEL_AGENT_SEARCH")
    return _model


def _count_tool_messages(messages: list[object]) -> int:
    return sum(
        1
        for message in messages
        if getattr(message, "type", None) == "tool"
        or type(message).__name__ == "ToolMessage"
    )


def call_agent(pergunta: str) -> str:
    logger.info("Agente pesquisador invocando LLM. tema=%s", pergunta)
    started = time.perf_counter()
    agent = create_agent(
        model=_get_model(),
        tools=[search_new],
        system_prompt=get_system_prompt(pergunta),
    )

    result = agent.invoke({"messages": [{"role": "user", "content": pergunta}]})
    messages = result["messages"]
    content = extract_message_text(messages[-1].content)
    if not content:
        raise ValueError("O agente pesquisador retornou uma resposta vazia.")

    logger.info(
        "Agente pesquisador concluiu em %.1fs. mensagens=%s buscas=%s resposta=%s caracteres",
        time.perf_counter() - started,
        len(messages),
        _count_tool_messages(messages),
        len(content),
    )
    return content


if __name__ == "__main__":
    pergunta = input("Digite sua pergunta: ")
    print(call_agent(pergunta))
