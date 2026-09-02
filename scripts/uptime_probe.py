"""HTTP and WebSocket health probe for Streamlit deployments."""
from __future__ import annotations
import json, os, urllib.request
from urllib.parse import urlparse

def main():
    base=os.getenv('PSB_MONITOR_URL','https://pakistan-shipping-bureau-training.onrender.com').rstrip('/')
    results={}
    for path in ('/_stcore/health','/_stcore/host-config','/'):
        with urllib.request.urlopen(base+path,timeout=30) as response:
            results[path]=response.status
            if response.status != 200: raise SystemExit(f'HTTP probe failed: {path}={response.status}')
    try:
        import websocket
        parsed=urlparse(base); scheme='wss' if parsed.scheme=='https' else 'ws'
        ws=websocket.create_connection(f'{scheme}://{parsed.netloc}/_stcore/stream',timeout=20,subprotocols=['streamlit'],origin=base)
        results['websocket']='connected'; ws.close()
    except Exception as exc:
        raise SystemExit(f'WebSocket probe failed: {type(exc).__name__}')
    print(json.dumps(results,sort_keys=True))

if __name__=='__main__': main()

