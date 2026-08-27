from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / 'config' / 'role_view_context_policy.json'


def _load() -> dict:
    try:
        return json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}


def context_for(role: str, page: str) -> str:
    policy = _load()
    role_map = policy.get('Surveyor' if role in {'NSC Surveyor','In-Service Surveyor'} else role, {})
    ctx = role_map.get(page)
    if ctx:
        return str(ctx)
    # Conservative default: unknown role/page is self-scoped.
    return 'Own'


def set_context(actor, page: str) -> str:
    role = str((actor or {}).get('role', '') if isinstance(actor, dict) else '')
    ctx = context_for(role, page)
    return ctx
