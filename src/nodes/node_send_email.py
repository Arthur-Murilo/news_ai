from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

import resend
from langchain_core.messages import AIMessage

from src.security import looks_like_html, sanitize_newsletter_html
from src.sent_news import mark_research_as_sent
from src.settings import APP_TIMEZONE, load_settings
from src.state import STATUS_ERRO, NewsletterState
from src.utils import extract_message_text, strip_markdown_code_fences

logger = logging.getLogger(__name__)


def write_preview(html: str, path: Path | None = None) -> Path:
    settings = load_settings()
    target = path or settings.preview_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    logger.info("Preview gravado em %s (%s caracteres)", target, len(html))
    return target


def send_email(html: str) -> str:
    settings = load_settings()
    settings.validate_for_workflow(skip_email=False)
    resend.api_key = settings.resend_api_key
    today = datetime.now(APP_TIMEZONE).strftime("%Y-%m-%d")
    sanitized_html = sanitize_newsletter_html(strip_markdown_code_fences(html))
    if not sanitized_html.strip() or not looks_like_html(sanitized_html):
        raise ValueError("HTML da newsletter invalido apos sanitizacao.")

    logger.info(
        "Enviando email via Resend. from=%s to=%s html=%s caracteres",
        settings.newsletter_from_email,
        settings.newsletter_to_email,
        len(sanitized_html),
    )
    resend.Emails.send(
        {
            "from": settings.newsletter_from_email,
            "to": settings.newsletter_to_email,
            "subject": f"Relatorio News AI - {today}",
            "html": sanitized_html,
        }
    )
    return "Email enviado com sucesso."


def node_send_email(state: NewsletterState):
    started = time.perf_counter()
    try:
        html = extract_message_text(state.get("html") or "")
        if not html:
            html = extract_message_text(state["messages"][-1].content)

        logger.info("Etapa envio de email iniciada. html=%s caracteres", len(html))
        sanitized_html = sanitize_newsletter_html(strip_markdown_code_fences(html))
        if not sanitized_html.strip() or not looks_like_html(sanitized_html):
            raise ValueError("HTML da newsletter invalido apos sanitizacao.")

        preview = write_preview(sanitized_html)
        skip_email = bool(state.get("skip_email") or state.get("dry_run"))
        if skip_email:
            message = f"Envio ignorado. Preview em {preview}."
            logger.info(
                "Etapa envio de email concluida em %.1fs. envio ignorado (dry-run/skip-email).",
                time.perf_counter() - started,
            )
            return {
                "messages": [AIMessage(content=message)],
                "html": sanitized_html,
                "email_result": message,
                "error": "",
            }

        result = send_email(sanitized_html)
        mark_research_as_sent(state.get("research_payload") or {})
        logger.info(
            "Etapa envio de email concluida em %.1fs. email enviado.",
            time.perf_counter() - started,
        )
        return {
            "messages": [AIMessage(content=result)],
            "html": sanitized_html,
            "email_result": result,
            "error": "",
        }
    except Exception as exc:
        message = str(exc)
        logger.exception(
            "Etapa envio de email falhou apos %.1fs: %s",
            time.perf_counter() - started,
            message,
        )
        return {
            "messages": [AIMessage(content=message)],
            "status": STATUS_ERRO,
            "error": message,
        }
