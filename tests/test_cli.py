from __future__ import annotations

from src.main import parse_args


def test_parse_args_defaults():
    args = parse_args([])
    assert args.subject is None
    assert args.days is None
    assert args.dry_run is False
    assert args.skip_email is False


def test_parse_args_flags():
    args = parse_args(
        ["--subject", "Agentes", "--days", "5", "--dry-run", "--skip-email"]
    )
    assert args.subject == "Agentes"
    assert args.days == 5
    assert args.dry_run is True
    assert args.skip_email is True
