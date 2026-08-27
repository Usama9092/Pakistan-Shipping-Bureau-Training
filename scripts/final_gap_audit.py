from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
report={}

def check(k,v,detail=''):
    report[k]={'status':'PASS' if v else 'FAIL','detail':detail}

schema=(ROOT/'database/postgres_schema.sql').read_text(errors='ignore').lower()
rls=(ROOT/'database/supabase_rls_production.sql').read_text(errors='ignore').lower()
tables=set(re.findall(r'create table if not exists\s+(?:public\.)?([a-z0-9_]+)',schema))
enabled=set(re.findall(r'alter table\s+public\.([a-z0-9_]+)\s+enable row level security',rls))
revoked=set(re.findall(r'revoke all on table public\.([a-z0-9_]+) from anon, authenticated',rls))
check('01_rls_all_tables', tables <= enabled, f'{len(tables)} schema tables; {len(tables-enabled)} missing RLS enable')
check('02_client_privileges_denied', tables <= revoked, f'{len(tables-revoked)} tables without explicit client revoke')

runtime=(ROOT/'psb_app/legacy_runtime.py').read_text(errors='ignore')
common=(ROOT/'psb_app/common.py').read_text(errors='ignore')
pages='\n'.join(p.read_text(errors='ignore') for p in (ROOT/'psb_app/pages').glob('*.py'))
check('03_record_authorization_boundary', 'def authorize_action(' in (ROOT/'core/authorization.py').read_text() and 'authorize_action(actor, module, action' in runtime, 'single mutation authorization API')
check('04_no_page_write_sql_bypass', not re.search(r'exec_sql\(\s*["\']\s*(?:insert|update|delete)\b', pages, re.I), 'all page writes go through guarded db_* helpers')
check('05_internal_mutation_context', '_SERVER_INTERNAL_TABLES' in runtime and 'is_system_write()' in runtime and 'MUTATION_GUARD_EXEMPT' not in runtime, 'system writes require explicit context')
policy=(ROOT/'core/access_policy.py').read_text(errors='ignore')
role_policy=(ROOT/'config/role_scope_policy.json').read_text(errors='ignore') if (ROOT/'config/role_scope_policy.json').exists() else ''
check('06_scope_contract_explicit', all(x in role_policy for x in ['Trainer','Department Manager','Surveyor','Plan Appraiser','Rule Development Rep','Trainee','QMS Auditor']), 'role/module scopes declared')

try:
    _role_policy_obj=json.loads(role_policy)
except Exception:
    _role_policy_obj={}
crb_migration=(ROOT/'database/migrations/038_qualification_path_levels_modules_crb_board.sql').read_text(errors='ignore').lower()
check('07_crb_case_scope', 'crb_case_board_assignments' in crb_migration and 'board_role text not null' in crb_migration and 'crb member' not in _role_policy_obj, 'CRB is a case-based board assignment and not a standalone account role')
check('08_qr_logging_ratelimit', '_log_qr_event' in (ROOT/'psb_app/pages/public_verify.py').read_text() and '_qr_rate_limited' in (ROOT/'psb_app/pages/public_verify.py').read_text() and 'RATE_LIMIT' in (ROOT/'verify_service.py').read_text(), 'public verification telemetry and throttling')
check('09_rbac_centralized', 'def can_action(' in (ROOT/'core/authorization.py').read_text() and 'def authorize_record' in (ROOT/'core/authorization.py').read_text(), 'central authorization layer')
check('10_common_facade', len(common.splitlines()) < 120 and 'legacy_runtime' in common, f'common.py is {len(common.splitlines())} lines')
check('11_no_page_ddl', not re.search(r'create table if not exists\s+(training_requirements|competency_reviews|departments)', pages, re.I), 'no page-level schema creation')
check('12_no_active_sessions_dict', 'ACTIVE_SESSIONS' not in runtime, 'sessions are DB-backed')
check('13_audit_coverage', (ROOT/'scripts/audit_coverage_check.py').exists(), 'machine-auditable audit registry/checker present')
check('14_backup_gate', (ROOT/'LIVE_RELEASE_GATE.md').exists() and 'restore' in (ROOT/'LIVE_RELEASE_GATE.md').read_text(errors='ignore').lower(), 'backup/restore release gate documented')
check('15_scheduler_health', all(x in (ROOT/'core/scheduler.py').read_text(errors='ignore') for x in ['retry','next_retry_at','scheduler_runs']), 'retry/backoff telemetry')
check('16_kpi_governance', 'approval_status' in (ROOT/'database/migrations/024_kpi_governance_defaults.sql').read_text(errors='ignore') and 'calculation_version' in (ROOT/'database/postgres_schema.sql').read_text(errors='ignore'), 'KPI definitions versioned with business approval metadata')
check('17_public_verify_service', (ROOT/'verify_render.yaml').exists() and (ROOT/'verify_service.py').exists(), 'isolated public verification service artifacts present')

# External deployment-only checks are tracked separately and intentionally not falsely marked PASS here.
report['EXTERNAL_1_SUPABASE_JWT_RLS']='REQUIRES_STAGING_EXECUTION'
report['EXTERNAL_2_RENDER_MULTII_INSTANCE']='REQUIRES_STAGING_EXECUTION'
report['EXTERNAL_3_BROWSER_REGRESSION']='REQUIRES_STAGING_EXECUTION'
report['EXTERNAL_4_LOAD_TEST']='REQUIRES_STAGING_EXECUTION'
report['EXTERNAL_5_REAL_BACKUP_RESTORE']='REQUIRES_STAGING_EXECUTION'

fails=[k for k,v in report.items() if isinstance(v,dict) and v.get('status')=='FAIL']
out={'checks':report,'failed_static_checks':fails,'overall_static_status':'PASS' if not fails else 'FAIL'}
(ROOT/'FINAL_GAP_AUDIT.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
raise SystemExit(1 if fails else 0)
