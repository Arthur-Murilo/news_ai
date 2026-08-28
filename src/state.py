from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

STATUS_PENDING = "pending"
STATUS_APTO = "apto"
STATUS_NAO_APTO = "nao_apto"
STATUS_ERRO = "erro"


class NewsletterState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    subject: str
    status: str
    research_text: str
    research_payload: dict[str, Any]
    html: str
    error: str
    skip_email: bool
    dry_run: bool
    email_result: str
