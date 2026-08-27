from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
checks={}; errors=[]
def ok(name,value,detail=''):
    checks[name]={'ok':bool(value),'detail':detail}
    if not value: errors.append(name)
main=(ROOT/'psb_app'/'main.py').read_text(encoding='utf-8')
auth=(ROOT/'psb_app'/'pages'/'auth_ui.py').read_text(encoding='utf-8')
design=(ROOT/'core'/'design_system.py').read_text(encoding='utf-8')
prod_path=(ROOT/'core'/'production.py')
cfg=(ROOT/'.streamlit'/'config.toml').read_text(encoding='utf-8')
ok('global_design_system', all(x in design+auth for x in ['psb-page-kicker','psb-empty','psb-status','psb-role-dot']), 'shared UX tokens/components')
ok('fixed_sidebar', '290px' in design+auth, 'fixed sidebar width')
ok('sidebar_toggle_hidden', 'Toggle sidebar' in design+auth and 'display:none' in design+auth, 'sidebar toggle suppressed')
ok('visible_signout', 'psb-signout' in auth or 'Sign out' in auth, 'sign-out component exists')
ok('role_header', '_page_kicker' in main or 'page_kicker' in auth, 'role-aware global header')
ok('global_page_error_boundary', 'unhandled_page_error' in main and 'Reference:' in main, 'global error handling')
ok('global_spinner', 'st.spinner' in main, 'global loading state')
ok('production_module', prod_path.exists(), 'production module')
ok('xsrf_enabled', 'enableXsrfProtection = true' in cfg, 'Streamlit XSRF')
ok('cors_disabled', 'enableCORS = false' in cfg, 'CORS disabled')
text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in (ROOT/'psb_app').rglob('*.py'))
ok('legacy_files_removed', 'def files_page' not in text, 'legacy Files workflow removed')
ok('legacy_management_removed', 'def management_page' not in text, 'legacy Management workflow removed')
extract=ROOT/'psb_extracted'/'psb_app'/'main.py'
ok('single_canonical_codebase', (not extract.exists()) or extract.read_text(encoding='utf-8') == main, 'no divergent embedded application copy')
# Explicit role nav test
nav=(ROOT/'core'/'navigation.py').read_text(encoding='utf-8')
roles=['GM','Admin','Trainer','Department Manager','Surveyor','Plan Appraiser','QMS Auditor','Industrial Surveyor','Rule Development Rep','QMR','Management','Trainee','On Probation']
ok('explicit_role_navigation', all(f'"{r}"' in nav for r in roles), 'explicit role navigation including GM')
out={'checks':checks,'errors':errors,'status':'PASS' if not errors else 'FAIL'}
(ROOT/'PHASE4_VALIDATION.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
sys.exit(1 if errors else 0)
