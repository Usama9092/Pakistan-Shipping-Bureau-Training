from __future__ import annotations
from datetime import date
from typing import Any, Callable
from .access_policy import ROLE_ALLOWED_SCOPES, ROLE_MODULE_SCOPE_DEFAULTS, scope_permission_allowed


def can_action(
    actor: dict,
    module: str,
    action: str,
    scope: str,
    *,
    db_all: Callable[[str], Any],
    db_where: Callable[..., Any],
    actor_get: Callable[[dict, str, str], str],
) -> bool:
    """Central RBAC decision: role permission first, then time-bounded user override.

    The caller owns the database/cache implementation. This keeps authorization logic
    testable and prevents page-specific permission forks.
    """
    if not isinstance(actor, dict) or not actor_get(actor, "user_id", ""):
        return False
    role = actor_get(actor, "role", "")
    allowed_scopes = ROLE_ALLOWED_SCOPES.get(role, {"Own"})
    from .access_policy import POLICY_LOAD_ERROR
    module_scopes = ROLE_MODULE_SCOPE_DEFAULTS.get(role, {}).get(module)
    if POLICY_LOAD_ERROR and role not in {"Admin", "GM"}:
        return False
    if module_scopes is not None and scope not in module_scopes:
        return False
    if module_scopes is None and role not in {"Admin", "GM", "Management", "QMR"} and module not in {"Dashboard", "Employee Profile", "Knowledge Library"}:
        return False
    if scope == "Organization-wide" and role not in {"Admin", "GM", "Management", "QMR"}:
        if not scope_permission_allowed(role, module, action, scope):
            return False
    elif scope not in allowed_scopes:
        return False
    try:
        perms = db_all("permissions")
        if perms.empty:
            return role in {"Admin", "GM"} and module == "Administration" and action == "Manage" and scope == "Organization-wide"
        p = perms[(perms["module_name"].astype(str) == module) &
                  (perms["action"].astype(str) == action) &
                  (perms["scope"].astype(str) == scope)]
        if p.empty:
            return False
        pid = str(p.iloc[0]["permission_id"])
        rp = db_where(
            "role_permissions",
            "role_name = :role and permission_id = :pid and enabled = 'Yes'",
            (("role", role), ("pid", pid)),
        )
        if not rp.empty:
            return True
        ov = db_where(
            "user_permission_overrides",
            "user_id = :uid and permission_id = :pid and enabled = 'Yes'",
            (("uid", actor_get(actor, "user_id", "")), ("pid", pid)),
        )
        if ov.empty:
            return False
        today = date.today().strftime("%Y-%m-%d")
        for _, row in ov.iterrows():
            start = str(row.get("effective_from") or "0000-00-00")[:10]
            end = str(row.get("effective_to") or "9999-12-31")[:10]
            if start <= today <= end:
                return True
        return False
    except Exception:
        return False


def authorize_record(actor: dict, module: str, action: str, row: dict | None, *, db_all, db_where, actor_get) -> bool:
    """Single record-level authorization boundary.

    This combines module/action permission and record scope so pages cannot
    accidentally authorize an action and then forget to enforce ownership.
    """
    from .access_policy import record_scope_allowed
    if not isinstance(actor, dict) or not actor_get(actor, 'user_id', ''):
        return False
    scope = __import__('core.access_policy', fromlist=['scope_for_actor_module']).scope_for_actor_module(actor, module)
    if module == 'Practical / Witness' and isinstance(row, dict):
        uid = actor_get(actor, 'user_id', '')
        subject = str(row.get('user_id') or row.get('trainee_id') or '')
        witness = str(row.get('witness_id') or row.get('proposed_witness_id') or '')
        if witness == uid and subject != uid:
            scope = 'Assigned'
        elif subject == uid:
            scope = 'Own'
    if not can_action(actor, module, action, scope, db_all=db_all, db_where=db_where, actor_get=actor_get):
        return False
    try:
        users = db_all('users')
        uds = db_all('user_departments')
        return bool(record_scope_allowed(actor, module, action, row, users, uds))
    except Exception:
        return False


def authorize_action(actor: dict, module: str, action: str, record: dict | None = None, *, db_all, db_where, actor_get) -> bool:
    """Single mandatory authorization boundary for business mutations and record actions.
    All callers should pass the concrete record when available; no page should need
    to compose can_action + scope checks manually.
    """
    return authorize_record(actor, module, action, record or {}, db_all=db_all, db_where=db_where, actor_get=actor_get)
