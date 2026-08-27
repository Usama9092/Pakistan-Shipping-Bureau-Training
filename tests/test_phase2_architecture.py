from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.schema_contract import contract_report

def test_schema_contract_is_complete():
    report = contract_report(ROOT, ROOT / "database" / "postgres_schema.sql")
    assert report["contract_ok"], report

def test_legacy_pages_removed():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "def files_page(" not in app
    assert "def management_page(" not in app

def test_central_permission_engine_exists():
    common = (ROOT / "psb_app" / "common.py").read_text(encoding="utf-8") + (ROOT / "psb_app" / "legacy_runtime.py").read_text(encoding="utf-8")
    auth = (ROOT / "core" / "authorization.py").read_text(encoding="utf-8")
    assert "def can_action(" in auth
    assert "can_action" in ((ROOT / 'psb_app' / 'services' / 'policy_service.py').read_text(encoding='utf-8'))
    assert "from core.authorization import" in common
