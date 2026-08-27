"""Extracted service boundary from the legacy runtime.
The module consumes the established runtime context for compatibility.
"""
from __future__ import annotations
from psb_app.legacy_runtime import (
    DEPARTMENTS,
    LOGO_PATH,
    base64,
    clean,
    database_is_persistent,
    db_all,
    io,
    is_render_runtime,
    pd,
    qrcode,
    re,
    st,
    storage_is_persistent,
)

def actor_get(actor: dict, key: str, default: str='') -> str:
    return clean(actor.get(key, default)) if isinstance(actor, dict) else default

def join_list(values: list[str]) -> str:
    return ', '.join(values)

def split_list(value: str) -> list[str]:
    return [x.strip() for x in re.split('[,;|]+', clean(value)) if x.strip()]

def logo_data_uri() -> str:
    if not LOGO_PATH.exists():
        return ''
    return 'data:image/png;base64,' + base64.b64encode(LOGO_PATH.read_bytes()).decode()

def make_qr_data_uri(value: str) -> str:
    img = qrcode.make(value)
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def backend_status_badges() -> str:
    db_badge = '✅ PostgreSQL/Supabase' if database_is_persistent() else '⚠️ Local SQLite'
    storage_badge = '✅ Supabase Storage' if storage_is_persistent() else '⚠️ Local files' if not is_render_runtime() else '❌ Storage missing'
    return f"<span class='pill'>{db_badge}</span><span class='pill'>{storage_badge}</span>"

def department_options() -> list[str]:
    try:
        deps = db_all('departments')
        active = deps[deps['status'] == 'Active']['department_name'].astype(str).tolist() if not deps.empty and 'status' in deps.columns else []
        return active or DEPARTMENTS
    except Exception:
        return DEPARTMENTS

def _user_label(row) -> str:
    return f"{row.get('name', '')} — {row.get('user_id', '')}"

def _parse_user_label(value: str) -> tuple[str, str]:
    if not value or ' — ' not in value:
        return ('', '')
    return value.split(' — ', 1)

def _user_label_series(users: pd.DataFrame) -> list[str]:
    if users is None or users.empty:
        return []
    return [_user_label(r) for _, r in users.iterrows()]

def select_person(label, roles=None, key=None):
    users = db_all('users')
    if users.empty:
        return ('', '', pd.Series(dtype=object))
    data = users if roles is None else users[users['role'].isin(roles)]
    if data.empty:
        return ('', '', pd.Series(dtype=object))
    item = st.selectbox(label, data['name'].astype(str) + ' — ' + data['user_id'].astype(str), key=key)
    name, uidv = item.split(' — ')
    return (name, uidv, data[data['user_id'] == uidv].iloc[0])

