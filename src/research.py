from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
import unicodedata
from typing import Any

from src.security import is_safe_public_url
from src.state import STATUS_APTO, STATUS_NAO_APTO

STATUS_APTO_LABEL = "APTO PARA PROXIMA FASE"
STATUS_NAO_APTO_LABEL = "NAO APTO"


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def normalize_research_status(value: str) -> str:
    text = _strip_accents(str(value)).lower().replace("_", " ").strip()
    if "nao apto" in text:
        return STATUS_NAO_APTO
    if "apto" in text:
        return STATUS_APTO
    return STATUS_NAO_APTO


@dataclass
class NoticiaValidada:
    titulo: str
    fonte: str = ""
    data: str = ""
    link: str = ""
    imagem_sugerida: str = ""
    o_que_aconteceu: str = ""
    por_que_e_relevante: str = ""
    contexto_adicional: str = ""
    evidencias: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResultadoPesquisa:
    status: str
    tema: str = ""
    janela_pesquisa: str = ""
    resumo: str = ""
    noticias: list[NoticiaValidada] = field(default_factory=list)
    contexto_impacto: str = ""
    pontos_atencao: list[str] = field(default_factory=list)
    links_consultados: list[str] = field(default_factory=list)
    bruto: str = ""

    @property
    def apto(self) -> bool:
        return self.status == STATUS_APTO and bool(self.noticias)

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["noticias"] = [noticia.to_dict() for noticia in self.noticias]
        return payload


def _as_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_str_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return [item.strip() for item in (_as_str(part) for part in value) if item.strip()]
    return []


def _pick(data: dict[str, Any], *keys: str) -> object:
    lowered = {str(key).lower(): value for key, value in data.items()}
    for key in keys:
        if key.lower() in lowered:
            return lowered[key.lower()]
    return None


def _noticia_from_dict(raw: object) -> NoticiaValidada | None:
    if not isinstance(raw, dict):
        return None

    titulo = _as_str(_pick(raw, "titulo", "title", "fato"))
    if not titulo:
        return None

    link = _as_str(_pick(raw, "link", "url", "fonte_url"))
    if link and not is_safe_public_url(link):
        link = ""

    imagem = _as_str(_pick(raw, "imagem_sugerida", "imagem", "image", "suggested_image"))
    if imagem and not is_safe_public_url(imagem):
        imagem = ""

    return NoticiaValidada(
        titulo=titulo,
        fonte=_as_str(_pick(raw, "fonte", "source")),
        data=_as_str(_pick(raw, "data", "date", "published_date")),
        link=link,
        imagem_sugerida=imagem,
        o_que_aconteceu=_as_str(_pick(raw, "o_que_aconteceu", "what_happened", "resumo")),
        por_que_e_relevante=_as_str(_pick(raw, "por_que_e_relevante", "why_relevant")),
        contexto_adicional=_as_str(_pick(raw, "contexto_adicional", "context")),
        evidencias=_as_str(_pick(raw, "evidencias", "evidencias_encontradas", "evidence")),
    )


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    candidates = []
    if fenced:
        candidates.append(fenced.group(1))
    if stripped.startswith("{"):
        candidates.append(stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        candidates.append(stripped[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _parse_text_noticias(text: str) -> list[NoticiaValidada]:
    block_match = re.search(
        r"Noticias validadas:\s*(.*?)(?:\nContexto e impacto:|\nPontos de atencao:|\nLinks consultados:|$)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not block_match:
        return []

    block = block_match.group(1)
    chunks = re.split(r"\n\s*\d+\.\s+", "\n" + block)
    noticias: list[NoticiaValidada] = []

    for chunk in chunks:
        lines = [line.rstrip() for line in chunk.strip().splitlines() if line.strip()]
        if not lines:
            continue

        fields: dict[str, str] = {"titulo": lines[0].strip()}
        current_key = None
        aliases = {
            "fonte": "fonte",
            "data": "data",
            "link": "link",
            "url": "link",
            "imagem sugerida": "imagem_sugerida",
            "o que aconteceu": "o_que_aconteceu",
            "por que e relevante": "por_que_e_relevante",
            "contexto adicional": "contexto_adicional",
            "evidencias encontradas": "evidencias",
            "evidencias": "evidencias",
        }

        for line in lines[1:]:
            match = re.match(r"^\s*([A-Za-zÀ-ÿ ]+):\s*(.*)$", line)
            if match:
                label = _strip_accents(match.group(1)).lower().strip()
                current_key = aliases.get(label)
                if current_key:
                    fields[current_key] = match.group(2).strip()
                continue
            if current_key:
                fields[current_key] = f"{fields.get(current_key, '')} {line.strip()}".strip()

        noticia = _noticia_from_dict(fields)
        if noticia:
            noticias.append(noticia)

    return noticias


def _section_text(text: str, label: str, next_labels: list[str]) -> str:
    next_pattern = "|".join(re.escape(item) for item in next_labels)
    match = re.search(
        rf"{re.escape(label)}\s*(.*?)(?:\n(?:{next_pattern})|$)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return ""
    return match.group(1).strip(" -\n")


def parse_research_result(raw_text: str) -> ResultadoPesquisa:
    text = (raw_text or "").strip()
    if not text:
        return ResultadoPesquisa(status=STATUS_NAO_APTO, bruto=text)

    payload = _extract_json_payload(text)
    if payload is not None:
        raw_news = payload.get("noticias")
        if raw_news is None:
            raw_news = payload.get("news")
        noticias = [
            noticia
            for item in (raw_news if isinstance(raw_news, list) else [])
            if (noticia := _noticia_from_dict(item))
        ]

        pontos = payload.get("pontos_atencao") or payload.get("attention_points") or []
        links = payload.get("links_consultados") or payload.get("links") or []

        resultado = ResultadoPesquisa(
            status=normalize_research_status(
                _as_str(_pick(payload, "status", "validacao") or STATUS_NAO_APTO)
            ),
            tema=_as_str(_pick(payload, "tema", "theme", "tema_pesquisado")),
            janela_pesquisa=_as_str(_pick(payload, "janela_pesquisa", "search_window")),
            resumo=_as_str(_pick(payload, "resumo", "summary", "resumo_da_pesquisa")),
            noticias=noticias,
            contexto_impacto=_as_str(_pick(payload, "contexto_impacto", "context")),
            pontos_atencao=_as_str_list(pontos),
            links_consultados=[
                link for link in _as_str_list(links) if is_safe_public_url(link)
            ],
            bruto=text,
        )
        if resultado.status == STATUS_APTO and not resultado.noticias:
            resultado.status = STATUS_NAO_APTO
            resultado.pontos_atencao.append(
                "Status APTO ignorado porque nenhuma noticia validada foi extraida."
            )
        return resultado

    status_match = re.search(
        r"Status de validacao:\s*(.+)",
        text,
        re.IGNORECASE,
    )
    tema_match = re.search(r"Tema pesquisado:\s*(.+)", text, re.IGNORECASE)
    janela_match = re.search(r"Janela de pesquisa:\s*(.+)", text, re.IGNORECASE)

    pontos_raw = _section_text(
        text,
        "Pontos de atencao:",
        ["Links consultados:"],
    )
    links_raw = _section_text(text, "Links consultados:", [])

    resultado = ResultadoPesquisa(
        status=normalize_research_status(status_match.group(1) if status_match else STATUS_NAO_APTO),
        tema=_as_str(tema_match.group(1) if tema_match else ""),
        janela_pesquisa=_as_str(janela_match.group(1) if janela_match else ""),
        resumo=_section_text(
            text,
            "Resumo da pesquisa:",
            ["Noticias validadas:"],
        ),
        noticias=_parse_text_noticias(text),
        contexto_impacto=_section_text(
            text,
            "Contexto e impacto:",
            ["Pontos de atencao:", "Links consultados:"],
        ),
        pontos_atencao=[
            line.strip(" -")
            for line in pontos_raw.splitlines()
            if line.strip(" -")
        ],
        links_consultados=[
            part.strip(" -")
            for part in re.findall(r"https?://\S+", links_raw)
            if is_safe_public_url(part.strip(" -"))
        ],
        bruto=text,
    )
    if resultado.status == STATUS_APTO and not resultado.noticias:
        resultado.status = STATUS_NAO_APTO
        resultado.pontos_atencao.append(
            "Status APTO ignorado porque nenhuma noticia validada foi extraida."
        )
    return resultado


def render_research_text(resultado: ResultadoPesquisa) -> str:
    status_label = (
        STATUS_APTO_LABEL if resultado.status == STATUS_APTO else STATUS_NAO_APTO_LABEL
    )
    lines = [
        f"Status de validacao: {status_label}",
        f"Tema pesquisado: {resultado.tema}",
        f"Janela de pesquisa: {resultado.janela_pesquisa}",
        "",
        "Resumo da pesquisa:",
        f"- {resultado.resumo}" if resultado.resumo else "- Sem resumo.",
        "",
        "Noticias validadas:",
    ]

    if not resultado.noticias:
        lines.append("- Nenhuma noticia validada.")
    else:
        for index, noticia in enumerate(resultado.noticias, start=1):
            lines.extend(
                [
                    f"{index}. {noticia.titulo}",
                    f"   Fonte: {noticia.fonte}",
                    f"   Data: {noticia.data}",
                    f"   Link: {noticia.link}",
                    f"   Imagem sugerida: {noticia.imagem_sugerida}",
                    f"   O que aconteceu: {noticia.o_que_aconteceu}",
                    f"   Por que e relevante: {noticia.por_que_e_relevante}",
                    f"   Contexto adicional: {noticia.contexto_adicional}",
                    f"   Evidencias encontradas: {noticia.evidencias}",
                    "",
                ]
            )

    lines.extend(
        [
            "Contexto e impacto:",
            resultado.contexto_impacto or "- Sem contexto adicional.",
            "",
            "Pontos de atencao:",
        ]
    )
    if resultado.pontos_atencao:
        lines.extend(f"- {item}" for item in resultado.pontos_atencao)
    else:
        lines.append("- Nenhum.")

    lines.extend(["", "Links consultados:"])
    if resultado.links_consultados:
        lines.extend(f"- {link}" for link in resultado.links_consultados)
    else:
        lines.append("- Nenhum.")

    return "\n".join(lines).strip()
