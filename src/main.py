import os
from typing import cast

from dotenv import load_dotenv
from langgraph.graph import END, START, MessagesState, StateGraph
from rich import print
from src.nodes.node_formatador import node_formatador
from src.nodes.node_pesquisador import node_pesquisador
from src.nodes.node_send_email import node_send_email

load_dotenv()


def build_graph():
    graph = StateGraph(MessagesState)
    graph.add_node("pesquisador", node_pesquisador)
    graph.add_node("formatador", node_formatador)
    graph.add_node("enviar_email", node_send_email)
    graph.add_edge(START, "pesquisador")
    graph.add_edge("pesquisador", "formatador")
    graph.add_edge("formatador", "enviar_email")
    graph.add_edge("enviar_email", END)
    return graph.compile()


def run_workflow(subject: str | None = None) -> str:
    workflow_subject = subject or os.getenv("SUBJECT", "Inteligencia Artificial")
    graph = build_graph()
    response = graph.invoke(
        cast(
            MessagesState,
            {"messages": [{"role": "user", "content": workflow_subject}]},
        )
    )
    final_message = str(response["messages"][-1].content)
    print(final_message)
    return final_message


if __name__ == "__main__":
    run_workflow()
