from __future__ import annotations

import json

from src.research import parse_research_result, render_research_text
from src.state import STATUS_APTO, STATUS_NAO_APTO


def test_parse_json_research_result():
    payload = {
        "status": "APTO PARA PROXIMA FASE",
        "tema": "Agentes de IA",
        "janela_pesquisa": "2026-08-15 a 2026-08-22",
        "resumo": "Novos agentes foram lancados.",
        "noticias": [
            {
                "titulo": "OpenAI lanca agente",
                "fonte": "TechCrunch",
                "data": "2026-08-20",
                "link": "https://techcrunch.com/agent",
                "imagem_sugerida": "https://techcrunch.com/img.png",
                "o_que_aconteceu": "Lancamento",
                "por_que_e_relevante": "Impacta o mercado",
                "contexto_adicional": "Mais detalhes",
                "evidencias": "Comunicado oficial",
            }
        ],
        "contexto_impacto": "Empresas vao testar agentes.",
        "pontos_atencao": ["Uma fonte apenas"],
        "links_consultados": ["https://techcrunch.com/agent", "javascript:alert(1)"],
    }

    result = parse_research_result(json.dumps(payload))

    assert result.status == STATUS_APTO
    assert result.apto
    assert result.noticias[0].titulo == "OpenAI lanca agente"
    assert result.links_consultados == ["https://techcrunch.com/agent"]


def test_parse_text_research_result_and_render_roundtrip():
    raw = """
Status de validacao: APTO PARA PROXIMA FASE
Tema pesquisado: IA
Janela de pesquisa: 2026-08-15 a 2026-08-22

Resumo da pesquisa:
- Semana movimentada

Noticias validadas:
1. Modelo novo
   Fonte: The Verge
   Data: 2026-08-21
   Link: https://theverge.com/modelo
   Imagem sugerida:
   O que aconteceu: Saiu um modelo
   Por que e relevante: Muda o mercado
   Contexto adicional: Poucos detalhes
   Evidencias encontradas: Post oficial

Contexto e impacto:
- Times vao migrar ferramentas

Pontos de atencao:
- Sem segunda fonte

Links consultados:
- https://theverge.com/modelo
"""
    result = parse_research_result(raw)
    assert result.status == STATUS_APTO
    assert result.noticias[0].fonte == "The Verge"

    rendered = render_research_text(result)
    assert "Status de validacao: APTO PARA PROXIMA FASE" in rendered
    assert "https://theverge.com/modelo" in rendered


def test_apto_without_news_becomes_nao_apto():
    raw = json.dumps(
        {
            "status": "APTO PARA PROXIMA FASE",
            "tema": "IA",
            "noticias": [],
        }
    )
    result = parse_research_result(raw)
    assert result.status == STATUS_NAO_APTO
    assert not result.apto


def test_unsafe_news_link_is_dropped_from_item():
    raw = json.dumps(
        {
            "status": "APTO PARA PROXIMA FASE",
            "noticias": [
                {
                    "titulo": "Interno",
                    "link": "http://127.0.0.1/secret",
                }
            ],
        }
    )
    result = parse_research_result(raw)
    assert result.noticias[0].link == ""


def test_parse_json_with_intro_and_trailing_commas():
    raw = (
        "Tenho material suficiente para compor uma newsletter.\n\n"
        "{\n"
        '  "status": "APTO PARA PROXIMA FASE",\n'
        '  "tema": "Inteligencia Artificial",\n'
        '  "janela_pesquisa": "2026-08-21 a 2026-08-28",\n'
        '  "resumo": "Resumo da semana com novidades.",\n'
        '  "noticias": [\n'
        "    {\n"
        '      "titulo": "Meta lanca modelo aberto",\n'
        '      "fonte": "Phoronix",\n'
        '      "link": "https://example.com/news",\n'
        '      "o_que_aconteceu": "Lancamento de modelo",\n'
        "    },\n"
        "  ],\n"
        '  "pontos_atencao": ["Ponto 1"],\n'
        '  "links_consultados": ["https://example.com/news"]\n'
        "}\n\n"
        "Espero que tenha gostado!"
    )
    result = parse_research_result(raw)
    assert result.status == STATUS_APTO
    assert result.apto
    assert len(result.noticias) == 1
    assert result.noticias[0].titulo == "Meta lanca modelo aberto"
