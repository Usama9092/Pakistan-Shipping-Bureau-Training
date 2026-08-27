from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def test_no_wildcard_imports_in_application():
    files=list((ROOT/'psb_app').rglob('*.py')) + list((ROOT/'core').rglob('*.py'))
    bad=[]
    for p in files:
        text=p.read_text(encoding='utf-8', errors='ignore')
        if re.search(r'^\s*from\s+[^#\n]+\s+import\s+\*', text, re.M):
            bad.append(str(p.relative_to(ROOT)))
    assert not bad, f'wildcard imports remain: {bad}'
