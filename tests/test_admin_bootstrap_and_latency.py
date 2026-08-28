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
    assert "Confirm new password" in section
