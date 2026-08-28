from __future__ import annotations

import re


def extract_message_text(message_content: object) -> str:
    if isinstance(message_content, str):
        return message_content.strip()

    if isinstance(message_content, list):
        parts: list[str] = []
        for item in message_content:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = str(item.get("text", "")).strip()
            else:
                text = str(item).strip()

            if text:
                parts.append(text)

        return "\n".join(parts).strip()

    if isinstance(message_content, dict):
        return str(message_content.get("text", "")).strip()

    if message_content is None:
        return ""

    return str(message_content).strip()


def strip_markdown_code_fences(text: str) -> str:
    cleaned = text.strip()
    fenced_match = re.search(
        r"```(?:html)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL | re.IGNORECASE
    )
    if fenced_match:
        return fenced_match.group(1).strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned
