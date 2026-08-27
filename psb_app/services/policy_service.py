"""Extracted service boundary from the legacy runtime.
The module consumes the established runtime context for compatibility.
"""
from __future__ import annotations
from core.access_policy import allowed_user_ids as _policy_allowed_user_ids, filter_frame as _policy_filter_frame
from core.authorization import can_action as _core_can_action
from psb_app.legacy_runtime import (
    actor_get,
    db_all,
    db_all_unscoped,
    db_where_unscoped,
    pd,
    table_exists,
)

def allowed_user_ids(actor: dict) -> set[str]:
    users = db_all('users')
    uds = db_all('user_departments') if table_exists('user_departments') else pd.DataFrame()
    return _policy_allowed_user_ids(actor, users, uds)

def restrict_user_frame(frame, actor: dict, user_col: str='user_id'):
    users = db_all('users')
    uds = db_all('user_departments') if table_exists('user_departments') else pd.DataFrame()
    return _policy_filter_frame(frame, actor, users, uds)

def can_action(actor: dict, module: str, action: str, scope: str='Organization-wide') -> bool:
    return _core_can_action(actor, module, action, scope, db_all=db_all_unscoped, db_where=db_where_unscoped, actor_get=actor_get)

def access_record(actor: dict, module: str, action: str, scope: str, row: dict | None) -> bool:
    users = db_all('users')
    uds = db_all('user_departments') if table_exists('user_departments') else pd.DataFrame()
    from core.access_policy import record_access
    return record_access(actor, module, action, scope, row, users, uds, permission_ok=can_action(actor, module, action, scope))
