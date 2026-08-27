from __future__ import annotations

import argparse
import os
from typing import Sequence

from langgraph.graph import END, START, StateGraph
from rich import print

from src.nodes.node_formatador import node_formatador
from src.nodes.node_pesquisador import node_pesquisador
from src.nodes.node_send_email import node_send_email
from src.settings import load_settings
from src.state import STATUS_APTO, STATUS_ERRO, STATUS_PENDING, NewsletterState

_compiled_graph = None


def route_after_pesquisador(state: NewsletterState) -> str:
    if state.get("status") == STATUS_APTO:
        return "formatador"
    return END


def route_after_formatador(state: NewsletterState) -> str:
    if state.get("status") == STATUS_ERRO:
        return END
    return "enviar_email"


def build_graph():
    graph = StateGraph(NewsletterState)
    graph.add_node("pesquisador", node_pesquisador)
    graph.add_node("formatador", node_formatador)
    graph.add_node("enviar_email", node_send_email)
    graph.add_edge(START, "pesquisador")
    graph.add_conditional_edges(
        "pesquisador",
        route_after_pesquisador,
        {"formatador": "formatador", END: END},
    )
    graph.add_conditional_edges(
        "formatador",
        route_after_formatador,
        {"enviar_email": "enviar_email", END: END},
    )
    graph.add_edge("enviar_email", END)
    return graph.compile()


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="News AI workflow")
    parser.add_argument("--subject", default=None, help="Tema da pesquisa.")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Janela de busca em dias, sobrescreve BEFORE_DAYS.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa pesquisa e formatacao, grava preview e nao envia email.",
    )
    parser.add_argument(
        "--skip-email",
        action="store_true",
        help="Nao envia email ao final do fluxo.",
    )
    return parser.parse_args(argv)


def run_workflow(
    subject: str | None = None,
    *,
    skip_email: bool = False,
    dry_run: bool = False,
) -> str:
    settings = load_settings()
    skip_send = skip_email or dry_run
    settings.validate_for_workflow(skip_email=skip_send)

    workflow_subject = (subject or settings.subject).strip()
    graph = get_graph()
    response = graph.invoke(
        {
            "messages": [{"role": "user", "content": workflow_subject}],
            "subject": workflow_subject,
            "status": STATUS_PENDING,
            "research_text": "",
            "research_payload": {},
            "html": "",
            "error": "",
            "skip_email": skip_send,
            "dry_run": dry_run,
            "email_result": "",
        }
    )

    if response.get("status") == STATUS_ERRO:
        raise RuntimeError(response.get("error") or "Workflow falhou.")

    final_message = str(
        response.get("email_result")
        or response.get("research_text")
        or response["messages"][-1].content
    )
    print(final_message)
    return final_message


def main(argv: Sequence[str] | None = None) -> str:
    args = parse_args(argv)
    if args.days is not None:
        os.environ["BEFORE_DAYS"] = str(args.days)
    return run_workflow(
        subject=args.subject,
        skip_email=args.skip_email or args.dry_run,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
