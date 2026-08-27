from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_management_review_child_action_register():
    s=read('database/postgres_schema.sql'); m=read('database/migrations/031_management_review_actions.sql'); w=read('psb_app/pages/role_workspaces.py')
    assert 'qms_management_review_actions' in s and 'qms_management_review_actions' in m and 'Action Register' in w and 'Add Governance Action' in w

def test_management_review_action_audit():
    w=read('psb_app/pages/role_workspaces.py')
    assert 'Management Review Action Created' in w and 'Management Review Action Updated' in w

def test_my_performance_is_self_scoped():
    w=read('psb_app/pages/role_workspaces.py')
    assert "db_where('users', 'user_id = :uid'" in w and 'self-scoped' in w and 'Organization-wide KPI data is not exposed' not in w

def test_gap9_10_rls_action_table():
    r=read('database/supabase_rls_production.sql')
    assert 'alter table public.qms_management_review_actions enable row level security;' in r
    assert 'revoke all on table public.qms_management_review_actions from anon, authenticated;' in r
