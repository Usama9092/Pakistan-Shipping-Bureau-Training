"""Notification lifecycle helpers with retry/backoff metadata."""
from __future__ import annotations
from datetime import datetime
from typing import Callable, Any
from core.system_write import system_write

def queue_notification(db_insert: Callable[[str, dict], None], uid: str, user_id: str, subject: str, message: str, ntype: str, email: str = "") -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with system_write("notification_service"):
        db_insert("notifications", {
            "notification_id": uid, "user_id": user_id, "subject": subject, "message": message,
            "type": ntype, "status": "Queued", "delivery_status": "Queued", "retry_count": 0,
            "next_retry_at": "", "last_error": "", "created_on": now, "sent_on": "",
            "delivered_on": "", "acknowledged_on": "", "email": email,
        })

def record_delivery(db_update: Callable[[str, str, str, dict], None], notification_id: str, *, ok: bool, error: str = "", attempts: int = 0, next_retry_at: str = "") -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    patch = {
        "delivery_status": "Delivered" if ok else "Retry Scheduled",
        "status": "Sent" if ok else "Queued", "retry_count": attempts,
        "last_error": error, "next_retry_at": "" if ok else next_retry_at,
        "sent_on": now if ok else "", "delivered_on": now if ok else "",
    }
    with system_write("notification_service"):
        db_update("notifications", "notification_id", notification_id, patch)
