from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def test_all_schema_tables_are_explicitly_server_only_to_browser():
    schema=(ROOT/'database/postgres_schema.sql').read_text().lower()
    rls=(ROOT/'database/supabase_rls_production.sql').read_text().lower()
    import re
    tables=set(re.findall(r'create table if not exists\s+(?:public\.)?([a-z0-9_]+)', schema))
    enabled=set(re.findall(r'alter table\s+public\.([a-z0-9_]+)\s+enable row level security', rls))
    revoked=set(re.findall(r'revoke all on table public\.([a-z0-9_]+) from anon, authenticated', rls))
    assert tables <= enabled
    assert tables <= revoked

def test_mutation_boundary_is_single_entry():
    auth=(ROOT/'core/authorization.py').read_text()
    runtime=(ROOT/'psb_app/legacy_runtime.py').read_text()
    assert 'def authorize_action(' in auth
    assert '_mutation_guard(table' in runtime
    assert 'authorize_action(actor, module, action' in runtime

def test_no_page_level_schema_creation():
    pages='\n'.join(p.read_text(errors='ignore') for p in (ROOT/'psb_app/pages').glob('*.py'))
    assert not re.search(r'create\s+table\s+if\s+not\s+exists', pages, re.I)

def test_common_is_compatibility_facade_only():
    common=(ROOT/'psb_app/common.py').read_text()
    assert len(common.splitlines()) < 50
    assert 'legacy_runtime' in common

def test_db_sessions_are_authoritative():
    runtime=(ROOT/'psb_app/legacy_runtime.py').read_text()
    assert 'ACTIVE_SESSIONS' not in runtime
    assert 'auth_sessions' in runtime
