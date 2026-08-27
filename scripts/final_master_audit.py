#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from core.navigation import ROLE_NAVIGATION

def tables_from(pattern: str, path: Path):
    return set(re.findall(pattern, path.read_text(encoding='utf-8'), re.I))

schema=tables_from(r'create\s+table\s+if\s+not\s+exists\s+(?:public\.)?([a-zA-Z_][\w]*)', ROOT/'database/postgres_schema.sql')
rls=tables_from(r'alter\s+table\s+(?:public\.)?([a-zA-Z_][\w]*)\s+enable\s+row\s+level\s+security', ROOT/'database/supabase_rls_production.sql')
rev=tables_from(r'revoke\s+all\s+on\s+table\s+(?:public\.)?([a-zA-Z_][\w]*)', ROOT/'database/supabase_rls_production.sql')
route_count=sum(len(items) for sections in ROLE_NAVIGATION.values() for _,items,_ in sections)
migs=sorted(int(p.name.split('_',1)[0]) for p in (ROOT/'database/migrations').glob('[0-9][0-9][0-9]_*.sql'))
patches=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and 'archive' not in p.parts and (p.name.lower().endswith(('.bak','.tmp','.orig','.rej')) or ('patch' in p.name.lower() and p.suffix=='.py'))]
checks={
 'roles_configured':len(ROLE_NAVIGATION)==15 and {'GM','Trainer','Department Manager','NSC Surveyor','In-Service Surveyor'}.issubset(ROLE_NAVIGATION),
 'routes_mapped':subprocess.call([sys.executable,'scripts/final_role_page_audit.py'],cwd=ROOT,stdout=subprocess.DEVNULL)==0,
 'role_gap_loop_17':subprocess.call([sys.executable,'scripts/role_experience_gap_loop.py'],cwd=ROOT,stdout=subprocess.DEVNULL)==0,
 'schema_rls_exact_parity':schema==rls==rev,
 'no_patch_temp_artifacts':not patches,
 'migration_continuity':migs==list(range(migs[0],migs[-1]+1)),
 'embedded_security_parity': (not (ROOT/'psb_extracted').exists()) or ((ROOT/'database/supabase_rls_production.sql').read_bytes()==(ROOT/'psb_extracted/database/supabase_rls_production.sql').read_bytes() and (ROOT/'core/navigation.py').read_bytes()==(ROOT/'psb_extracted/core/navigation.py').read_bytes()),
 'plain_pytest':subprocess.call([sys.executable,'-m','pytest','-q'],cwd=ROOT,stdout=subprocess.DEVNULL)==0,
}
status='PASS' if all(checks.values()) else 'FAIL'
out={
 'status':status,'checks':checks,'roles':len(ROLE_NAVIGATION),'routes':route_count,
 'schema_tables':len(schema),'rls_tables':len(rls),'client_revokes':len(rev),
 'migrations':f'{migs[0]:03d}-{migs[-1]:03d}','patch_temp_artifacts':patches,
 'external_staging_required':['Supabase JWT/RLS behavioral verification','Render multi-instance continuity','browser role regression','realistic load','real backup/restore']
}
(ROOT/'FINAL_MASTER_AUDIT.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
raise SystemExit(0 if status=='PASS' else 1)
