"""Extracted service boundary from the legacy runtime.
The module consumes the established runtime context for compatibility.
"""
from __future__ import annotations
from psb_app.legacy_runtime import (
    actor_get,
    clean,
    db_all,
    db_insert,
    db_where,
    now,
    pd,
    st,
    system_write,
    table_exists,
    uid,
)

def audit(action: str, details: str | None='', result: str='Success', actor: dict | None=None, entity_type: str='', entity_id: str='', reason: str='', before_value: str='', after_value: str='') -> None:
    """Write an immutable business-level audit event.

    The audit trail is intentionally richer than a raw database UPDATE log so
    administrators can understand who changed what, why, and the before/after
    state of sensitive records.
    """
    actor_data = actor or st.session_state.get('user', {})
    details = clean(details)
    with system_write('audit_event'):
        db_insert('audit_trail', {'audit_id': uid('AUD'), 'date_time': now(), 'actor_id': actor_get(actor_data, 'user_id'), 'actor_name': actor_get(actor_data, 'name', 'System'), 'actor_role': actor_get(actor_data, 'role', 'System'), 'action': action, 'details': details, 'result': result, 'entity_type': entity_type, 'entity_id': entity_id, 'reason': clean(reason), 'before_value': clean(before_value), 'after_value': clean(after_value), 'session_id': clean(st.session_state.get('session_id', ''))})

def create_notification(user_id: str, subject: str, message: str, ntype: str) -> None:
    u = db_where('users', 'user_id = :user_id', (('user_id', user_id),))
    if u.empty:
        return
    row = u.iloc[0]
    with system_write('notification_create'):
        db_insert('notifications', {'notification_id': uid('NOT'), 'user_id': row['user_id'], 'name': row['name'], 'email': row['email'], 'subject': subject, 'message': message, 'type': ntype, 'status': 'Generated', 'created_on': now(), 'sent_on': ''})

def scheduler_record(job_name: str, status: str, started_on: str, finished_on: str='', attempt: int=1, error_message: str='', duration_ms: float=0.0) -> None:
    if not table_exists('scheduler_runs'):
        return
    with system_write('scheduler_run'):
        db_insert('scheduler_runs', {'run_id': uid('SCH'), 'job_name': job_name, 'started_on': started_on, 'finished_on': finished_on or now(), 'status': status, 'attempt': attempt, 'error_message': error_message, 'duration_ms': duration_ms})

def scheduler_health_summary() -> dict:
    runs = db_all('scheduler_runs') if table_exists('scheduler_runs') else pd.DataFrame()
    if runs.empty:
        return {'last_status': 'No runs recorded', 'failed_24h': 0, 'last_run': '—'}
    runs['started_on_dt'] = pd.to_datetime(runs['started_on'], errors='coerce')
    cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(hours=24)
    recent = runs[runs['started_on_dt'] >= cutoff]
    return {'last_status': str(runs.sort_values('started_on_dt').iloc[-1].get('status', 'Unknown')), 'failed_24h': int((recent['status'].astype(str).str.lower() == 'failed').sum()), 'last_run': str(runs.sort_values('started_on_dt').iloc[-1].get('finished_on', runs.iloc[-1].get('started_on', '—')))}

def kpi_definitions_frame() -> pd.DataFrame:
    return db_all('kpi_definitions') if table_exists('kpi_definitions') else pd.DataFrame()
