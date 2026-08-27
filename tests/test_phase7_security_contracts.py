from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]

def _runtime_text():
    return (ROOT/'psb_app/common.py').read_text() + (ROOT/'psb_app/legacy_runtime.py').read_text()

def test_all_schema_tables_are_rls_enabled_and_client_denied():
    schema=(ROOT/'database/postgres_schema.sql').read_text().lower()
    sql=(ROOT/'database/supabase_rls_production.sql').read_text().lower()
    tables=re.findall(r'create table if not exists\s+([a-z0-9_]+)', schema)
    for table in set(tables):
        assert f'alter table public.{table} enable row level security;' in sql
        assert f'revoke all on table public.{table} from anon, authenticated;' in sql

def test_record_auth_api_is_single_boundary():
    auth=(ROOT/'core/authorization.py').read_text()
    common=_runtime_text()
    assert 'def authorize_record' in auth
    assert '_mutation_guard' in common and 'authorize_action' in (common + auth)
    assert 'TABLE_MUTATION_MODULES.get(table)' in common

def test_system_tables_require_internal_context():
    common=_runtime_text()
    assert 'is_system_write()' in common and '_SERVER_INTERNAL_TABLES' in common
    assert 'MUTATION_GUARD_EXEMPT' not in common

def test_crb_case_scope_exists():
    migration=(ROOT/'database/migrations/038_qualification_path_levels_modules_crb_board.sql').read_text()
    workspace=(ROOT/'psb_app/pages/role_workspaces.py').read_text()
    assert 'crb_case_board_assignments' in migration
    assert 'CRB is a case-based board function' in workspace
    assert 'CRB Member' not in (ROOT/'core/navigation.py').read_text()

def test_qr_telemetry_runtime():
    src=(ROOT/'psb_app/pages/public_verify.py').read_text()
    assert '_log_qr_event' in src and 'RateLimited' in src

def test_phase7_role_scope_map_is_explicit():
    from core.access_policy import ROLE_MODULE_SCOPE_DEFAULTS, ROLE_ALLOWED_SCOPES
    for r in ['Trainer','Surveyor','Plan Appraiser','Management','Rule Development Rep','Trainee','QMS Auditor']:
        assert r in ROLE_MODULE_SCOPE_DEFAULTS or r in ROLE_ALLOWED_SCOPES

def test_common_is_facade_not_monolith():
    common=(ROOT/'psb_app/common.py').read_text()
    assert len(common.splitlines()) < 50
    assert 'legacy_runtime' in common and 'import *' not in common

def test_universal_authorize_action_boundary():
    auth=(ROOT/'core/authorization.py').read_text()
    runtime=(ROOT/'psb_app/legacy_runtime.py').read_text()
    assert 'def authorize_action(' in auth
    assert 'authorize_action(actor, module, action' in runtime

def test_no_page_level_write_sql_bypass():
    text='\n'.join(p.read_text(errors='ignore') for p in (ROOT/'psb_app/pages').glob('*.py'))
    assert not re.search(r'exec_sql\(\s*["\']\s*(?:insert|update|delete)\b', text, re.I)
