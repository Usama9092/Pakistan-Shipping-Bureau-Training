from __future__ import annotations
import logging
import os
import time
import uuid
from contextlib import contextmanager

logger = logging.getLogger('psb.production')

@contextmanager
def page_execution(page: str, role: str = ''):
    rid = uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        yield rid
    except Exception:
        logger.exception('page_error page=%s role=%s request_id=%s', page, role, rid)
        raise
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed >= float(os.getenv('PAGE_SLOW_MS', '1500')):
            logger.warning('slow_page page=%s role=%s request_id=%s elapsed_ms=%.2f', page, role, rid, elapsed)

def production_config_report() -> dict:
    return {
        'app_env': os.getenv('APP_ENV', 'local'),
        'auth_mode': os.getenv('AUTH_MODE', 'local'),
        'supabase_auth_enabled': bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY')),
        'database_persistent': str(os.getenv('DATABASE_URL', '')).startswith(('postgresql://','postgresql+psycopg2://','postgres://')),
        'page_slow_ms': os.getenv('PAGE_SLOW_MS', '1500'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    }
