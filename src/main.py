from langgraph.graph import StateGraph, MessagesState, START, END
from src.nodes.node_pesquisador import node_pesquisador
from src.nodes.node_formatador import node_formatador
from src.nodes.node_send_email import node_send_email
import os
from dotenv import load_dotenv
from typing import cast
from rich import print

load_dotenv()
subject = os.getenv("SUBJECT","Inteligencia Artifical")

graph = StateGraph(MessagesState)
graph.add_node("pesquisador", node_pesquisador)
graph.add_node("formatador", node_formatador)
graph.add_node("enviar_email",node_send_email)
graph.add_edge(START, "pesquisador")
graph.add_edge("pesquisador","formatador")
graph.add_edge("formatador","enviar_email")
graph.add_edge("enviar_email", END)
graph = graph.compile()

response = graph.invoke(cast(MessagesState, {"messages": [{"role": "user", "content": subject}]}))

print(response["messages"][-1].content)