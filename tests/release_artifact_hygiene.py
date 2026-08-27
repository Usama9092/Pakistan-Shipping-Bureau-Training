from __future__ import annotations
from pathlib import Path
import json, re
from core.navigation import ROLE_NAVIGATION
ROOT=Path(__file__).resolve().parents[1]

def _schema_count():
    t=(ROOT/'database/postgres_schema.sql').read_text(encoding='utf-8')
    return len(set(re.findall(r'create\s+table\s+if\s+not\s+exists\s+(?:public\.)?([a-zA-Z_][\w]*)',t,re.I)))

def test_active_release_manifest_is_source_derived() -> None:
    m=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    routes=sum(len(items) for sections in ROLE_NAVIGATION.values() for _,items,_ in sections)
    assert m['roles']==len(ROLE_NAVIGATION)
    assert m['routes']==routes
    assert m['schema_tables']==_schema_count()

def test_historical_audits_are_archived() -> None:
    required=['BEASTMODE_FINAL_AUDIT.md','FINAL_17_GAP_CLOSURE_REPORT.md','FINAL_GAP_AUDIT.json','FINAL_ROLE_PAGE_AUDIT.json']
    missing=[x for x in required if not (ROOT/'archive/audits'/x).exists()]
    assert not missing, f'not archived: {missing}'
