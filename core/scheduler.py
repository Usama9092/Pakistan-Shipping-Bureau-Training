from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Callable, Any
from core.system_write import system_write

@dataclass
class SchedulerResult:
    name: str
    ok: bool
    attempts: int
    started_at: str
    finished_at: str
    error: str = ""
    next_retry_at: str = ""

def run_with_retry(name: str, fn: Callable[[], Any], *, retries: int = 2, base_delay_seconds: float = 1.0) -> SchedulerResult:
    started = datetime.now(timezone.utc)
    last_error = ""
    attempts = 0
    next_retry = ""
    for attempt in range(1, retries + 2):
        attempts = attempt
        try:
            fn()
            return SchedulerResult(name, True, attempts, started.isoformat(), datetime.now(timezone.utc).isoformat())
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt <= retries:
                delay = base_delay_seconds * (2 ** (attempt - 1))
                next_retry = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat()
                sleep(delay)
    return SchedulerResult(name, False, attempts, started.isoformat(), datetime.now(timezone.utc).isoformat(), last_error, next_retry)

def run_recorded_job(name: str, fn: Callable[[], Any], *, db_insert: Callable[[str, dict], None], retries: int = 2, base_delay_seconds: float = 1.0) -> SchedulerResult:
    run_id = f"SCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    started = datetime.now(timezone.utc).isoformat()
    result = run_with_retry(name, fn, retries=retries, base_delay_seconds=base_delay_seconds)
    try:
        with system_write("scheduler_service"):
            db_insert("scheduler_runs", {
                "run_id": run_id, "job_name": name, "started_on": started,
                "finished_on": result.finished_at, "status": "Success" if result.ok else "Failed",
                "attempt": result.attempts, "error_message": result.error,
                "duration_ms": None, "retry_count": max(0, result.attempts - 1),
                "next_retry_at": result.next_retry_at, "heartbeat_on": result.finished_at,
            })
    except Exception:
        pass
    return result
