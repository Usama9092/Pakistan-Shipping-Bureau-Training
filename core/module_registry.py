from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    group: str
    owner: str

MODULES = [
    ModuleSpec("dashboard", "Dashboard", "Dashboard", "core"),
    ModuleSpec("people", "People & Development", "People & Development", "people"),
    ModuleSpec("training", "Training & Competency", "Training & Competency", "training"),
    ModuleSpec("authorization", "Authorization", "Authorization", "authorization"),
    ModuleSpec("quality", "Technical & Quality", "Technical & Quality", "quality"),
    ModuleSpec("operations", "Operations", "Operations", "operations"),
    ModuleSpec("administration", "Administration", "Administration", "admin"),
    ModuleSpec("verification", "QR Verify", "Verification", "verification"),
]

def module_keys() -> set[str]:
    return {m.key for m in MODULES}
