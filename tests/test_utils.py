from __future__ import annotations

from src.utils import extract_message_text


def test_extract_message_text_from_common_shapes():
    assert extract_message_text("  ola  ") == "ola"
    assert extract_message_text([{"text": "parte 1"}, {"text": "parte 2"}]) == "parte 1\nparte 2"
    assert extract_message_text({"text": "unico"}) == "unico"
    assert extract_message_text(None) == ""
