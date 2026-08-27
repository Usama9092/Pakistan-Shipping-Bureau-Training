#!/usr/bin/env python3
"""Preflight and optional live staging gate for PSB production validation.

Offline mode validates that the release contains all staging contracts.
Live mode performs network checks when the required environment variables are supplied.
"""
from __future__ import annotations
import json, os, sys, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ROOT/'database/rls_behavioral_tests.sql',
    ROOT/'database/supabase_rls_production.sql',
    ROOT/'scripts/production_gate.py',
    ROOT/'tests/live_environment_smoke.py',
    ROOT/'staging/README.md',
]

def http_get(url: str, timeout: int=15) -> tuple[int, str]:
    req=urllib.request.Request(url, headers={'User-Agent':'PSB-Staging-Gate/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return int(r.status), r.read(5000).decode('utf-8','ignore')
    except urllib.error.HTTPError as e:
        return int(e.code), e.read(1000).decode('utf-8','ignore')

def offline_gate() -> None:
    missing=[str(p.relative_to(ROOT)) for p in REQUIRED_FILES if not p.exists()]
    if missing:
        raise SystemExit('STAGING PREFLIGHT FAIL: missing '+', '.join(missing))
    print('STAGING PREFLIGHT: PASS')

def live_gate() -> None:
    offline_gate()
    app_url=os.getenv('STAGING_APP_URL')
    verify_url=os.getenv('STAGING_VERIFY_URL')
    if not app_url or not verify_url:
        raise SystemExit('LIVE gate requires STAGING_APP_URL and STAGING_VERIFY_URL')
    for label,url in [('app',app_url),('verify',verify_url)]:
        code,body=http_get(url)
        if code < 200 or code >= 400:
            raise SystemExit(f'LIVE gate FAIL: {label} returned HTTP {code}: {body[:200]}')
        print(f'{label}: HTTP {code}')
    supabase_url=os.getenv('SUPABASE_URL')
    anon_key=os.getenv('SUPABASE_ANON_KEY')
    if not supabase_url or not anon_key:
        raise SystemExit('LIVE gate also requires SUPABASE_URL and SUPABASE_ANON_KEY')
    # Lightweight auth endpoint reachability; role/RLS behavioral assertions remain in SQL harness.
    code,body=http_get(supabase_url.rstrip('/')+'/auth/v1/settings')
    if code < 200 or code >= 400:
        raise SystemExit(f'Supabase Auth endpoint failed HTTP {code}')
    print('supabase-auth-endpoint: PASS')
    print('LIVE STAGING GATE: PASS (network reachability; execute role/RLS SQL matrix separately)')

if __name__=='__main__':
    if '--live' in sys.argv:
        live_gate()
    else:
        offline_gate()
