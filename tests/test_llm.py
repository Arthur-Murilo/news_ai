from __future__ import annotations

import pytest

from src.llm import call_with_retries, describe_llm_error, is_transient_llm_error


class ReadError(Exception):
    pass


def test_is_transient_winerror_10054_in_message():
    exc = ReadError(
        "[WinError 10054] Foi forçado o cancelamento de uma conexão existente pelo host remoto"
    )
    assert is_transient_llm_error(exc)


def test_is_transient_nested_oserror():
    inner = OSError(104, "Connection reset by peer")
    inner.errno = 104
    outer = ReadError("stream failed")
    outer.__cause__ = inner
    assert is_transient_llm_error(outer)


def test_value_error_is_not_transient():
    assert not is_transient_llm_error(ValueError("HTML invalido"))


def test_call_with_retries_recovers_after_transient_error():
    calls = {"n": 0}

    def operation() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise ReadError("connection reset")
        return "ok"

    assert (
        call_with_retries(operation, attempts=3, delay_seconds=0, what="teste") == "ok"
    )
    assert calls["n"] == 2


def test_call_with_retries_gives_up_on_persistent_transient_error():
    def operation() -> str:
        raise ReadError("connection reset")

    with pytest.raises(ReadError, match="connection reset"):
        call_with_retries(operation, attempts=2, delay_seconds=0, what="teste")


def test_describe_llm_error_explains_remote_reset():
    message = describe_llm_error(ReadError("[WinError 10054] reset"))
    assert "host remoto" in message
    assert "WinError 10054" in message or "10054" in message
