from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
schema=(ROOT/'database'/'postgres_schema.sql').read_text().lower()
sql=(ROOT/'database'/'supabase_rls_production.sql').read_text().lower()
def tables(text):
    return {m.group(1) for m in re.finditer(r'(?:create table if not exists|create table)\s+(?:public\.)?([a-z0-9_]+)', text, re.I)}
def enabled(text):
    return {m.group(1) for m in re.finditer(r'alter table\s+(?:public\.)?([a-z0-9_]+)\s+enable row level security', text, re.I)}
def revoked(text):
    return {m.group(1) for m in re.finditer(r'revoke all on table public\.([a-z0-9_]+) from anon, authenticated', text, re.I)}
schema_tables=tables(schema)
missing=sorted(schema_tables-enabled(sql))
missing_revoke=sorted(schema_tables-revoked(sql))
assert not missing, missing
assert not missing_revoke, missing_revoke
assert not re.search(r'create policy\s+\S+\s+on\s+public\.\S+\s+for\s+select\s+to\s+authenticated', sql)
print({'rls_policy_check':'passed','schema_tables':len(schema_tables),'rls_enabled_tables':len(enabled(sql)),'client_privilege_revokes':len(revoked(sql)),'client_select_policies':0})
