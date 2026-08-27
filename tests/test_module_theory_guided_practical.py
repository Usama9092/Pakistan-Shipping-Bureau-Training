from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_module_theory_guided_practical_schema_and_security():
    schema=read('database/postgres_schema.sql').lower(); rls=read('database/supabase_rls_production.sql').lower()
    tables=['qualification_module_training','training_resources','training_live_sessions','training_assessment_configs','training_assessment_sessions','guided_practical_training','module_practical_gates','independent_practical_records']
    for t in tables:
        assert f'create table if not exists {t}' in schema
        assert f'alter table public.{t} enable row level security;' in rls
        assert f'revoke all on table public.{t} from anon, authenticated;' in rls

def test_module_curriculum_supports_requested_learning_flow():
    q=read('psb_app/pages/qualification.py')
    for text in ['Theoretical Training inside Modules','Downloadable learning material','Video / Rules / Other links','Live / Zoom session','Timed MCQ Test Builder','Minimum guided Practical/Witness trainings','Ready for Independent Practical','Submit Guided Practical Report']:
        assert text in q
    assert "minimum_guided_practical':2" in q

def test_timed_mcq_uses_server_session_and_expiry():
    t=read('psb_app/pages/training.py')
    for text in ['Start Timed Assessment','training_assessment_sessions','expires_at','Time Remaining','server-side timer','automatically submitted']:
        assert text in t
