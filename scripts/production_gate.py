#!/usr/bin/env python3
"""Run the deterministic local release gate before deployment."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cmds=[
    [sys.executable,'-m','pytest','-q'],
    [sys.executable,'tests/architecture_gap_guard.py'],
    [sys.executable,'tests/migration_check.py'],
    [sys.executable,'tests/rls_policy_check.py'],
    [sys.executable,'scripts/phase4_static_check.py'],
    [sys.executable,'scripts/audit_coverage_check.py'],
    [sys.executable,'scripts/final_gap_audit.py'],
    [sys.executable,'scripts/final_master_audit.py'],
]
for cmd in cmds:
    print('RUN', ' '.join(cmd))
    rc=subprocess.call(cmd,cwd=ROOT)
    if rc!=0:
        raise SystemExit(rc)
print('PRODUCTION GATE: PASS')
