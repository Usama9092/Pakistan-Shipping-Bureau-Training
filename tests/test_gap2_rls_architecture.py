from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_production_rls_is_server_mediated_and_fail_closed():
    sql = (ROOT / 'database' / 'supabase_rls_production.sql').read_text().lower()
    # The production contract should not contain authenticated SELECT grants/policies;
    # business scope is enforced server-side by the application authorization layer.
    assert not re.search(r'create policy\s+\S+\s+on\s+public\.\S+\s+for\s+select\s+to\s+authenticated', sql)
    assert 'revoke all on table public.users from anon, authenticated;' in sql
    assert 'alter table public.users enable row level security;' in sql


def test_scope_model_is_explicit():
    policy = (ROOT / 'config' / 'role_scope_policy.json').read_text()
    assert all(x in policy for x in ['Trainer', 'Management', 'Surveyor'])
    access = (ROOT / 'core' / 'access_policy.py').read_text()
    assert 'scope_allows' in access and 'record_scope_allowed' in access
    assert 'scope_allows' in access
    assert 'ROLE_MODULE_SCOPE_DEFAULTS' in access
