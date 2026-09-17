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
    init_section = service.split('def init_db', 1)[1].split('def ensure_indexes', 1)[0]
    assert 'seed_demo()' in init_section
    assert "if db_all('users').empty:\n        seed_demo()" not in init_section


def test_repository_supports_single_transaction_bulk_insert():
    repository = (ROOT / 'core/repository.py').read_text(encoding='utf-8')
    assert 'def insert_many(' in repository
    assert 'self.exec_sql(' in repository.split('def insert_many', 1)[1].split('def update', 1)[0]


def test_role_permission_baseline_avoids_per_grant_database_queries():
    runtime = (ROOT / 'psb_app/legacy_runtime.py').read_text(encoding='utf-8')
    section = runtime.split('def _ensure_role_permission_baseline', 1)[1].split('# ---------------------------------------------------------------------------', 1)[0]
    assert "existing_all = db_all('role_permissions')" in section
    assert "db_where('role_permissions'" not in section
    assert "db_insert_many('role_permissions', missing_rows)" in section


def test_scoped_database_reads_are_not_shared_across_streamlit_sessions():
    runtime = (ROOT / 'psb_app/legacy_runtime.py').read_text(encoding='utf-8')
    assert "@st.cache_data(ttl=20, show_spinner=False)\ndef db_all_unscoped" in runtime
    assert "@st.cache_data(ttl=20, show_spinner=False)\ndef db_where_unscoped" in runtime
    assert "@st.cache_data(ttl=20, show_spinner=False)\ndef db_all(" not in runtime
    assert "@st.cache_data(ttl=20, show_spinner=False)\ndef db_where(" not in runtime
    clear_section = runtime.split('def clear_db_cache', 1)[1].split('REPOSITORY =', 1)[0]
    assert 'db_all_unscoped.clear()' in clear_section
    assert 'db_where_unscoped.clear()' in clear_section


def test_qualification_baseline_repair_is_idempotent_and_scope_limited():
    migration = (ROOT / 'database/migrations/056_trainer_qualification_baseline_repair.sql').read_text(encoding='utf-8').lower()
    assert "('qp-nsc'" in migration and "('qp-is'" in migration
    assert "('qp-ind'" in migration and "('qp-pa'" in migration
    assert "('qpv-nsc-1'" in migration and "'1.0', 'active'" in migration
    assert "p.module_name = 'training'" in migration
    assert "p.scope = 'assigned'" in migration
    assert "rp.role_name = 'trainer'" in migration
    assert "on conflict (path_id, version_no) do update" in migration
    assert 'grant ' not in migration


def test_industrial_curriculum_is_complete_and_source_gated():
    migration = (ROOT / 'database/migrations/057_industrial_survey_curriculum.sql').read_text(encoding='utf-8').lower()
    for module_code in ('ind-qa', 'ind-mat-weld', 'ind-nde-test', 'ind-qa-ojt', 'ind-mat-ojt', 'ind-nde-ojt', 'ind-fat-ojt'):
        assert module_code in migration
    assert migration.count("'guided practical'") >= 2
    assert migration.count("'independent practical'") >= 2
    assert "'draft',10" in migration
    assert "meeting_link" in migration
    assert 'grant ' not in migration


def test_draft_courses_without_sources_skip_per_course_queries():
    source = (ROOT / 'psb_app/services/auto_publish_curriculum.py').read_text(encoding='utf-8')
    loop = source.split('for _, tr_row in drafts.iterrows():', 1)[1]
    skip = loop.index('if learning_items == 0 and not source:')
    question_query = loop.index("select question_id,question from question_bank")
    assert skip < question_query


def test_administration_master_repair_migration_is_additive():
    migration = (ROOT / 'database/migrations/048_administration_master_repair.sql').read_text(encoding='utf-8').lower()
    for table in ['roles', 'permissions', 'role_permissions', 'user_permission_overrides', 'system_settings']:
        assert f'create table if not exists {table}' in migration


def test_production_dockerfile_has_non_root_health_checked_runtime():
    dockerfile = (ROOT / 'Dockerfile').read_text(encoding='utf-8')
    assert 'FROM python:3.12-slim' in dockerfile
    assert 'USER psb' in dockerfile
    assert 'HEALTHCHECK' in dockerfile
    assert '/_stcore/health' in dockerfile
    assert '--server.address=0.0.0.0' in dockerfile

