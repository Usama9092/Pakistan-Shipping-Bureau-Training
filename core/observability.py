from __future__ import annotations
import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from typing import Iterator

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SLOW_QUERY_MS = float(os.getenv("SLOW_QUERY_MS", "500"))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("psb")

@dataclass
class Timing:
    name: str
    elapsed_ms: float

@contextmanager
def timed(name: str, threshold_ms: float | None = None) -> Iterator[Timing]:
    start = time.perf_counter()
    result = Timing(name=name, elapsed_ms=0.0)
    try:
        yield result
    finally:
        result.elapsed_ms = (time.perf_counter() - start) * 1000
        threshold = SLOW_QUERY_MS if threshold_ms is None else threshold_ms
        if result.elapsed_ms >= threshold:
            logger.warning("slow_operation name=%s elapsed_ms=%.2f", name, result.elapsed_ms)


def performance_snapshot() -> dict:
    return {
        "log_level": LOG_LEVEL,
        "slow_query_threshold_ms": SLOW_QUERY_MS,
    }
