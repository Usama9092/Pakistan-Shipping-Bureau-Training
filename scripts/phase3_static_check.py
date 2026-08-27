from pathlib import Path
import ast, json, re

ROOT=Path(__file__).resolve().parents[1]
apps=[ROOT/'app.py', ROOT/'psb_extracted'/'app.py']
report={"python_parse":{},"auth_identity":{},"legacy_duplicates":{},"tests":{}}
for p in apps:
    ast.parse(p.read_text())
    report["python_parse"][str(p.relative_to(ROOT))]=True
    txt=p.read_text()
    report["auth_identity"][str(p.relative_to(ROOT))]={
        "auth_user_id": "auth_user_id" in txt,
        "supabase_auth": "SupabaseAuthProvider" in txt,
        "force_password_change_guard": 'original_force = str(user.get("force_password_change", "No")) == "Yes"' in txt,
    }
    report["legacy_duplicates"][str(p.relative_to(ROOT))]={
        "files_page_absent": "def files_page" not in txt,
        "management_page_absent": "def management_page" not in txt,
    }
print(json.dumps(report, indent=2))
