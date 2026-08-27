from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_crb_case_readiness_board_exists():
    s=(ROOT/'psb_app/pages/role_workspaces.py').read_text()
    assert "Case Evidence Package" in s
    assert "Required Gates" in s and "Decision Readiness" in s
    assert "authorization_evidence_links" in s

def test_probation_progress_board_has_all_gates():
    s=(ROOT/'psb_app/pages/role_workspaces.py').read_text()
    for token in ['Objectives','Training','Competency','Practical / Witness','Performance','Trainer Assessment','Probation Timeline']:
        assert token in s

def test_probation_progress_is_read_only_for_self():
    s=(ROOT/'psb_app/pages/role_workspaces.py').read_text()
    assert 'read-only personal progress view' in s
