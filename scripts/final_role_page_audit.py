#!/usr/bin/env python3
from __future__ import annotations
import json, ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'core/navigation.py').read_text(encoding='utf-8')
tree=ast.parse(src)
value=None
for n in tree.body:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id=='ROLE_NAVIGATION':
                value=ast.literal_eval(n.value)
if not isinstance(value, dict):
    raise SystemExit('ROLE_NAVIGATION not statically readable')
labels=[]
for role, groups in value.items():
    for group, items, target in groups:
        for label in items:
            labels.append((role,group,label,target))
report={'roles':sorted(value),'role_count':len(value),'route_count':len(labels),'duplicate_labels_within_role':{},'unmapped_targets':[]}
for role in value:
    seen=[l for r,g,l,t in labels if r==role]
    dup=sorted({x for x in seen if seen.count(x)>1})
    if dup: report['duplicate_labels_within_role'][role]=dup
# target module must exist; label-level aliases may use the same module as the parent group.
modules={p.stem for p in (ROOT/'psb_app/pages').glob('*.py')}
for role,group,label,target in labels:
    if target not in modules and target not in {'mywork','myops','dashboard'}:
        report['unmapped_targets'].append({'role':role,'label':label,'target':target})
report['status']='PASS' if value and not report['duplicate_labels_within_role'] and not report['unmapped_targets'] else 'FAIL'
(ROOT/'FINAL_ROLE_PAGE_AUDIT.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
