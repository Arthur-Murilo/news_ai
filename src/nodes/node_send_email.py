import os
from datetime import datetime, timedelta, timezone
from typing import cast

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState
import resend

from src.security import sanitize_newsletter_html

load_dotenv()

APP_TIMEZONE = timezone(
    timedelta(hours=-3),
    name="America/Sao_Paulo",
)


def _read_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ValueError(f"A variavel de ambiente {name} e obrigatoria.")
    return value.strip()


def send_email(html: str):
    resend.api_key = _read_required_env("RESEND_API_KEY")
    today = datetime.now(APP_TIMEZONE).strftime("%Y-%m-%d")
    sender = _read_required_env("NEWSLETTER_FROM_EMAIL")
    recipient = _read_required_env("NEWSLETTER_TO_EMAIL")
    sanitized_html = sanitize_newsletter_html(html)

    resend.Emails.send(
        {
            "from": sender,
            "to": recipient,
            "subject": f"Relatorio News AI - {today}",
            "html": sanitized_html,
        }
    )

    return "Email enviado com sucesso."


def node_send_email(state: MessagesState):
    email = state["messages"][-1].content
    finish_email = send_email(cast(str, email))
    return {"messages": [AIMessage(content=finish_email)]}
