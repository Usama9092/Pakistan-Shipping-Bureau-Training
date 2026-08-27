from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.schema_contract import contract_report

root = ROOT
report = contract_report(root, root / "database" / "postgres_schema.sql")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["contract_ok"] else 1)
