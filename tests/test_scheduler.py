from __future__ import annotations

from datetime import datetime

from src.scheduler import (
    ScheduleConfig,
    _effective_month_day,
    _execution_key,
    _should_run_now,
    load_last_execution_key,
    save_last_execution_key,
)
from src.settings import APP_TIMEZONE


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=APP_TIMEZONE)


def test_daily_and_weekly_execution_keys():
    now = _dt("2026-08-22T17:00:00")
    assert _execution_key(ScheduleConfig("daily", 17), now) == "2026-08-22"
    assert _execution_key(ScheduleConfig("weekly", 17, weekday=6), now) == "2026-W34"
    assert _execution_key(ScheduleConfig("monthly", 17, day=31), now) == "2026-08"


def test_should_run_now_requires_exact_hour():
    config = ScheduleConfig("daily", 17)
    assert _should_run_now(config, _dt("2026-08-22T17:00:00"))
    assert not _should_run_now(config, _dt("2026-08-22T17:01:00"))
    assert not _should_run_now(config, _dt("2026-08-22T16:00:00"))


def test_monthly_day_falls_back_to_last_day_of_month():
    config = ScheduleConfig("monthly", 9, day=31)
    feb_28 = _dt("2026-02-28T09:00:00")
    assert _effective_month_day(config, feb_28) == 28
    assert _should_run_now(config, feb_28)
    assert not _should_run_now(config, _dt("2026-02-27T09:00:00"))


def test_scheduler_persists_only_explicit_success(tmp_path):
    path = tmp_path / "scheduler_state.json"
    assert load_last_execution_key(path) is None

    save_last_execution_key("2026-08-22", path)
    assert load_last_execution_key(path) == "2026-08-22"
