from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_supplied_psb_logo_is_upscaled_for_crisp_rendering():
    im = Image.open(ROOT / 'assets' / 'psb-logo.png')
    assert im.width >= 800 and im.height >= 1000


def test_psb_brand_palette_is_applied_to_global_theme():
    ui = read('psb_app/pages/auth_ui.py')
    assert '--psb-ink:#010819' in ui
    assert '--psb-green:#095b25' in ui
    assert '--psb-bg:#f4f7f6' in ui


def test_task_navigation_has_explicit_active_state_and_no_section_selectbox():
    ui = read('psb_app/pages/auth_ui.py')
    sidebar = ui.split('def sidebar(actor):', 1)[1].split('def dashboard_page(actor):', 1)[0]
    assert 'psb-nav-active' in sidebar
    assert 'st.sidebar.selectbox' not in sidebar


def test_accessibility_motion_and_focus_contracts_are_present():
    ui = read('psb_app/pages/auth_ui.py')
    assert 'prefers-reduced-motion: reduce' in ui
    assert ':focus-visible' in ui


def test_current_product_name_is_used_on_login():
    ui = read('psb_app/pages/auth_ui.py')
    assert 'HRD&amp;M Portal' in ui
    assert 'Pakistan Shipping Bureau' in ui
    assert 'Classification Society HRDM Platform' not in ui
