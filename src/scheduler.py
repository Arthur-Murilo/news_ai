from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import time

from src.main import run_workflow
from src.settings import (
    ALLOWED_SCHEDULE_FREQUENCIES,
    APP_TIMEZONE,
    load_settings,
)


@dataclass(frozen=True)
class ScheduleConfig:
    frequency: str
    hour: int
    weekday: int | None = None
    day: int | None = None


def _now() -> datetime:
    return datetime.now(APP_TIMEZONE)


def load_schedule_config() -> ScheduleConfig:
    settings = load_settings()
    frequency = settings.schedule_frequency
    if frequency not in ALLOWED_SCHEDULE_FREQUENCIES:
        raise ValueError("SCHEDULE_FREQUENCY deve ser daily, weekly ou monthly.")

    if frequency == "daily":
        return ScheduleConfig(frequency=frequency, hour=settings.schedule_hour)

    if frequency == "weekly":
        return ScheduleConfig(
            frequency=frequency,
            hour=settings.schedule_hour,
            weekday=settings.schedule_weekday,
        )

    return ScheduleConfig(
        frequency=frequency,
        hour=settings.schedule_hour,
        day=settings.schedule_day,
    )


def scheduler_state_path() -> Path:
    return load_settings().data_dir / "scheduler_state.json"


def load_last_execution_key(path: Path | None = None) -> str | None:
    state_path = path or scheduler_state_path()
    if not state_path.exists():
        return None
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    key = payload.get("last_success_key")
    if isinstance(key, str) and key.strip():
        return key.strip()
    return None


def save_last_execution_key(key: str, path: Path | None = None) -> None:
    state_path = path or scheduler_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"last_success_key": key}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _execution_key(config: ScheduleConfig, now: datetime) -> str:
    if config.frequency == "daily":
        return now.strftime("%Y-%m-%d")
    if config.frequency == "weekly":
        return now.strftime("%G-W%V")
    return now.strftime("%Y-%m")


def _effective_month_day(config: ScheduleConfig, now: datetime) -> int:
    last_day = calendar.monthrange(now.year, now.month)[1]
    if config.day is None:
        return now.day
    return min(config.day, last_day)


def _should_run_now(config: ScheduleConfig, now: datetime) -> bool:
    if now.minute != 0:
        return False

    if config.frequency == "daily":
        return now.hour == config.hour

    if config.frequency == "weekly":
        return now.isoweekday() == config.weekday and now.hour == config.hour

    return now.day == _effective_month_day(config, now) and now.hour == config.hour


def _sleep_until_next_minute() -> None:
    now = _now()
    seconds_until_next_minute = 60 - now.second
    if seconds_until_next_minute <= 0:
        seconds_until_next_minute = 60
    time.sleep(seconds_until_next_minute)


def _describe_schedule(config: ScheduleConfig) -> str:
    if config.frequency == "daily":
        return f"todo dia as {config.hour:02d}:00"
    if config.frequency == "weekly":
        return f"toda semana no dia {config.weekday} as {config.hour:02d}:00"
    return f"todo mes no dia {config.day} as {config.hour:02d}:00"


def run_scheduler() -> None:
    config = load_schedule_config()
    last_execution_key = load_last_execution_key()
    now = _now()

    print(
        "Scheduler iniciado para executar "
        f"{_describe_schedule(config)}. "
        f"Timezone: America/Sao_Paulo. Hora atual: "
        f"{now.isoformat(timespec='seconds')}."
    )

    while True:
        now = _now()
        current_key = _execution_key(config, now)

        if _should_run_now(config, now) and last_execution_key != current_key:
            print(
                "Executando workflow agendado em "
                f"{now.isoformat(timespec='seconds')}."
            )
            try:
                run_workflow()
            except Exception as exc:
                print(f"Falha na execucao agendada: {exc}")
            else:
                save_last_execution_key(current_key)
                last_execution_key = current_key

        _sleep_until_next_minute()


if __name__ == "__main__":
    run_scheduler()
