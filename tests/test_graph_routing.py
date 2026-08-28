from __future__ import annotations

import json

from langgraph.graph import END

from src.main import build_graph, route_after_formatador, route_after_pesquisador
from src.state import STATUS_APTO, STATUS_ERRO, STATUS_NAO_APTO, STATUS_PENDING


def test_route_after_pesquisador():
    assert route_after_pesquisador({"status": STATUS_APTO}) == "formatador"
    assert route_after_pesquisador({"status": STATUS_NAO_APTO}) == END
    assert route_after_pesquisador({"status": STATUS_ERRO}) == END


def test_route_after_formatador():
    assert route_after_formatador({"status": STATUS_APTO}) == "enviar_email"
    assert route_after_formatador({"status": STATUS_ERRO}) == END


def test_nao_apto_skips_formatter_and_email(env_defaults, monkeypatch):
    calls = {"format": 0, "email": 0}

    def mock_format(_text: str) -> str:
        calls["format"] += 1
        return "<div>x</div>"

    def mock_email(_html: str) -> str:
        calls["email"] += 1
        return "sent"

    monkeypatch.setattr(
        "src.nodes.node_pesquisador.call_agent",
        lambda _subject: json.dumps(
            {
                "status": "NAO APTO",
                "tema": "IA",
                "resumo": "Sem material suficiente",
                "noticias": [],
            }
        ),
    )
    monkeypatch.setattr(
        "src.nodes.node_formatador.call_agent_formater",
        mock_format,
    )
    monkeypatch.setattr(
        "src.nodes.node_send_email.send_email",
        mock_email,
    )

    result = build_graph().invoke(
        {
            "messages": [{"role": "user", "content": "IA"}],
            "subject": "IA",
            "status": STATUS_PENDING,
            "research_text": "",
            "research_payload": {},
            "html": "",
            "error": "",
            "skip_email": False,
            "dry_run": False,
            "email_result": "",
        }
    )

    assert result["status"] == STATUS_NAO_APTO
    assert calls == {"format": 0, "email": 0}


def test_apto_dry_run_writes_preview_without_sending(env_defaults, monkeypatch):
    sent = {"email": 0, "marked": 0}

    def mock_email(_html: str) -> str:
        sent["email"] += 1
        return "sent"

    def mock_mark(_payload: object) -> None:
        sent["marked"] += 1

    monkeypatch.setattr(
        "src.nodes.node_pesquisador.call_agent",
        lambda _subject: json.dumps(
            {
                "status": "APTO PARA PROXIMA FASE",
                "tema": "IA",
                "resumo": "Teve novidade",
                "noticias": [
                    {
                        "titulo": "Modelo novo",
                        "link": "https://example.com/modelo",
                        "fonte": "Example",
                        "data": "2026-08-21",
                    }
                ],
                "links_consultados": ["https://example.com/modelo"],
            }
        ),
    )
    monkeypatch.setattr(
        "src.nodes.node_formatador.call_agent_formater",
        lambda _text: "<div><h1>News AI</h1><p>Modelo novo</p></div>",
    )
    monkeypatch.setattr(
        "src.nodes.node_send_email.send_email",
        mock_email,
    )
    monkeypatch.setattr(
        "src.nodes.node_send_email.mark_research_as_sent",
        mock_mark,
    )

    result = build_graph().invoke(
        {
            "messages": [{"role": "user", "content": "IA"}],
            "subject": "IA",
            "status": STATUS_PENDING,
            "research_text": "",
            "research_payload": {},
            "html": "",
            "error": "",
            "skip_email": True,
            "dry_run": True,
            "email_result": "",
        }
    )

    assert result["status"] == STATUS_APTO
    assert sent == {"email": 0, "marked": 0}
    assert "Envio ignorado" in result["email_result"]
    assert (env_defaults / "preview.html").exists()


def test_successful_send_marks_news_as_sent(env_defaults, monkeypatch):
    monkeypatch.setattr(
        "src.nodes.node_pesquisador.call_agent",
        lambda _subject: json.dumps(
            {
                "status": "APTO PARA PROXIMA FASE",
                "tema": "IA",
                "noticias": [
                    {
                        "titulo": "Modelo novo",
                        "link": "https://example.com/modelo",
                    }
                ],
            }
        ),
    )
    monkeypatch.setattr(
        "src.nodes.node_formatador.call_agent_formater",
        lambda _text: "<div><h1>News AI</h1><p>ok</p></div>",
    )
    monkeypatch.setattr(
        "src.nodes.node_send_email.resend.Emails.send",
        lambda _payload: {"id": "email_1"},
    )

    first = build_graph().invoke(
        {
            "messages": [{"role": "user", "content": "IA"}],
            "subject": "IA",
            "status": STATUS_PENDING,
            "research_text": "",
            "research_payload": {},
            "html": "",
            "error": "",
            "skip_email": False,
            "dry_run": False,
            "email_result": "",
        }
    )
    assert first["email_result"] == "Email enviado com sucesso."

    second = build_graph().invoke(
        {
            "messages": [{"role": "user", "content": "IA"}],
            "subject": "IA",
            "status": STATUS_PENDING,
            "research_text": "",
            "research_payload": {},
            "html": "",
            "error": "",
            "skip_email": False,
            "dry_run": False,
            "email_result": "",
        }
    )
    assert second["status"] == STATUS_NAO_APTO
    assert "ja foram enviadas" in second["research_text"]
