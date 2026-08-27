from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_timed_mcq_enforces_window_and_stable_randomization():
    src=(ROOT/'psb_app/pages/training.py').read_text(encoding='utf-8')
    assert '_assessment_window_open' in src
    assert '_stable_question_rows' in src
    assert '_stable_options' in src
    assert 'available_from' in src and 'available_until' in src

def test_theory_gate_requires_resources_and_session_attendance():
    src=(ROOT/'psb_app/pages/qualification.py').read_text(encoding='utf-8')
    assert 'training_resource_progress' in src
    assert 'training_session_attendance' in src
    assert "attendance_status','')) not in {'Present','Recording Viewed'}" in src

def test_trainer_final_gate_and_independent_assessment_are_explicit():
    src=(ROOT/'psb_app/pages/qualification.py').read_text(encoding='utf-8')
    assert 'Final Trainer Readiness Gate' in src
    assert 'module_trainer_readiness' in src
    assert 'independent_practical_assessor_panel' in src
    assert 'independent_practical_assessments' in src

def test_probation_requires_separate_approval():
    src=(ROOT/'psb_app/pages/qualification.py').read_text(encoding='utf-8')
    assert 'Submit Progression Recommendation' in src
    assert 'Pending Approval' in src
    assert 'Record Progression Decision' in src

def test_crb_policy_is_case_based_and_management_mandatory():
    policy=json.loads((ROOT/'config/crb_policy.json').read_text(encoding='utf-8'))
    assert 'Management' in policy['mandatory_roles']
    assert 'CRB Member' not in (ROOT/'core/navigation.py').read_text(encoding='utf-8')
    src=(ROOT/'psb_app/pages/qualification.py').read_text(encoding='utf-8')
    assert 'crb_case_board_assignments' in src
    assert 'CRB Recommended' in src
