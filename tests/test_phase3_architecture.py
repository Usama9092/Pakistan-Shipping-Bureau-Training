from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def _all_py():
    return '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in ROOT.rglob('*.py') if '__pycache__' not in p.parts)

def test_phase3_core_modules_exist():
    for name in ['repository.py','auth_provider.py','security.py','module_registry.py']:
        assert (ROOT/'core'/name).exists(), name

def test_auth_user_mapping_present():
    text=_all_py(); schema=(ROOT/'database'/'postgres_schema.sql').read_text()
    assert 'auth_user_id' in text and 'auth_user_id' in schema

def test_supabase_auth_provider_present():
    text=_all_py()
    assert 'SupabaseAuthProvider' in text and 'AUTH_MODE' in text

def test_force_password_change_is_preserved_after_rehash():
    text=_all_py()
    assert 'original_force = str(user.get(\'force_password_change\', \'No\')) == \'Yes\'' in text
    assert 'force_password_change' in text

def test_safe_repository_boundary():
    source=(ROOT/'core'/'repository.py').read_text()
    assert 'IDENT_RE' in source and 'Unsafe SQL identifier' in source

def test_schema_contract_has_auth_identity():
    schema=(ROOT/'database'/'postgres_schema.sql').read_text()
    assert 'auth_user_id' in schema

def test_db_backed_sessions():
    text=_all_py(); schema=(ROOT/'database'/'postgres_schema.sql').read_text()
    assert 'auth_sessions' in text and 'token_hash' in text and 'auth_sessions' in schema

def test_auth_sessions_are_server_only_in_rls_template():
    rls=(ROOT/'database'/'supabase_rls_template.sql').read_text()
    assert 'auth_sessions_server_only' in rls
