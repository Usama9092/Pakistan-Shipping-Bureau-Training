from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_executive_dashboard_is_management_only():
    s=read('psb_app/pages/executive.py')
    assert "actor_get(actor, 'role', '') != 'Management'" in s
    assert 'Executive Dashboard is reserved for the Management role.' in s

def test_executive_dashboard_has_decision_board_and_risk_pulse():
    s=read('psb_app/pages/executive.py')
    assert 'Executive Risk Pulse' in s
    assert 'Decision Board' in s
    assert 'Workforce & Qualification Risk' in s
    assert 'Quality & Client Signal' in s
    assert 'Management Review Actions' in s

def test_executive_dashboard_uses_authoritative_records():
    s=read('psb_app/pages/executive.py')
    for table_name in ['users','training_records','competency_ncrs','job_requests','authorization_requests','client_feedback','kpi_snapshots','qms_management_reviews']:
        assert table_name in s
