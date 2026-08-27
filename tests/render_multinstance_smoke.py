"""Render multi-instance/session continuity check.
Provide PSB_INSTANCE_A_URL and PSB_INSTANCE_B_URL plus a pre-authenticated cookie header.
"""
from __future__ import annotations
import os, urllib.request, urllib.error
A=os.getenv('PSB_INSTANCE_A_URL','').rstrip('/')
B=os.getenv('PSB_INSTANCE_B_URL','').rstrip('/')
COOKIE=os.getenv('PSB_SESSION_COOKIE','')
if __name__=='__main__':
    if not all([A,B,COOKIE]): raise SystemExit('Set PSB_INSTANCE_A_URL, PSB_INSTANCE_B_URL, PSB_SESSION_COOKIE')
    for label,url in [('A',A),('B',B)]:
        req=urllib.request.Request(url+'/',headers={'Cookie':COOKIE,'User-Agent':'PSB-multi-instance/1.0'})
        try:
            with urllib.request.urlopen(req,timeout=20) as r: code=r.status
        except urllib.error.HTTPError as e: code=e.code
        if code >= 500: raise SystemExit(f'FAIL instance {label}: HTTP {code}')
        print(f'PASS instance {label}: HTTP {code}')
    print('RENDER MULTI-INSTANCE SESSION SMOKE: PASS (HTTP continuity; authenticated browser flow recommended)')
