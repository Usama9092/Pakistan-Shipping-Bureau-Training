from __future__ import annotations
from pathlib import Path
import hashlib
from sqlalchemy import create_engine, text

def run_pending_migrations(database_url: str, root: Path) -> dict:
    if not database_url: return {"applied": [], "errors": ["DATABASE_URL missing"]}
    if database_url.startswith("postgresql://"): database_url=database_url.replace("postgresql://","postgresql+psycopg2://",1)
    if not database_url.startswith(("postgresql://","postgresql+psycopg2://","postgres://")):
        return {"applied": [], "errors": [], "skipped": "non-postgres"}
    engine=create_engine(database_url, pool_pre_ping=True)
    mdir=root/"database"/"migrations"
    applied=[]
    errors=[]
    try:
        with engine.begin() as conn:
            conn.execute(text("create table if not exists schema_migrations (version text primary key, checksum text not null, applied_on text not null)"))
        with engine.connect() as conn:
            current={str(r[0]):str(r[1]) for r in conn.execute(text("select version, checksum from schema_migrations"))}
    except Exception as exc:
        return {"applied": applied, "errors": [str(exc)]}
    for path in sorted(mdir.glob("*.sql")):
        version=path.name.split("_",1)[0]
        checksum=hashlib.sha256(path.read_bytes()).hexdigest()
        if version in current:
            if current[version] != checksum:
                # v035 existed in two released sibling branches. Accept only the
                # two known legacy checksums; v036 is an idempotent bridge that
                # converges either lineage onto the unified schema.
                legacy_035 = {
                    "b7c7346e9e6e69a08dbc854f9723f764ebf67b643de626278412ccb40885b2ca",
                    "7b7a93f9c6835fe8be88740c4a057686d128676271e21590a586354dd72c314f",
                }
                if not (version == "035" and current[version] in legacy_035):
                    errors.append(f"Checksum mismatch: {path.name}")
            continue
        try:
            # Each migration has its own transaction. A legacy-schema conflict in
            # one migration must not roll back every independent successful upgrade.
            with engine.begin() as conn:
                conn.execute(text(path.read_text(encoding="utf-8")))
                conn.execute(text("insert into schema_migrations(version,checksum,applied_on) values (:v,:c,CURRENT_TIMESTAMP)"),{"v":version,"c":checksum})
            applied.append(path.name)
            current[version]=checksum
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    return {"applied":applied,"errors":errors}
