from __future__ import annotations
import json
from pathlib import Path

_POLICY_FILE = Path(__file__).resolve().parents[1] / 'config' / 'practical_witness_policy.json'
try:
    _POLICY = json.loads(_POLICY_FILE.read_text(encoding='utf-8'))
except Exception:
    _POLICY = {'witness_roles': [], 'senior_witness_roles': [], 'workspace_modes': {}}

WITNESS_ROLES = frozenset(str(x) for x in _POLICY.get('witness_roles', []))
SENIOR_WITNESS_ROLES = frozenset(str(x) for x in _POLICY.get('senior_witness_roles', []))


def is_witness_role(role: str) -> bool:
    return str(role) in WITNESS_ROLES


def is_senior_witness_role(role: str) -> bool:
    return str(role) in SENIOR_WITNESS_ROLES


def workspace_modes_for_role(role: str) -> list[str]:
    return list(_POLICY.get('workspace_modes', {}).get(str(role), []))
