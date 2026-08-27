from pathlib import Path
import re, json
ROOT = Path(__file__).resolve().parents[1]
rls = (ROOT / 'database' / 'supabase_rls_production.sql').read_text(encoding='utf-8', errors='ignore')
schema = (ROOT / 'database' / 'postgres_schema.sql').read_text(encoding='utf-8', errors='ignore')

def tables(text):
    return {m.group(1).lower() for m in re.finditer(r'(?:create table if not exists|create table)\s+(?:public\.)?([A-Za-z0-9_]+)', text, re.I)}

def enabled(text):
    return {m.group(1).lower() for m in re.finditer(r'alter table\s+(?:public\.)?([A-Za-z0-9_]+)\s+enable row level security', text, re.I)}

def revoked(text):
    return {m.group(1).lower() for m in re.finditer(r'revoke all on table public\.([A-Za-z0-9_]+) from anon, authenticated', text, re.I)}

schema_tables = tables(schema)
enabled_tables = enabled(rls)
revoked_tables = revoked(rls)
missing_enable = sorted(schema_tables - enabled_tables)
missing_revoke = sorted(schema_tables - revoked_tables)
client_select_policies = len(re.findall(r'create\s+policy\b[^\n]*\bon\s+public\.[^\s]+\s+for\s+select\s+to\s+authenticated', rls, re.I))
report = {
    'schema_tables': len(schema_tables),
    'rls_enabled_tables': len(enabled_tables),
    'client_privilege_revokes': len(revoked_tables),
    'schema_tables_without_rls_enable': missing_enable,
    'schema_tables_without_client_revoke': missing_revoke,
    'client_authenticated_select_policies': client_select_policies,
    'status': 'PASS' if not missing_enable and not missing_revoke and client_select_policies == 0 else 'FAIL'
}
print(json.dumps(report, indent=2))
if report['status'] != 'PASS':
    raise SystemExit(1)
