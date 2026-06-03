import resend
import os
from datetime import datetime
from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage
from typing import cast
from dotenv import load_dotenv

load_dotenv()


def send_email(html: str):
    resend.api_key = os.getenv("RESEND_API_KEY")
    today = datetime.now().strftime("%Y-%m-%d")

    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": "arthurmurilo49@gmail.com",
        "subject": f"Relatorio News AI - {today}",
        "html": html,
    })

    return "Email enviado com sucesso."


def node_send_email(state: MessagesState):
    email = state["messages"][-1].content

    finish_email = send_email(cast(str, email))

    # Retorna o objeto AIMessage que o MessagesState exige
    return {"messages": [AIMessage(content=finish_email)]}
