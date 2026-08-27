from pathlib import Path
from core.navigation import ROLE_NAVIGATION
ROOT=Path(__file__).resolve().parents[1]

def labels(role):
    return {x for _,items,_ in ROLE_NAVIGATION[role] for x in items}

def read(path): return (ROOT/path).read_text(encoding='utf-8')

def test_trainer_has_single_qualification_workspace_with_library_inside():
    assert labels('Trainer')=={'Qualification Workspace'}
    q=read('psb_app/pages/qualification.py')
    assert "'Knowledge Library'" in q
    assert "knowledge_page(actor)" in q

def test_mcq_generation_is_review_then_publish_to_learners():
    q=read('psb_app/pages/qualification.py')
    assert 'Generate Professional MCQ Draft' in q
    assert 'Save Reviewed Drafts' in q
    assert 'Publish MCQs to Assigned Learners' in q
    assert 'training_mcq_drafts' in q
    svc=read('psb_app/services/training_service.py')
    assert 'PSB_AI_MCQ_ENDPOINT' in svc and 'Controlled local grounded generator' in svc

def test_path_specific_survey_and_plan_practical_requirements():
    q=read('psb_app/pages/qualification.py')
    assert 'qualification_practical_requirements' in q
    assert 'Witness / Observe' in q
    assert 'Work Together / Joint' in q
    assert 'Plan Appraisal' in q
    assert '_specific_practical_requirements_status' in q

def test_authorization_decision_is_post_crb_and_allocates_one_year_digital_certificate():
    q=read('psb_app/pages/qualification.py')
    assert "status = :s',(('s','CRB Recommended')" in q
    assert 'CRB Discussion & Decision' in q
    assert 'Approve Authorization & Allocate Digital Certificate' in q
    a=read('psb_app/pages/authorization.py')
    assert 'add_months(issue_date, 12)' in a
    assert 'Digital Certificate of Authorization Issued' in a

def test_admin_creates_role_credentials_but_trainer_owns_path():
    a=read('psb_app/pages/admin.py')
    assert "selectbox('Role', ROLES)" in a
    assert "text_input('Login ID'" in a
    assert "text_input('Temporary Password'" in a
    assert 'Qualification Path is assigned only by the responsible Trainer' in a
    assert "Qualification Path (Trainer controlled)" in a

def test_training_material_extraction_includes_excel_and_pptx():
    src=read('psb_app/legacy_runtime.py')
    assert "lower.endswith('.pptx')" in src
    assert "lower.endswith(('.xlsx', '.xlsm'))" in src
