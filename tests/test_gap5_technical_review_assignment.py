from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_gap5_assignment_migration_and_schema_present():
    mig = ROOT / 'database' / 'migrations' / '030_technical_review_assignments.sql'
    schema = ROOT / 'database' / 'postgres_schema.sql'
    assert mig.exists()
    assert 'create table if not exists public.technical_review_assignments' in mig.read_text().lower()
    assert 'technical_review_assignments' in schema.read_text()


def test_gap5_my_technical_reviews_requires_explicit_assignment():
    src = (ROOT / 'psb_app' / 'pages' / 'role_workspaces.py').read_text()
    section = src.split('def my_technical_reviews_page(actor):', 1)[1].split('\ndef audit_workspace_page', 1)[0]
    assert "db_all('technical_review_assignments')" in section
    assert "assigned_reviewer_id" in section
    assert "reviewer_id' in reviews" not in section
    assert "user_id', 'reviewer_id" not in section


def test_gap5_review_creation_records_assignment():
    src = (ROOT / 'psb_app' / 'pages' / 'quality.py').read_text()
    section = src.split('def technical_reviews_page(actor):', 1)[1].split('\ndef accreditation_readiness_page', 1)[0]
    assert section.count("db_insert('technical_review_assignments'") >= 2
    assert 'assigned_reviewer_id' in section
    assert "assigned_on': now()" in section


def test_gap5_rls_server_only_assignment_table():
    src = (ROOT / 'database' / 'supabase_rls_production.sql').read_text().lower()
    assert 'alter table public.technical_review_assignments enable row level security' in src
    assert 'revoke all on table public.technical_review_assignments from anon, authenticated' in src
    assert 'using (false)' in src[src.find('psb_server_only_technical_review_assignments'):]
