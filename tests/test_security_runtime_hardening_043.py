from pathlib import Path
import json,re
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_runtime_import_blockers_fixed_in_source():
    src=read('psb_app/legacy_runtime.py')
    assert 'from argon2 import PasswordHasher' in src
    assert 'from supabase import create_client' in src
    assert 'def filter_frame' in read('core/access_policy.py')

def test_local_auth_never_places_bearer_token_in_url_or_browser_cookie():
    ui=read('psb_app/pages/auth_ui.py')
    assert 'experimental_set_query_params(auth_token=token)' not in ui
    assert "psb_auth={token}" not in ui
    assert 'URLSearchParams(window.location.search)' not in ui

def test_private_storage_and_upload_hardening():
    src=read('psb_app/legacy_runtime.py')
    assert "options={'public': False}" in src
    assert 'get_public_url' not in src
    assert 'MAX_UPLOAD_BYTES' in src
    assert '_validate_upload_bytes' in src
    assert '_malware_scan_upload' in src
    assert "'html'" not in re.search(r'ALLOWED_EXTENSIONS\s*=\s*\[(.*?)\]',src,re.S).group(1)
    # the upload rate-limit must be outside a swallow-all try/except
    segment=src[src.index('def upload_file'):src.index('def extract_text')]
    assert "if not RATE_LIMITER.allowed('upload'" in segment
    assert "except Exception:\n        pass" not in segment.split("if not RATE_LIMITER.allowed('upload'",1)[0][-160:]

def test_security_controls_are_enforced_not_cosmetic():
    ui=read('psb_app/pages/auth_ui.py')
    for token in ['_persistent_login_state','_record_login_failure','_password_expired','_mfa_required','_verify_totp','_encrypt_mfa_secret']:
        assert token in ui
    assert 'PSB_MFA_ENCRYPTION_KEY' in ui

def test_current_certificate_governance_labels():
    c=read('psb_app/services/certificate_service.py')
    assert 'Department Recommendation' in c
    assert 'CRB Outcome' in c
    assert 'Final Approving Authority' in c
    for old in ['<b>Tutor</b>','<b>Principal/Chief</b>','<b>QMS</b>']:
        assert old not in c

def test_current_navigation_is_single_source_and_legacy_workflow_not_reachable():
    ui=read('psb_app/pages/auth_ui.py')
    assert 'gm_buttons =' not in ui
    assert 'allowed_pages={default_page' in ui
    nav=read('core/navigation.py')
    for old_page in ['Job Allocation','Client Feedback','Performance & KPI','Revalidation','Annual Review']:
        assert old_page not in nav

def test_case_correspondence_and_handoff_notifications_exist():
    q=read('psb_app/pages/qualification.py')
    assert 'Activity & Correspondence' in q
    assert '_case_message' in q
    assert '_notify_roles' in q
    assert 'Authorization Ready for Final Decision' in q

def test_role_view_policy_matches_canonical_navigation():
    from core.navigation import ROLE_NAVIGATION
    p=json.loads(read('config/role_view_policy.json'))
    assert set(p)==set(ROLE_NAVIGATION)
    for role,sections in ROLE_NAVIGATION.items():
        got=[(x['name'],x['views'],x['view_group']) for x in p[role]['sections']]
        assert got==sections

def test_performance_guards_present():
    g=read('core/database_gateway.py')
    assert 'statement_timeout' in g and 'pool_timeout=15' in g
    runtime=read('psb_app/legacy_runtime.py')
    assert '@st.cache_data(ttl=20' in runtime
    common=read('psb_app/common.py')
    assert 'max_rows: int = 300' in common

def test_scope_engine_behaviour():
    from core.access_policy import scope_allows,filter_frame
    users=pd.DataFrame([
      {'user_id':'M1','role':'Department Manager','primary_department':'Survey NSC'},
      {'user_id':'U1','role':'Trainee','primary_department':'Survey NSC','trainer_id':'T1'},
      {'user_id':'U2','role':'Trainee','primary_department':'Plan Appraisal','trainer_id':'T2'},
      {'user_id':'T1','role':'Trainer','primary_department':'Training'},
    ])
    dm={'user_id':'M1','role':'Department Manager'}
    assert scope_allows(dm,'Department',{'user_id':'U1'},users)
    assert not scope_allows(dm,'Department',{'user_id':'U2'},users)
    tr={'user_id':'T1','role':'Trainer'}
    f=pd.DataFrame([{'user_id':'U1','value':1},{'user_id':'U2','value':2}])
    out=filter_frame(f,tr,users)
    assert out['user_id'].tolist()==['U1']
