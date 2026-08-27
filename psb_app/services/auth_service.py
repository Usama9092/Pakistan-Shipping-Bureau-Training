"""Extracted service boundary from the legacy runtime.
The module consumes the established runtime context for compatibility.
"""
from __future__ import annotations
from psb_app.legacy_runtime import (
    _session_hash,
    PASSWORD_HASHER,
    SESSION_IDLE_MINUTES,
    SESSION_MAX_HOURS,
    clean,
    components,
    datetime,
    db_insert,
    db_update,
    db_where,
    hashlib,
    now,
    secrets,
    st,
    string,
    system_write,
    timedelta,
    uid,
)

def create_auth_token(user_id: str) -> str:
    token = secrets.token_urlsafe(48)
    created = now()
    expires = (datetime.utcnow() + timedelta(hours=SESSION_MAX_HOURS)).strftime('%Y-%m-%d %H:%M:%S')
    with system_write('auth_session_create'):
        db_insert('auth_sessions', {'session_id': uid('SES'), 'token_hash': _session_hash(token), 'user_id': user_id, 'created_on': created, 'last_seen': created, 'expires_at': expires, 'revoked_on': ''})
    return token

def resolve_auth_token(token: str) -> str | None:
    token = clean(token)
    if not token:
        return None
    try:
        session = db_where('auth_sessions', "token_hash = :token_hash and revoked_on = ''", (('token_hash', _session_hash(token)),))
        if session.empty:
            return None
        row = session.iloc[0]
        now_dt = datetime.utcnow()
        created = datetime.strptime(str(row.get('created_on'))[:19], '%Y-%m-%d %H:%M:%S') if row.get('created_on') else now_dt
        last_seen = datetime.strptime(str(row.get('last_seen'))[:19], '%Y-%m-%d %H:%M:%S') if row.get('last_seen') else created
        expires_at = datetime.strptime(str(row.get('expires_at'))[:19], '%Y-%m-%d %H:%M:%S') if row.get('expires_at') else created + timedelta(hours=SESSION_MAX_HOURS)
        if now_dt - last_seen > timedelta(minutes=SESSION_IDLE_MINUTES) or now_dt > expires_at:
            with system_write('auth_session_revoke'):
                db_update('auth_sessions', 'session_id', str(row.get('session_id')), {'revoked_on': now()})
            return None
        with system_write('auth_session_touch'):
            db_update('auth_sessions', 'session_id', str(row.get('session_id')), {'last_seen': now()})
        return str(row.get('user_id') or '') or None
    except Exception:
        return None

def clear_auth_token() -> None:
    token = clean(st.session_state.get('auth_token', ''))
    if token:
        try:
            rows = db_where('auth_sessions', "token_hash = :token_hash and revoked_on = ''", (('token_hash', _session_hash(token)),))
            if not rows.empty:
                with system_write('auth_session_revoke'):
                    db_update('auth_sessions', 'session_id', str(rows.iloc[0].get('session_id')), {'revoked_on': now()})
        except Exception:
            pass
    st.session_state.pop('auth_token', None)
    # Local authentication tokens remain server-side in Streamlit session state.
    # Never expose bearer tokens in query strings, browser-readable cookies, or logs.
    try:
        getattr(st, 'experimental_set_query_params', lambda **kwargs: None)()
    except Exception:
        pass

def phash(password: str) -> str:
    """Hash passwords with Argon2id. Legacy SHA-256 hashes are only accepted during login migration."""
    if PASSWORD_HASHER is None:
        raise RuntimeError('Argon2 password hashing is unavailable. Install argon2-cffi before enabling local authentication.')
    return PASSWORD_HASHER.hash(clean(password))

def verify_password(stored_hash: str, password: str) -> tuple[bool, bool]:
    """Return (valid, needs_rehash). Supports one-time migration from legacy SHA-256."""
    stored = clean(stored_hash)
    candidate = clean(password)
    if not stored or not candidate:
        return (False, False)
    if stored.startswith('$argon2'):
        try:
            valid = PASSWORD_HASHER.verify(stored, candidate) if PASSWORD_HASHER else False
            return (bool(valid), bool(valid and PASSWORD_HASHER.check_needs_rehash(stored)))
        except Exception:
            return (False, False)
    legacy = hashlib.sha256(candidate.encode('utf-8')).hexdigest()
    return (secrets.compare_digest(stored, legacy), True)

def temp_password(n: int=10) -> str:
    return ''.join((secrets.choice(string.ascii_letters + string.digits + '@#$') for _ in range(n)))
