from __future__ import annotations
import json
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "config" / "role_scope_classes.json"
try:
    ROLE_CLASSES = json.loads(_PATH.read_text(encoding="utf-8"))
except Exception:
    ROLE_CLASSES = {}

ORG_ROLES = set(ROLE_CLASSES.get("organization", []))
SELF_ROLES = set(ROLE_CLASSES.get("self", []))
ASSIGNED_ROLES = set(ROLE_CLASSES.get("assigned", []))
CASE_ROLES = set(ROLE_CLASSES.get("case", []))
DEPARTMENT_ROLES = set(ROLE_CLASSES.get("department", []))

def role_class(role: str) -> str:
    r=str(role or "")
    for name, roles in ROLE_CLASSES.items():
        if r in roles:
            return name
    return "unknown"
