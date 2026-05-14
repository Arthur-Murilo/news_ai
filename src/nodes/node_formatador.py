from src.agents.agent_formatador import call_agent_formater
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage
from typing import cast

def node_formatador(state: MessagesState):
    # Pega o texto da última mensagem do usuário
    text = state["messages"][-1].content
    resposta_texto = call_agent_formater(cast(str, text))
    return {"messages": [AIMessage(content=resposta_texto)]}