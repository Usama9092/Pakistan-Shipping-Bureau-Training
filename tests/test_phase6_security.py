from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_postgres_schema_is_migration_owned():
    files=[ROOT/'psb_app/common.py',ROOT/'psb_app/legacy_runtime.py',ROOT/'psb_app/services/database_service.py']
    source='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in files)
    assert 'is_postgres' in source
    assert 'postgres_schema_mode=migrations_only' in source
