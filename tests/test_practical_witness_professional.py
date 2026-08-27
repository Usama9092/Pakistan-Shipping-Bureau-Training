from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT/rel).read_text(encoding='utf-8')


def test_practical_page_is_real_and_routed():
    src=read('psb_app/pages/practical_witness.py')
    main=read('psb_app/main.py')
    assert 'def practical_page' in src
    assert 'def my_witness_assessments_page' in src
    assert 'def practical_governance_page' in src
    assert 'from psb_app.pages.practical_witness import' in main
    assert '"Practical / Witness": practical_page' in main
    assert '"My Witness Assessments": my_witness_assessments_page' in main


def test_professional_tables_are_canonical_and_rls_protected():
    schema=read('database/postgres_schema.sql').lower()
    rls=read('database/supabase_rls_production.sql').lower()
    migration=read('database/migrations/035_practical_witness_professional.sql').lower()
    for table in ['practical_requirement_templates','practical_activities','practical_assessments','practical_evidence_links']:
        assert f'create table if not exists {table}' in schema
        assert f'create table if not exists {table}' in migration
        assert f'alter table public.{table} enable row level security' in rls
        assert f'revoke all on table public.{table} from anon, authenticated' in rls


def test_role_specific_workspaces_exist():
    nav=read('core/navigation.py')
    assert 'My Assessments' in nav
    assert 'Department Qualification' in nav
    assert 'My Qualification' in nav


def test_witness_eligibility_and_assessment_controls_exist():
    src=read('psb_app/pages/practical_witness.py')
    for phrase in [
        'A person cannot witness their own assessment.',
        'No active authorization exists for the required scope.',
        'An active authorization restriction blocks witness eligibility.',
        'Assessment Outcome',
        'Competent / Requirement Satisfied',
        'More Practice Required',
        'Assessment Invalid / Could Not Observe',
        'I directly observed sufficient elements of this activity.',
        'I am authorized within the relevant technical scope.',
        'I assessed the person objectively against the defined criteria.',
        'I have disclosed any relevant conflict of interest.',
    ]:
        assert phrase in src


def test_evidence_links_do_not_duplicate_documents():
    src=read('psb_app/pages/practical_witness.py')
    assert "db_all('files')" in src
    assert "db_insert('practical_evidence_links'" in src
    assert 'without duplicating the source document' in src
    assert "upload_file(" not in src


def test_witness_feedback_flows_to_tutor_and_competency():
    src=read('psb_app/pages/practical_witness.py')
    readiness=read('psb_app/services/training_service.py')
    assert 'Add to Development Plan' in src
    assert 'Witness Assessment' in src
    assert "db_all('practical_assessments')" in readiness
    assert 'Practical requirement incomplete:' in readiness


def test_role_scope_policy_supports_own_and_assigned_witness_work():
    policy=json.loads(read('config/role_scope_policy.json'))
    for role in ['Surveyor','Industrial Surveyor','Plan Appraiser']:
        scopes=set(policy[role]['Practical / Witness'])
        assert {'Own','Assigned'} <= scopes


def test_practical_tables_use_central_mutation_boundary():
    policy=read('core/access_policy.py')
    for table in ['practical_requirement_templates','practical_activities','practical_assessments','practical_evidence_links']:
        assert f"'{table}':'Practical / Witness'" in policy
    auth=read('core/authorization.py')
    assert "module == 'Practical / Witness'" in auth


def test_vertical_audit_is_not_conflated_with_initial_practical_assessment():
    src=read('psb_app/pages/practical_witness.py').lower()
    # The practical workflow may mention authorization readiness but it must not masquerade
    # as the annual vertical-audit record type.
    assert 'vertical audit workspace' not in src
