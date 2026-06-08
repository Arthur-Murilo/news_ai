import os
import time
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv

from src.main import run_workflow

load_dotenv()


@dataclass(frozen=True)
class ScheduleConfig:
    day: int
    hour: int


def _read_int_env(name: str) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        raise ValueError(f"A variavel de ambiente {name} e obrigatoria.")

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"A variavel de ambiente {name} deve ser um numero inteiro."
        ) from exc


def load_schedule_config() -> ScheduleConfig:
    day = _read_int_env("SCHEDULE_DAY")
    hour = _read_int_env("SCHEDULE_HOUR")

    if not 1 <= day <= 31:
        raise ValueError("SCHEDULE_DAY deve estar entre 1 e 31.")
    if not 0 <= hour <= 23:
        raise ValueError("SCHEDULE_HOUR deve estar entre 0 e 23.")

    return ScheduleConfig(day=day, hour=hour)


def _execution_key(now: datetime) -> str:
    return now.strftime("%Y-%m")


def _sleep_until_next_minute() -> None:
    now = datetime.now().astimezone()
    seconds_until_next_minute = 60 - now.second
    if seconds_until_next_minute <= 0:
        seconds_until_next_minute = 60
    time.sleep(seconds_until_next_minute)


def run_scheduler() -> None:
    config = load_schedule_config()
    last_execution_key: str | None = None
    now = datetime.now().astimezone()

    print(
        "Scheduler iniciado para executar no dia "
        f"{config.day} as {config.hour:02d}:00. "
        f"Timezone atual: {now.tzinfo}. Hora atual: {now.isoformat(timespec='seconds')}."
    )

    while True:
        now = datetime.now().astimezone()
        current_key = _execution_key(now)

        if now.day == config.day and now.hour == config.hour:
            if last_execution_key != current_key:
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
