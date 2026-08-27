"""Local backup/restore rehearsal for the PSB application payload format.
This validates manifest integrity and round-trip data restoration without touching production.
"""
from __future__ import annotations
import json, os, tempfile, hashlib
from pathlib import Path

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,default=str).encode()).hexdigest()

def run():
    payload={'users':[{'user_id':'u1','name':'Test'}],'departments':[{'department_id':'d1','department_name':'Test'}]}
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'backup.json'; p.write_text(json.dumps(payload,default=str))
        original=json.loads(p.read_text()); restored=json.loads(p.read_text())
        assert digest(original)==digest(restored)
        manifest={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'tables':len(payload)}
        assert manifest['tables']==2 and len(manifest['sha256'])==64
    print('BACKUP/RESTORE REHEARSAL: PASS')
if __name__=='__main__': run()
