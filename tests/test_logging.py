from __future__ import annotations

import logging

from src.logging_config import resolve_log_level
from src.main import run_workflow
from src.state import STATUS_APTO


def test_resolve_log_level_defaults_and_invalid_values(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert resolve_log_level(None) == logging.INFO
    assert resolve_log_level("debug") == logging.DEBUG
    assert resolve_log_level("NOPE") == logging.INFO


def test_run_workflow_dry_run_logs_each_stage(env_defaults, monkeypatch, caplog):
    monkeypatch.setattr(
        "src.nodes.node_pesquisador.call_agent",
        lambda _subject: (
            "{"
            '"status": "APTO PARA PROXIMA FASE",'
            '"tema": "IA",'
            '"resumo": "Teve novidade",'
            '"noticias": [{"titulo": "Modelo novo",'
            '"link": "https://example.com/modelo"}]'
            "}"
        ),
    )
    monkeypatch.setattr(
        "src.nodes.node_formatador.call_agent_formater",
        lambda _text: "<div><h1>News AI</h1><p>Modelo novo</p></div>",
    )
    monkeypatch.setattr(
        "src.nodes.node_send_email.send_email",
        lambda _html: "sent",
    )

    caplog.set_level(logging.INFO)
    result = run_workflow(subject="IA", dry_run=True)

    assert "Envio ignorado" in result
    log_text = caplog.text
    assert "Workflow iniciado" in log_text
    assert "Etapa pesquisador iniciada" in log_text
    assert "Etapa pesquisador concluida" in log_text
    assert "Roteamento apos pesquisador: seguir para formatador" in log_text
    assert "Etapa formatador iniciada" in log_text
    assert "Etapa formatador concluida" in log_text
    assert "Etapa envio de email iniciada" in log_text
    assert "envio ignorado" in log_text
    assert "Workflow concluido" in log_text
    assert STATUS_APTO in log_text or "status=apto" in log_text
