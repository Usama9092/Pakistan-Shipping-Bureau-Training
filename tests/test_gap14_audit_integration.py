from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
CRITICAL = {
    'User Created': 'psb_app/pages/admin.py',
    'Role Permissions Updated': 'psb_app/pages/admin.py',
    'Authorization': 'psb_app/pages/authorization.py',
    'CRB': 'psb_app/pages/authorization.py',
    'Competency': 'psb_app/pages/competency.py',
    'Job': 'psb_app/pages/operations.py',
    'NCR': 'psb_app/pages/competency.py',
    'QMS Audit': 'psb_app/pages/quality.py',
    'Management Review Action': 'psb_app/pages/role_workspaces.py',
}

def test_critical_modules_have_audit_calls():
    for label, rel in CRITICAL.items():
        p = ROOT / rel
        assert p.exists(), f'missing source: {rel}'
        text = p.read_text(errors='ignore')
        assert 'audit(' in text, f'{label}: no audit call in {rel}'

def test_critical_audit_actions_are_distinct_and_machine_checkable():
    texts='\n'.join((ROOT/p).read_text(errors='ignore') for p in {
        'psb_app/pages/admin.py','psb_app/pages/authorization.py','psb_app/pages/competency.py',
        'psb_app/pages/operations.py','psb_app/pages/quality.py','psb_app/pages/role_workspaces.py'})
    actions=set(re.findall(r"audit\(['\"]([^'\"]+)['\"]", texts))
    required = {
        'User Created','Role Permissions Updated','QMS Audit Created','Technical Review Created',
        'Interpretation Submitted','Management Review Action Created','Management Review Action Updated'
    }
    assert required <= actions
