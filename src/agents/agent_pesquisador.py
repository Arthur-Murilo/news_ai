from langchain.agents import create_agent
from rich import print

from src.agents.tools.search_tool import search_new
from src.llm import create_chat_model
from src.prompts.agent_pesquisador_prompt import get_system_prompt
from src.utils import extract_message_text

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = create_chat_model("MODEL_AGENT_SEARCH")
    return _model


def call_agent(pergunta: str) -> str:
    agent = create_agent(
        model=_get_model(),
        tools=[search_new],
        system_prompt=get_system_prompt(pergunta),
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": pergunta}]}
    )

    content = extract_message_text(result["messages"][-1].content)
    if not content:
        raise ValueError("O agente pesquisador retornou uma resposta vazia.")

    return content


if __name__ == "__main__":
    pergunta = input("Digite sua pergunta: ")
    print(call_agent(pergunta))
