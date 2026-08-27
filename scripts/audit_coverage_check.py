from pathlib import Path
import re, json, sys
ROOT=Path(__file__).resolve().parents[1]
registry=(ROOT/'database/migrations/019_audit_coverage_registry.sql').read_text()
source='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in (ROOT/'psb_app/pages').glob('*.py'))
required=re.findall(r"\('AUD-[^']+',\s*'([^']+)',\s*'([^']+)'", registry)
missing=[]
for module, action in required:
    if f"'{module}'" not in source and f'"{module}"' not in source:
        missing.append((module,action,'module not found'))
out={'required_events':len(required),'missing':missing,'status':'PASS' if not missing else 'FAIL'}
print(json.dumps(out,indent=2))
sys.exit(1 if missing else 0)
