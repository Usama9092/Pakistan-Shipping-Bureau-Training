from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_runtime_does_not_eager_import_extracted_services():
    src = (ROOT / 'psb_app' / 'legacy_runtime.py').read_text(encoding='utf-8')
    # The runtime is the dependency foundation for extracted services. Eagerly
    # importing those services here recreates the circular import that prevents
    # app.py from loading.
    assert 'from psb_app.services.auth_service import' not in src
    assert 'from psb_app.services.policy_service import' not in src
    assert 'from psb_app.services.training_service import' not in src
    assert 'from psb_app.services.certificate_service import' not in src
    assert 'from psb_app.services.governance_service import' not in src
    assert 'from psb_app.services.admin_service import' not in src
    assert 'from psb_app.services.ui_helpers import' not in src
    assert '_lazy_service_call' in src


def test_main_imports_shared_runtime_symbols_only_from_common():
    src = (ROOT / 'psb_app' / 'main.py').read_text(encoding='utf-8')
    # Page modules expose page functions. Shared symbols belong to common and
    # must not be re-imported from pages where they may not exist.
    page_import_region = src.split('from core.view_context', 1)[0]
    for symbol in ('APP_TITLE,', 'LOGO_PATH,', 'actor_get,', '    st,', '    uuid,'):
        # These symbols are allowed in the common import block only.
        tail = page_import_region.split('from psb_app.pages.auth_ui', 1)[-1]
        assert symbol not in tail


def test_shared_table_renderer_lives_in_common_facade():
    common = (ROOT / 'psb_app' / 'common.py').read_text(encoding='utf-8')
    practical = (ROOT / 'psb_app' / 'pages' / 'practical_witness.py').read_text(encoding='utf-8')
    assert 'def table(df, max_rows: int = 300)' in common
    assert '    table,' in practical
