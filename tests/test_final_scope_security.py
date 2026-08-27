import json
from pathlib import Path
from core.access_policy import ROLE_MODULE_SCOPE_DEFAULTS
from core.navigation import ROLE_NAVIGATION
ROOT=Path(__file__).resolve().parents[1]

def test_removed_account_roles_do_not_exist():
    for role in ['CRB Member','Job Coordinator','Lead Auditor']:
        assert role not in ROLE_NAVIGATION

def test_crb_is_case_assignment_not_system_role():
    migration=(ROOT/'database/migrations/038_qualification_path_levels_modules_crb_board.sql').read_text()
    assert 'crb_case_board_assignments' in migration
    assert 'system_role text not null' in migration
    assert 'board_role text not null' in migration
    assert "role in ('Lead Auditor','CRB Member','Job Coordinator')" in migration

def test_trainer_and_tutor_are_assignment_only_by_default():
    assert ROLE_MODULE_SCOPE_DEFAULTS['Trainer']['Training'] == ['Assigned']
    assert ROLE_MODULE_SCOPE_DEFAULTS['Trainer']['Competency'] == ['Assigned']
    assert ROLE_MODULE_SCOPE_DEFAULTS['Trainer']['Development Plans'] == ['Assigned']
    assert 'Department' not in ROLE_MODULE_SCOPE_DEFAULTS['Trainer']['Training']

def test_role_policy_is_external_configured():
    data=json.loads((ROOT/'config/role_scope_policy.json').read_text())
    for role in ['Trainer','Trainer','Surveyor','Plan Appraiser','Rule Development Rep','Trainee','Management','QMS Auditor']:
        assert role in data and isinstance(data[role],dict)
