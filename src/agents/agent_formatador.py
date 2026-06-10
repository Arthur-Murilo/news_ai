import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from src.prompts.agent_fomatador_prompt import SYSTEM_PROMPT

load_dotenv()

model = ChatGoogleGenerativeAI(
    model=os.getenv("MODEL_AGENT_FORMATER", os.getenv("AI_MODEL", "gemini-2.5-flash")),
    temperature=0.3,
    max_tokens=8000,
)


def _extract_message_text(message_content: object) -> str:
    if isinstance(message_content, str):
        return message_content.strip()

    if isinstance(message_content, list):
        parts: list[str] = []
        for item in message_content:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = str(item.get("text", "")).strip()
            else:
                text = str(item).strip()

            if text:
                parts.append(text)

        return "\n".join(parts).strip()

    if isinstance(message_content, dict):
        return str(message_content.get("text", "")).strip()

    if message_content is None:
        return ""

    return str(message_content).strip()


def call_agent_formater(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("O agente formatador recebeu uma entrada vazia.")

    agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )

    newsletter = agent.invoke(
        {"messages": [{"role": "user", "content": text}]}
    )

    content = _extract_message_text(newsletter["messages"][-1].content)
    if not content:
        raise ValueError("O agente formatador retornou uma resposta vazia.")

    return content
