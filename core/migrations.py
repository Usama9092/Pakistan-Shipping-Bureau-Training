from __future__ import annotations
from pathlib import Path
import hashlib
from sqlalchemy import create_engine, text

# These migrations belong to an older baseline/role-workspace lineage. Some assume
# tables/columns that were never part of the production branch and therefore cannot
# be replayed safely after the later consolidated migrations have already upgraded
# the database. On a demonstrably modern database (v040+), treat them as superseded
# rather than retrying them on every Streamlit session. This does not mark them as
# applied and does not hide errors from current/new migrations.
SUPERSEDED_ON_MODERN_SCHEMA = {
    "017",  # old monolithic canonical baseline; replaced by later converged schema
    "023",  # old all-table RLS contract against the obsolete baseline table set
    "025",  # comment-only server-control placeholder
    "027",  # obsolete technical-review workspace branch
    "029",  # obsolete technical-review workspace branch
    "030",  # obsolete technical-review assignment branch
    "033",  # obsolete technical-discipline branch
    "034",  # comment-only role-scope placeholder
}


def run_pending_migrations(database_url: str, root: Path) -> dict:
    if not database_url:
        return {"applied": [], "errors": ["DATABASE_URL missing"]}
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if not database_url.startswith(("postgresql://", "postgresql+psycopg2://", "postgres://")):
        return {"applied": [], "errors": [], "skipped": "non-postgres"}

    engine = create_engine(database_url, pool_pre_ping=True)
    mdir = root / "database" / "migrations"
    applied: list[str] = []
    errors: list[str] = []
    superseded: list[str] = []
    try:
        with engine.begin() as conn:
            conn.execute(text("create table if not exists schema_migrations (version text primary key, checksum text not null, applied_on text not null)"))
        with engine.connect() as conn:
            current = {str(r[0]): str(r[1]) for r in conn.execute(text("select version, checksum from schema_migrations"))}
    except Exception as exc:
        return {"applied": applied, "errors": [str(exc)]}

    # A database at/after v040 has already crossed the consolidated production
    # baseline. Failed legacy branch migrations before that point must not be
    # replayed into the newer schema. Current and future migrations still run.
    numeric_versions = [int(v) for v in current if v.isdigit() and len(v) <= 3]
    modern_schema = bool(numeric_versions and max(numeric_versions) >= 40)

    for path in sorted(mdir.glob("*.sql")):
        version = path.name.split("_", 1)[0]
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()

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

        if modern_schema and version in SUPERSEDED_ON_MODERN_SCHEMA:
            superseded.append(path.name)
            continue

        try:
            # Each migration has its own transaction. A conflict in one migration
            # must not roll back every independent successful upgrade.
            with engine.begin() as conn:
                sql = path.read_text(encoding="utf-8").strip()
                # Comment-only placeholders are valid no-op migrations.
                if sql and any(line.strip() and not line.lstrip().startswith("--") for line in sql.splitlines()):
                    conn.execute(text(sql))
                conn.execute(
                    text("insert into schema_migrations(version,checksum,applied_on) values (:v,:c,CURRENT_TIMESTAMP)"),
                    {"v": version, "c": checksum},
                )
            applied.append(path.name)
            current[version] = checksum
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")

    return {"applied": applied, "errors": errors, "superseded": superseded}
