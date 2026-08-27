from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Callable


def application_health(*, database_is_persistent: Callable[[], bool], storage_is_persistent: Callable[[], bool], schema_report: dict) -> dict:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "database_persistent": bool(database_is_persistent()),
        "storage_persistent": bool(storage_is_persistent()),
        "schema_contract_ok": bool(schema_report.get("contract_ok")),
        "missing_schema_tables": schema_report.get("missing_tables", []),
        "status": "healthy" if database_is_persistent() and storage_is_persistent() and schema_report.get("contract_ok") else "degraded",
    }
