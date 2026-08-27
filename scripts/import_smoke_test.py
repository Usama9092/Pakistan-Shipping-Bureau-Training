"""PSB application import smoke test.

Run after installing requirements:
    python scripts/import_smoke_test.py

This catches circular imports and missing page/shared-symbol exports before
starting Streamlit.
"""
from __future__ import annotations
import importlib.util
import sys

required = ['streamlit', 'pandas', 'sqlalchemy', 'qrcode', 'PIL', 'docx', 'pptx']
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print('IMPORT SMOKE TEST: DEPENDENCIES MISSING:', ', '.join(missing))
    print('Install requirements first: pip install -r requirements.txt')
    raise SystemExit(2)

try:
    import app  # noqa: F401
except Exception as exc:
    print(f'IMPORT SMOKE TEST: FAIL: {type(exc).__name__}: {exc}')
    raise
else:
    print('IMPORT SMOKE TEST: PASS')
