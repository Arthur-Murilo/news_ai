import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from src.main import run_workflow

load_dotenv()

SCHEDULE_TIMEZONE = timezone(
    timedelta(hours=-3),
    name="America/Sao_Paulo",
)
ALLOWED_SCHEDULE_FREQUENCIES = {"daily", "weekly", "monthly"}


@dataclass(frozen=True)
class ScheduleConfig:
    frequency: str
    hour: int
    weekday: int | None = None
    day: int | None = None


def _now() -> datetime:
    return datetime.now(SCHEDULE_TIMEZONE)


def _read_required_env(name: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        raise ValueError(f"A variavel de ambiente {name} e obrigatoria.")
    return raw_value.strip()


def _read_int_env(name: str) -> int:
    raw_value = _read_required_env(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"A variavel de ambiente {name} deve ser um numero inteiro."
        ) from exc


def load_schedule_config() -> ScheduleConfig:
    frequency = _read_required_env("SCHEDULE_FREQUENCY").lower()
    if frequency not in ALLOWED_SCHEDULE_FREQUENCIES:
        raise ValueError(
            "SCHEDULE_FREQUENCY deve ser daily, weekly ou monthly."
        )

    hour = _read_int_env("SCHEDULE_HOUR")
    if not 0 <= hour <= 23:
        raise ValueError("SCHEDULE_HOUR deve estar entre 0 e 23.")

    if frequency == "daily":
        return ScheduleConfig(frequency=frequency, hour=hour)

    if frequency == "weekly":
        weekday = _read_int_env("SCHEDULE_WEEKDAY")
        if not 1 <= weekday <= 7:
            raise ValueError("SCHEDULE_WEEKDAY deve estar entre 1 e 7.")
        return ScheduleConfig(frequency=frequency, hour=hour, weekday=weekday)

    day = _read_int_env("SCHEDULE_DAY")
    if not 1 <= day <= 31:
        raise ValueError("SCHEDULE_DAY deve estar entre 1 e 31.")
    return ScheduleConfig(frequency=frequency, hour=hour, day=day)


def _execution_key(config: ScheduleConfig, now: datetime) -> str:
    if config.frequency == "daily":
        return now.strftime("%Y-%m-%d")
    if config.frequency == "weekly":
        return now.strftime("%G-W%V")
    return now.strftime("%Y-%m")


def _should_run_now(config: ScheduleConfig, now: datetime) -> bool:
    if now.minute != 0:
        return False

    if config.frequency == "daily":
        return now.hour == config.hour

    if config.frequency == "weekly":
        return now.isoweekday() == config.weekday and now.hour == config.hour

    return now.day == config.day and now.hour == config.hour


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
    last_execution_key: str | None = None
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
            finally:
                last_execution_key = current_key

        _sleep_until_next_minute()


if __name__ == "__main__":
    run_scheduler()
