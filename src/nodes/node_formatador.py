from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState

from src.agents.agent_formatador import call_agent_formater


def node_formatador(state: MessagesState):
    text = str(state["messages"][-1].content).strip()
    if not text:
        raise ValueError("O no formatador recebeu uma mensagem vazia do passo anterior.")

    resposta_texto = call_agent_formater(text)
    return {"messages": [AIMessage(content=resposta_texto)]}
