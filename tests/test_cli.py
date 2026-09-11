from __future__ import annotations

from src.main import parse_args


def test_parse_args_defaults():
    args = parse_args([])
    assert args.subject is None
    assert args.days is None
    assert args.dry_run is False
    assert args.skip_email is False
    assert args.log_level is None


def test_parse_args_flags():
    args = parse_args(
        [
            "--subject",
            "Agentes",
            "--days",
            "5",
            "--dry-run",
            "--skip-email",
            "--log-level",
            "DEBUG",
        ]
    )
    assert args.subject == "Agentes"
    assert args.days == 5
    assert args.dry_run is True
    assert args.skip_email is True
    assert args.log_level == "DEBUG"
