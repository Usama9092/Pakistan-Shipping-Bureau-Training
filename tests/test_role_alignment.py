from core.navigation import ROLE_NAVIGATION

def test_all_current_roles_have_explicit_navigation():
    roles=['GM','Admin','Trainer','Department Manager','Surveyor','NSC Surveyor','In-Service Surveyor','Plan Appraiser','QMS Auditor','Industrial Surveyor','Rule Development Rep','QMR','Management','Trainee','On Probation']
    assert set(roles)==set(ROLE_NAVIGATION)
    for removed in ['Principal Surveyor','Chief Plan Appraiser','Technical Manager','Lead Auditor','CRB Member','Job Coordinator']:
        assert removed not in ROLE_NAVIGATION

def test_department_manager_is_task_oriented():
    labels={p for _,items,_ in ROLE_NAVIGATION['Department Manager'] for p in items}
    assert {'Department Qualification','My Assessments','Authorization Cases'} <= labels

def test_qms_auditor_is_single_auditor_role():
    assert 'QMS Auditor' in ROLE_NAVIGATION and 'Lead Auditor' not in ROLE_NAVIGATION
