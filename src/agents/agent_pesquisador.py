from langchain.agents import create_agent
from rich import print

from src.agents.tools.search_tool import search_new
from src.llm import create_chat_model
from src.prompts.agent_pesquisador_prompt import get_system_prompt

model = create_chat_model("MODEL_AGENT_SEARCH")


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


def call_agent(pergunta: str) -> str:
    agent = create_agent(
        model=model,
        tools=[search_new],
        system_prompt=get_system_prompt(),
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": pergunta}]}
    )

    content = _extract_message_text(result["messages"][-1].content)
    if not content:
        raise ValueError("O agente pesquisador retornou uma resposta vazia.")

    return content


if __name__ == "__main__":
    pergunta = input("Digite sua pergunta: ")
    print(call_agent(pergunta))
