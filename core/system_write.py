from __future__ import annotations
from contextlib import contextmanager
import contextvars

_SYSTEM_WRITE = contextvars.ContextVar("psb_system_write", default=False)

def is_system_write() -> bool:
    return bool(_SYSTEM_WRITE.get())

@contextmanager
def system_write(reason: str = ""):
    token = _SYSTEM_WRITE.set(True)
    try:
        yield
    finally:
        _SYSTEM_WRITE.reset(token)
