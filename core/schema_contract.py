from __future__ import annotations
import re
from pathlib import Path

TABLE_REF_RE = re.compile(r'db_(?:all|where|insert|update|delete)\(\s*["\']([A-Za-z0-9_]+)', re.I)
INFRA_TABLES = {"schema_migrations", "deprecated_table_registry", "qr_verification_events", "audit_event_requirements"}
TABLE_DEF_RE = re.compile(r'(?:create\s+table\s+if\s+not\s+exists|create\s+table)\s+([A-Za-z0-9_]+)', re.I)

def schema_tables(schema_path: str | Path) -> set[str]:
    text = Path(schema_path).read_text(encoding="utf-8", errors="ignore")
    return {m.group(1).lower() for m in TABLE_DEF_RE.finditer(text)}

def referenced_tables(app_path: str | Path) -> set[str]:
    p = Path(app_path)
    if p.is_dir():
        files=[]
        for base in (p/"psb_app", p/"core"):
            if base.exists():
                files.extend(x for x in base.rglob("*.py") if "__pycache__" not in x.parts)
        texts=[x.read_text(encoding="utf-8", errors="ignore") for x in files]
        text="\n".join(texts)
    else:
        text=p.read_text(encoding="utf-8", errors="ignore")
    return {m.group(1).lower() for m in TABLE_REF_RE.finditer(text)}

def contract_report(app_path: str | Path, schema_path: str | Path) -> dict:
    refs = referenced_tables(app_path)
    defs = schema_tables(schema_path)
    missing = sorted(refs - defs)
    unused = sorted((defs - refs) - INFRA_TABLES)
    return {
        "referenced_count": len(refs),
        "schema_count": len(defs),
        "missing_tables": missing,
        "unused_schema_tables": unused,
        "contract_ok": not missing,
    }
