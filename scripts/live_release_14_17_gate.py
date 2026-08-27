#!/usr/bin/env python3
"""Combined Gap 14-17 release gate.
Offline mode validates executable harnesses; --live runs environment-dependent gates when configured.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=['tests/test_gap14_audit_integration.py','tests/live_supabase_security.py','tests/render_multinstance_smoke.py','tests/browser_role_regression.py','tests/backup_restore_rehearsal.py','locustfile.py']

def offline():
    missing=[x for x in FILES if not (ROOT/x).exists()]
    if missing: raise SystemExit('GAP14-17 PREFLIGHT FAIL: '+', '.join(missing))
    print('GAP14-17 OFFLINE PREFLIGHT: PASS')

def live():
    offline()
    commands=[['python','tests/live_supabase_security.py'],['python','tests/render_multinstance_smoke.py'],['python','tests/browser_role_regression.py'],['python','tests/backup_restore_rehearsal.py']]
    for cmd in commands:
        subprocess.run(cmd,cwd=ROOT,check=True)
    print('GAP14-17 LIVE GATE: PASS')
if __name__=='__main__':
    live() if '--live' in sys.argv else offline()
