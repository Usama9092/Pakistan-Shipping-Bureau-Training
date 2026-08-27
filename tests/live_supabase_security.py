"""Live Supabase security gate.
Requires a staging project and a low-privilege authenticated test user.
This script expects direct client table access to be denied by the server-only RLS posture.
"""
from __future__ import annotations
import os, sys, json, urllib.request, urllib.error

SUPABASE_URL=os.getenv('SUPABASE_URL','').rstrip('/')
ANON=os.getenv('SUPABASE_ANON_KEY','')
LOGIN=os.getenv('PSB_STAGING_LOGIN','')
PASSWORD=os.getenv('PSB_STAGING_PASSWORD','')
TABLES=[x.strip() for x in os.getenv('PSB_RLS_PROBE_TABLES','users,training_records,authorization_requests,qms_audits').split(',') if x.strip()]

def post(url, payload, headers=None):
    data=json.dumps(payload).encode()
    req=urllib.request.Request(url,data=data,method='POST',headers={'Content-Type':'application/json',**(headers or {})})
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.status, json.loads(r.read().decode() or '{}')

def get(url, headers):
    req=urllib.request.Request(url,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return r.status, r.read(1000)
    except urllib.error.HTTPError as e: return e.code, e.read(1000)

if __name__=='__main__':
    if not all([SUPABASE_URL,ANON,LOGIN,PASSWORD]):
        raise SystemExit('SKIP/FAIL: set SUPABASE_URL, SUPABASE_ANON_KEY, PSB_STAGING_LOGIN, PSB_STAGING_PASSWORD')
    status, body=post(SUPABASE_URL+'/auth/v1/token?grant_type=password',{'email':LOGIN,'password':PASSWORD},{'apikey':ANON})
    if status != 200 or 'access_token' not in body: raise SystemExit('FAIL: staging Supabase login')
    token=body['access_token']
    headers={'apikey':ANON,'Authorization':'Bearer '+token}
    for table in TABLES:
        code,_=get(f'{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1',headers)
        if code not in (401,403):
            raise SystemExit(f'FAIL: direct client access to {table} returned HTTP {code}; expected 401/403')
        print(f'PASS: direct client access denied for {table} (HTTP {code})')
    print('SUPABASE LIVE SECURITY GATE: PASS')
