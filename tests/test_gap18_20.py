from pathlib import Path
import json, ast
ROOT=Path(__file__).resolve().parents[1]

def test_gap18_certificate_history_present_and_immutable_posture():
    mig=ROOT/'database/migrations/032_certificate_history.sql'
    schema=ROOT/'database/postgres_schema.sql'
    rls=ROOT/'database/supabase_rls_production.sql'
    assert mig.exists()
    assert 'authorization_certificate_history' in schema.read_text()
    r=rls.read_text()
    assert 'alter table public.authorization_certificate_history enable row level security' in r
    assert 'revoke all on table public.authorization_certificate_history from anon, authenticated' in r

def test_gap19_technical_discipline_policy_and_assignment_field():
    p=ROOT/'config/technical_discipline_policy.json'
    assert p.exists()
    d=json.loads(p.read_text())
    assert 'disciplines' in d and 'roles' in d
    schema=ROOT/'database/postgres_schema.sql'
    assert 'alter table technical_reviews add column if not exists discipline text' in schema.read_text()
    assert 'alter table technical_review_assignments add column if not exists discipline text' in schema.read_text()
    src=(ROOT/'psb_app/pages/role_workspaces.py').read_text()
    assert 'allowed_disciplines' in src

def test_gap20_role_classes_single_source():
    p=ROOT/'config/role_scope_classes.json'
    assert p.exists()
    d=json.loads(p.read_text())
    all_roles=[r for vals in d.values() for r in vals]
    assert len(all_roles)==len(set(all_roles))
    src=(ROOT/'core/access_policy.py').read_text()
    assert 'from core.role_classes import ORG_ROLES, SELF_ROLES, ASSIGNED_ROLES, CASE_ROLES, DEPARTMENT_ROLES' in src
    assert 'ORG_ROLES = {' not in src

def test_gap20_policy_registry_migration_continuous():
    migs=sorted((ROOT/'database/migrations').glob('*.sql'))
    nums=[int(m.name.split('_',1)[0]) for m in migs]
    assert nums==list(range(1,max(nums)+1))
    assert max(nums)>=34
