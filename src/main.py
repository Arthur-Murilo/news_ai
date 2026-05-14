from langgraph.graph import StateGraph, MessagesState, START, END
from src.nodes.node_pesquisador import node_pesquisador
from src.nodes.node_formatador import node_formatador
from typing import cast
from rich import print


graph = StateGraph(MessagesState)
graph.add_node("pesquisador", node_pesquisador)
graph.add_node("formatador", node_formatador)
graph.add_edge(START, "pesquisador")
graph.add_edge("pesquisador","formatador")
graph.add_edge("formatador", END)
graph = graph.compile()

response = graph.invoke(cast(MessagesState, {"messages": [{"role": "user", "content": "Quero saber sobre noticias de inteligencia artificial dessa semana"}]}))

print(response["messages"][-1].content)