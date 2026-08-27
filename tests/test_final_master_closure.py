from __future__ import annotations
from pathlib import Path
import json, re, ast

ROOT = Path(__file__).resolve().parents[1]

def _schema_tables():
    text=(ROOT/'database/postgres_schema.sql').read_text(encoding='utf-8')
    return set(re.findall(r'create\s+table\s+if\s+not\s+exists\s+(?:public\.)?([a-zA-Z_][\w]*)', text, re.I))

def _rls_tables():
    text=(ROOT/'database/supabase_rls_production.sql').read_text(encoding='utf-8')
    return set(re.findall(r'alter\s+table\s+(?:public\.)?([a-zA-Z_][\w]*)\s+enable\s+row\s+level\s+security', text, re.I))

def _revoke_tables():
    text=(ROOT/'database/supabase_rls_production.sql').read_text(encoding='utf-8')
    return set(re.findall(r'revoke\s+all\s+on\s+table\s+(?:public\.)?([a-zA-Z_][\w]*)', text, re.I))

def test_no_release_patch_or_temp_artifacts():
    bad=[]
    for p in ROOT.rglob('*'):
        if not p.is_file() or 'archive' in p.parts: continue
        n=p.name.lower()
        if n.endswith(('.bak','.tmp','.orig','.rej')) or 'patch' in n and n.endswith('.py'):
            bad.append(str(p.relative_to(ROOT)))
    assert not bad, f'release patch/temp artifacts present: {bad}'

def test_production_rls_exactly_matches_canonical_schema():
    schema=_schema_tables(); rls=_rls_tables(); rev=_revoke_tables()
    assert rls == schema, f'RLS drift: extra={sorted(rls-schema)}, missing={sorted(schema-rls)}'
    assert rev == schema, f'revoke drift: extra={sorted(rev-schema)}, missing={sorted(schema-rev)}'

def test_release_manifest_matches_source():
    from core.navigation import ROLE_NAVIGATION
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    route_count=sum(len(items) for sections in ROLE_NAVIGATION.values() for _,items,_ in sections)
    migrations=sorted(int(p.name.split('_',1)[0]) for p in (ROOT/'database/migrations').glob('[0-9][0-9][0-9]_*.sql'))
    assert manifest['roles'] == len(ROLE_NAVIGATION)
    assert manifest['routes'] == route_count
    assert manifest['schema_tables'] == len(_schema_tables())
    assert manifest['rls_enabled'] == len(_rls_tables())
    assert manifest['client_revokes'] == len(_revoke_tables())
    assert manifest['migration_versions'] == f'{migrations[0]:03d}-{migrations[-1]:03d}'

def test_no_wildcard_imports_in_application_code():
    bad=[]
    for base in (ROOT/'psb_app', ROOT/'core'):
        for p in base.rglob('*.py'):
            tree=ast.parse(p.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and any(a.name=='*' for a in node.names):
                    bad.append(str(p.relative_to(ROOT)))
    assert not bad, f'wildcard imports: {bad}'

def test_historical_release_reports_not_active_at_root():
    allowed={
        'README.md','PRODUCTION_READY.md','DEPLOYMENT_GUIDE.md','DEPLOYMENT_CHECKLIST.md',
        'LIVE_ENVIRONMENT_TEST_PLAN.md','LIVE_RELEASE_GATE.md','LIVE_TEST_EXECUTION.md',
        'SECURITY_MODEL.md','MODULAR_ARCHITECTURE.md','PERFORMANCE_AND_UPTIME_GUIDE.md',
        'FINAL_RELEASE_EXECUTION_GATE.md','RELEASE_HYGIENE.md','FINAL_MASTER_AUDIT.md'
    }
    bad=[]
    for p in ROOT.glob('*.md'):
        if p.name in allowed: continue
        if re.search(r'(GAP\d|PHASE\d|_UPDATE|ROLE_ALIGNMENT|SEVENTEEN|FINAL_GAP|BEASTMODE)', p.name):
            bad.append(p.name)
    assert not bad, f'historical release reports still active at root: {bad}'

def test_embedded_security_and_navigation_parity():
    embedded=ROOT/'psb_extracted'
    if not embedded.exists():
        return
    pairs=[
        (ROOT/'database/supabase_rls_production.sql', embedded/'database/supabase_rls_production.sql'),
        (ROOT/'core/navigation.py', embedded/'core/navigation.py'),
        (ROOT/'config/role_scope_policy.json', embedded/'config/role_scope_policy.json'),
        (ROOT/'config/role_view_context_policy.json', embedded/'config/role_view_context_policy.json'),
    ]
    drift=[]
    for a,b in pairs:
        if not b.exists() or a.read_bytes()!=b.read_bytes():
            drift.append(str(b.relative_to(ROOT)))
    assert not drift, f'embedded authoritative-file drift: {drift}'
