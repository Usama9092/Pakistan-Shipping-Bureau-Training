from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')

def test_explicit_view_context_policy_entries():
    p=json.loads(read('config/role_view_context_policy.json'))
    assert p['On Probation']['My Qualification']=='Own'
    assert p['Trainer']['Qualification Workspace']=='Assigned'
    assert p['Department Manager']['Department Qualification']=='Department'

def test_no_removed_role_in_live_navigation():
    nav=read('core/navigation.py')
    for role in ['Principal Surveyor','Chief Plan Appraiser','Technical Manager']:
        assert f'"{role}":' not in nav
