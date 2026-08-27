"""Staging/production smoke checks. Set PSB_BASE_URL and optional PSB_VERIFY_BASE_URL.
Optional authentication checks use PSB_TEST_LOGIN/PSB_TEST_PASSWORD and are designed for staging.
Never print secrets.
"""
from __future__ import annotations
import os, sys, urllib.request, urllib.error, json
BASE_URL=os.getenv('PSB_BASE_URL','').rstrip('/')
VERIFY_BASE=os.getenv('PSB_VERIFY_BASE_URL', BASE_URL).rstrip('/')
CERT=os.getenv('PSB_VERIFY_CERT','')
if not BASE_URL:
    print('SKIP: set PSB_BASE_URL to run deployment smoke checks')
    raise SystemExit(0)
checks=[]
for url in [BASE_URL+'/', VERIFY_BASE+'/health' if VERIFY_BASE else '', VERIFY_BASE+'/verify/'+CERT if VERIFY_BASE and CERT else '']:
    if not url: continue
    try:
        req=urllib.request.Request(url, headers={'User-Agent':'PSB-live-smoke/1.0'})
        with urllib.request.urlopen(req,timeout=20) as resp:
            body=resp.read(8192).decode('utf-8','ignore')
            checks.append((url,resp.status,len(body)))
    except urllib.error.HTTPError as exc:
        checks.append((url,exc.code,0))
    except Exception as exc:
        print(f'FAIL {url}: {type(exc).__name__}')
        raise SystemExit(1)
for url,status,size in checks:
    if not (200 <= status < 500):
        raise SystemExit(f'FAIL {url}: HTTP {status}')
    print(f'PASS {url}: HTTP {status}, body={size} bytes')
print('Live HTTP smoke completed.')
print('For authenticated Supabase/RLS, Render multi-instance, browser, load and restore tests run the dedicated staging suites with real deployment credentials.')
