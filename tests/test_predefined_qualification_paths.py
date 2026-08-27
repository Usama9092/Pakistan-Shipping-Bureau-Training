from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_predefined_paths_and_removed_roles():
    runtime=read('psb_app/legacy_runtime.py')
    for path in ['NSC Surveyor','In-Service Surveyor','Industrial Surveyor','Plan Appraiser']:
        assert path in runtime
    for role in ['Principal Surveyor','Chief Plan Appraiser','Technical Manager']:
        assert role not in runtime.split('ROLES =',1)[1].split('DEPARTMENTS =',1)[0]
    assert 'Department Manager' in runtime

def test_path_tables_are_rls_protected():
    schema=read('database/postgres_schema.sql').lower(); rls=read('database/supabase_rls_production.sql').lower()
    for table in ['qualification_paths','qualification_path_training','qualification_assignments']:
        assert f'create table if not exists {table}' in schema
        assert f'alter table public.{table} enable row level security;' in rls
        assert f'revoke all on table public.{table} from anon, authenticated;' in rls

def test_trainer_path_page_assigns_training_and_owns_mentoring():
    src=read('psb_app/pages/qualification.py')
    assert 'Assign Qualification Path' in src
    assert 'Tutor / Mentor (optional)' not in src
    assert 'Trainer also owns mentoring and development support' in src or 'Trainer workspace' in src or 'mentoring and development support' in src
    assert '_ensure_path_training_records' in src
    assert 'Add Theoretical Training' in src
    assert 'Minimum guided Practical/Witness trainings' in src
    assert 'Timed MCQ Test Builder' in src

def test_department_manager_is_limited_to_technical_departments():
    src=read('psb_app/pages/qualification.py')
    assert "{'Survey NSC','Survey Inservice','Plan Appraisal'}" in src
