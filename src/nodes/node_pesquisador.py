from src.agents.agent_pesquisador import call_agent
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage
from typing import cast

def node_pesquisador(state: MessagesState):
    # Pega o texto da última mensagem do usuário
    pergunta = state["messages"][-1].content

    # Chama o agente (que só entende string)
    resposta_texto = call_agent(cast(str, pergunta))

    # Retorna o objeto AIMessage que o MessagesState exige
    return {"messages": [AIMessage(content=resposta_texto)]}