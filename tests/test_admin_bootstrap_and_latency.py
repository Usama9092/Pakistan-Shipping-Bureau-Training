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


def test_captcha_answer_is_derived_from_the_rendered_question():
    auth = (ROOT / 'psb_app/pages/auth_ui.py').read_text(encoding='utf-8')
    section = auth.split('def login_page', 1)[1].split('def require_login', 1)[0]
    assert "captcha_expected = str(sum(" in section
    assert "captcha.strip() != captcha_expected" in section


def test_master_seed_runs_when_an_admin_already_exists_and_batches_permissions():
    service = (ROOT / 'psb_app/services/database_service.py').read_text(encoding='utf-8')
    section = service.split('def seed_demo', 1)[1]
    assert "if not db_all('users').empty:\n        return" not in section
    assert "db_insert_many('permissions', missing_permissions)" in section
    assert "db_insert_many('system_settings'" in section


def test_repository_supports_single_transaction_bulk_insert():
    repository = (ROOT / 'core/repository.py').read_text(encoding='utf-8')
    assert 'def insert_many(' in repository
    assert 'self.exec_sql(' in repository.split('def insert_many', 1)[1].split('def update', 1)[0]

