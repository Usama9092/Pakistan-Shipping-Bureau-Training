from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE_WS = ROOT / 'psb_app' / 'pages' / 'role_workspaces.py'
MAIN = ROOT / 'psb_app' / 'main.py'
NAV = ROOT / 'core' / 'navigation.py'


def test_audit_workspace_exists_and_is_integrated():
    text = ROLE_WS.read_text()
    assert 'def audit_workspace_page(actor, audit_id=None):' in text
    assert "tabs = st.tabs(['Scope & Plan','Evidence','Findings / NCR','Corrective Actions','Verification & Closure'])" in text
    assert "authorization_evidence_links" not in text or 'qms_evidence_reviews' in text
    main = MAIN.read_text()
    assert '"Audit Workspace": audit_workspace_page' in main
    nav = NAV.read_text()
    assert '"Audit Workspace"' in nav


def test_audit_workspace_has_no_duplicate_capa_store():
    text = ROLE_WS.read_text()
    assert 'db_insert(\'audit_' not in text
    assert 'Corrective actions are created and maintained in the enterprise NCR/CAPA workflow.' in text


def test_my_audits_opens_workspace_directly():
    text = ROLE_WS.read_text()
    assert "audit_workspace_page(actor, selected)" in text
    assert "Open QMS Audit Workspace" not in text
