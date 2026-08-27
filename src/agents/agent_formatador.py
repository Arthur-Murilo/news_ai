from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import create_chat_model
from src.prompts.agent_formatador_prompt import SYSTEM_PROMPT
from src.utils import extract_message_text

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = create_chat_model("MODEL_AGENT_FORMATER")
    return _model


def call_agent_formater(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("O agente formatador recebeu uma entrada vazia.")

    result = _get_model().invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=text),
        ]
    )

    content = extract_message_text(result.content)
    if not content:
        raise ValueError("O agente formatador retornou uma resposta vazia.")

    return content
