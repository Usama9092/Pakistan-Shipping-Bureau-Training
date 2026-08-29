from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_admin_role_has_direct_administration_entry():
    source = (ROOT / 'psb_app/services/admin_service.py').read_text(encoding='utf-8')
    assert "{'admin', 'administrator'}" in source
    assert "role not in" in source


def test_bootstrap_admin_requires_first_login_password_change():
    source = (ROOT / 'psb_app/services/database_service.py').read_text(encoding='utf-8')
    migration = (ROOT / 'database/migrations/047_initial_admin_first_login.sql').read_text(encoding='utf-8')
    assert "'force_password_change': 'Yes'" in source
    assert "force_password_change = 'Yes'" in migration
    assert "admin@psbureau.org" in migration


def test_remote_database_pre_ping_is_opt_in():
    source = (ROOT / 'core/database_gateway.py').read_text(encoding='utf-8')
    assert "DB_POOL_PRE_PING" in source
    assert "'false'" in source


def test_forced_change_reuses_the_authenticated_login_session():
    source = (ROOT / 'psb_app/pages/auth_ui.py').read_text(encoding='utf-8')
    section = source.split('def password_change_page', 1)[1].split('def sidebar', 1)[0]
    assert "Current / temporary password" not in section
    assert "st.session_state.get('logged_in')" in section
    assert "row.empty" not in section
    assert "actor_get(st.session_state.get('user'" not in section
    assert "Confirm new password" in section
    assert "system_write('authenticated_self_password_change')" in section


def test_login_security_writes_are_trusted_internal_mutations():
    runtime = (ROOT / 'psb_app/legacy_runtime.py').read_text(encoding='utf-8')
    auth = (ROOT / 'psb_app/pages/auth_ui.py').read_text(encoding='utf-8')
    assert "'login_security_state'" in runtime.split('_SERVER_INTERNAL_TABLES', 1)[1].split('}', 1)[0]
    assert "system_write('login_security_failure')" in auth
    assert "system_write('login_security_clear')" in auth


def test_explicit_system_write_bypasses_end_user_module_permissions():
    runtime = (ROOT / 'psb_app/legacy_runtime.py').read_text(encoding='utf-8')
    section = runtime.split('def _mutation_guard', 1)[1].split('def db_insert', 1)[0]
    assert section.index('if is_system_write():') < section.index("actor = st.session_state.get('user')")

