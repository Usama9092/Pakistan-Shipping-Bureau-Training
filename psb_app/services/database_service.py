"""Database/bootstrap compatibility service extracted from legacy_runtime."""
from __future__ import annotations
from psb_app import legacy_runtime as _runtime

def __getattr__(name):
    return getattr(_runtime, name)

CORE_THEORETICAL_MODULES = getattr(_runtime, 'CORE_THEORETICAL_MODULES')
DATABASE_URL = getattr(_runtime, 'DATABASE_URL')
DEFAULT_AUTH_MATRIX = getattr(_runtime, 'DEFAULT_AUTH_MATRIX')
DEFAULT_ROLE_DESCRIPTIONS = getattr(_runtime, 'DEFAULT_ROLE_DESCRIPTIONS')
DEMO_PASSWORD = getattr(_runtime, 'DEMO_PASSWORD')
ENABLE_DEMO_SEED = getattr(_runtime, 'ENABLE_DEMO_SEED')
INITIAL_ADMIN_EMAIL = getattr(_runtime, 'INITIAL_ADMIN_EMAIL')
INITIAL_ADMIN_LOGIN = getattr(_runtime, 'INITIAL_ADMIN_LOGIN')
INITIAL_ADMIN_NAME = getattr(_runtime, 'INITIAL_ADMIN_NAME')
INITIAL_ADMIN_PASSWORD = getattr(_runtime, 'INITIAL_ADMIN_PASSWORD')
LOGIN_BLOCK_MINUTES = getattr(_runtime, 'LOGIN_BLOCK_MINUTES')
MAX_LOGIN_ATTEMPTS = getattr(_runtime, 'MAX_LOGIN_ATTEMPTS')
PERMISSION_ACTIONS = getattr(_runtime, 'PERMISSION_ACTIONS')
PERMISSION_MODULES = getattr(_runtime, 'PERMISSION_MODULES')
PERMISSION_SCOPES = getattr(_runtime, 'PERMISSION_SCOPES')
Path = getattr(_runtime, 'Path')
ROLES = getattr(_runtime, 'ROLES')
audit = getattr(_runtime, 'audit')
db_all = getattr(_runtime, 'db_all')
db_insert = getattr(_runtime, 'db_insert')
exec_sql = getattr(_runtime, 'exec_sql')
logging = getattr(_runtime, 'logging')
now = getattr(_runtime, 'now')
pd = getattr(_runtime, 'pd')
phash = getattr(_runtime, 'phash')
run_pending_migrations = getattr(_runtime, 'run_pending_migrations')
st = getattr(_runtime, 'st')
temp_password = getattr(_runtime, 'temp_password')
today = getattr(_runtime, 'today')
uid = getattr(_runtime, 'uid')
@st.cache_resource(show_spinner=False)
def init_db() -> None:
    stmts = ['create table if not exists users (\n            user_id text primary key, name text, role text, trainee_path text, department text, assigned_duty text,\n            email text unique, login_id text unique, password_hash text, auth_user_id text, status text,\n            availability text, current_location text, mentor_id text, mentor_name text,\n            tutor_id text, tutor_name text, trainer_id text, trainer_name text,\n            assigner_id text, assigner_name text, competency_level text,\n            created_on text, last_login text\n        )', 'create table if not exists training_modules (\n            module_id text primary key, title text, module_group text, target_path text, mandatory text,\n            refresher_required text, cpd_hours real, validity_months integer, added_by text, created_on text\n        )', 'create table if not exists trainings (\n            training_id text primary key, module_id text, title text, category text, standards text, target_roles text,\n            target_paths text, trainer_id text, trainer_name text, slides_link text, video_link text, reference_link text,\n            scorm_package_link text, lms_course_id text, schedule_date text, schedule_time text, meeting_link text,\n            recording_link text, passing_marks integer, validity_months integer, max_attempts integer, retest_wait_days integer,\n            status text, created_on text, updated_on text\n        )', 'create table if not exists files (\n            file_id text primary key, owner_user_id text, owner_name text, linked_table text, linked_id text,\n            category text, file_name text, file_ext text, mime_type text, storage_provider text,\n            storage_path text, public_url text, extracted_text text, ocr_status text, review_status text,\n            created_on text, updated_on text\n        )', 'create table if not exists training_records (\n            record_id text primary key, user_id text, name text, role text, trainee_path text, training_id text,\n            training_title text, status text, slides_opened text, video_opened text, live_attendance text,\n            recording_opened text, lms_completed text, test_status text, score real, passing_marks integer,\n            certificate_status text, certificate_link text, due_date text, completed_on text, progress integer,\n            remarks text, updated_on text\n        )', 'create table if not exists training_requirements (\n            requirement_id text primary key, module_id text, requirement_name text, department text, role text, trainee_path text,\n            requirement_type text, mandatory text, priority text, prerequisite_module_ids text, sequence_no integer, validity_months integer,\n            effective_from text, effective_to text, active text, notes text, created_by text, created_on text, updated_by text, updated_on text\n        )', 'create table if not exists competency_reviews (\n            review_id text primary key, competency_id text, user_id text, name text, scope text, current_level text, recommended_level text,\n            decision text, rationale text, evidence_summary text, gaps text, reviewer_id text, reviewer_name text, reviewed_on text,\n            next_review_date text, status text, created_on text, updated_on text\n        )', 'create table if not exists question_bank (\n            question_id text primary key, training_id text, question text, option_a text, option_b text,\n            option_c text, option_d text, correct_answer text, marks integer, generated_on text\n        )', 'create table if not exists assessment_history (\n            assessment_id text primary key, user_id text, name text, training_id text, training_title text,\n            attempt_no integer, score real, result text, attempted_on text, next_retest_allowed text, remarks text\n        )', 'create table if not exists competency_matrix (\n            competency_id text primary key, user_id text, name text, role text, trainee_path text, area text,\n            competency_level text, scope text, job_type text, required_training_ids text, required_witness_count integer,\n            required_supervised_count integer, required_joint_plan_count integer, required_independent_plan_count integer,\n            required_level_for_auth text, status text, expiry_date text, evidence text, created_on text, updated_on text\n        )', 'create table if not exists authorization_matrix (\n            matrix_id text primary key, scope text, job_type text, required_witness_count integer,\n            required_supervised_count integer, required_joint_plan_count integer, required_independent_plan_count integer,\n            required_level_for_auth text, minimum_job_level text, risk_category text, validity_months integer, active text\n        )', 'create table if not exists development_plans (\n            plan_id text primary key, user_id text, name text, trainee_path text, mentor_id text, mentor_name text,\n            competency_scope text, month_no integer, activity text, target_date text, status text, mentor_comments text,\n            created_on text, updated_on text\n        )', 'create table if not exists witness_surveys (\n            witness_id text primary key, user_id text, name text, trainee_path text, tutor_id text, tutor_name text,\n            vessel_or_project text, job_type text, scope text, witness_date text, location text, technical_knowledge integer,\n            rule_application integer, safety_awareness integer, communication integer, report_quality integer,\n            professional_conduct integer, outcome text, comments text, status text, created_on text, updated_on text\n        )', 'create table if not exists supervised_activities (\n            supervised_id text primary key, user_id text, name text, trainee_path text, tutor_id text, tutor_name text,\n            activity_kind text, vessel_or_project text, job_type text, scope text, activity_date text, location text,\n            preparation integer, execution_quality integer, findings_quality integer, reporting_quality integer,\n            rule_compliance integer, outcome text, comments text, status text, created_on text, updated_on text\n        )', 'create table if not exists authorization_requests (\n            authorization_id text primary key, user_id text, name text, trainee_path text, job_type text, scope text,\n            competency_id text, status text, tutor_remarks text, tutor_signature text, tutor_signed_on text,\n            principal_remarks text, principal_signature text, principal_signed_on text, technical_remarks text,\n            technical_signature text, technical_signed_on text, qms_remarks text, qms_signature text, qms_signed_on text,\n            crb_decision text, crb_remarks text, management_remarks text, management_signature text,\n            management_signed_on text, expiry_date text, certificate_id text, certificate_html text,\n            certificate_storage_link text, qr_data_uri text, created_on text, updated_on text\n        )', 'create table if not exists authorization_certificates (\n            certificate_id text primary key, authorization_id text, user_id text, name text, scope text, job_type text,\n            issue_date text, expiry_date text, certificate_html text, qr_data_uri text, storage_link text,\n            verification_url text, status text, created_on text\n        )', 'create table if not exists crb_reviews (\n            crb_id text primary key, authorization_id text, user_id text, name text, scope text, review_date text,\n            tutor_decision text, technical_decision text, qmr_decision text, management_decision text,\n            final_decision text, remarks text, signed_by text, created_on text\n        )', 'create table if not exists annual_reviews (\n            review_id text primary key, user_id text, name text, scope text, review_year integer,\n            training_status text, kpi_status text, complaint_status text, capa_status text, decision text,\n            reviewer text, review_date text, remarks text\n        )', 'create table if not exists revalidation_requests (\n            revalidation_id text primary key, authorization_id text, user_id text, name text, scope text,\n            refresher_training_status text, annual_review_status text, kpi_review_status text, tutor_confirmation text,\n            crb_status text, final_status text, due_date text, created_on text, updated_on text\n        )', 'create table if not exists job_requests (\n            job_id text primary key, job_title text, job_type text, required_scope text, vessel_name text,\n            imo_number text, location text, planned_date text, priority text, risk_level text, minimum_level text,\n            required_department text, estimated_days integer, client_name text, client_reference text, notes text,\n            status text, created_by text, assigned_user_id text, assigned_user_name text, assignment_reason text,\n            created_on text, updated_on text, completed_on text, cancelled_on text, cancellation_reason text\n        )', 'create table if not exists job_assignments (\n            assignment_id text primary key, job_id text, user_id text, user_name text, assignment_type text,\n            assigned_by text, assigned_on text, accepted_on text, released_on text, status text,\n            reason text, eligibility_snapshot text, created_on text\n        )', 'create table if not exists kpi_records (\n            kpi_id text primary key, user_id text, name text, period text, surveys_done integer,\n            plans_reviewed integer, audits_done integer, reports_overdue integer, ncr_count integer,\n            client_feedback real, training_compliance real, utilization_percent real, kpi_score real,\n            created_on text, remarks text\n        )', 'create table if not exists kpi_snapshots (\n            snapshot_id text primary key, user_id text, name text, period text,\n            training_score real, competency_score real, authorization_score real,\n            technical_review_score real, quality_score real, delivery_score real,\n            client_feedback_score real, ncr_score real, utilization_score real,\n            overall_score real, status text, calculation_version text,\n            source_counts text, calculated_on text, calculated_by text, notes text\n        )', 'create table if not exists cpd_records (\n            cpd_id text primary key, user_id text, name text, title text, category text, hours real,\n            provider text, completion_date text, evidence_file_id text, status text, created_on text\n        )', 'create table if not exists knowledge_library (\n            knowledge_id text primary key, title text, category text, standard text, revision text, issue_date text,\n            file_id text, mandatory_ack text, uploaded_by text, created_on text\n        )', 'create table if not exists knowledge_acknowledgements (\n            ack_id text primary key, knowledge_id text, user_id text, name text, acknowledged_on text, status text\n        )', 'create table if not exists rule_library (\n            rule_id text primary key, title text, standard text, revision text, category text, link text,\n            mandatory text, current_version_id text, created_on text, updated_on text\n        )', 'create table if not exists qms_audits (\n            audit_id text primary key, audit_type text, department text, standard text, audit_scope text,\n            lead_auditor_id text, lead_auditor_name text, planned_date text, completed_date text,\n            status text, overall_result text, objective text, report_summary text, created_by text, created_on text, updated_on text\n        )', 'create table if not exists qms_compliance_items (\n            compliance_id text primary key, standard text, clause text, requirement text, owner_department text,\n            owner_id text, owner_name text, frequency text, due_date text, status text, evidence_record text,\n            last_reviewed text, next_review_due text, notes text, created_on text, updated_on text\n        )', 'create table if not exists qms_management_reviews (\n            review_id text primary key, review_period text, chair_id text, chair_name text, review_date text,\n            inputs_summary text, decisions text, actions text, responsible_owner_id text, responsible_owner_name text,\n            due_date text, status text, created_by text, created_on text, updated_on text\n        )', 'create table if not exists qms_evidence_reviews (\n            evidence_review_id text primary key, source_module text, source_record_id text, evidence_title text,\n            reviewer_id text, reviewer_name text, decision text, comments text, reviewed_on text, created_on text\n        )', 'create table if not exists capa_register (\n            capa_id text primary key, source text, finding text, severity text, owner_id text, owner_name text,\n            due_date text, status text, corrective_action text, created_on text, updated_on text\n        )', 'create table if not exists notifications (\n            notification_id text primary key, user_id text, name text, email text, subject text, message text,\n            type text, status text, created_on text, sent_on text\n        )', 'create table if not exists audit_trail (\n            audit_id text primary key, date_time text, actor_id text, actor_name text, actor_role text,\n            action text, details text, result text\n        )', 'create table if not exists auth_sessions (\n            session_id text primary key, token_hash text unique, user_id text, created_on text,\n            last_seen text, expires_at text, revoked_on text\n        )', 'create table if not exists roles (\n            role_id text primary key, role_name text unique, description text, status text, created_on text, updated_on text\n        )', 'create table if not exists permissions (\n            permission_id text primary key, module_name text, action text, scope text, description text, status text, created_on text\n        )', 'create table if not exists role_permissions (\n            role_permission_id text primary key, role_name text, permission_id text, enabled text, created_on text, updated_on text\n        )', 'create table if not exists user_permission_overrides (\n            override_id text primary key, user_id text, permission_id text, enabled text, reason text, effective_from text, effective_to text, created_by text, created_on text\n        )', 'create table if not exists system_settings (\n            setting_key text primary key, setting_value text, setting_group text, description text, updated_by text, updated_on text\n        )', 'create table if not exists backup_records (\n            backup_id text primary key, backup_type text, started_on text, completed_on text, status text, file_name text, size_bytes integer, created_by text, notes text\n        )', 'create table if not exists recovery_requests (\n            recovery_id text primary key, restore_point text, reason text, requested_by text, requested_on text, status text, approved_by text, approved_on text, completed_on text, result text\n        )', 'create table if not exists user_assignments (\n            assignment_id text primary key, user_id text, assignment_type text, assigned_user_id text, assigned_user_name text, effective_from text, effective_to text, status text, created_by text, created_on text\n        )', 'create table if not exists departments (\n            department_id text primary key, department_name text unique, description text, head_user_id text, deputy_user_id text, status text, created_on text, updated_on text\n        )', 'create table if not exists technical_authorities (\n            authority_id text primary key, user_id text, name text, discipline text, authority_level text,\n            approval_limit text, active text, appointed_by text, appointed_on text, remarks text\n        )', 'create table if not exists competency_ncrs (\n            ncr_id text primary key, user_id text, name text, source text, scope text, ncr_type text,\n            description text, severity text, impact_on_authorization text, status text, corrective_action text,\n            raised_by text, raised_on text, closed_on text\n        )', 'create table if not exists gap_advisor_actions (\n            gap_action_id text primary key, user_id text, name text, scope text, gap_key text,\n            gap_category text, gap_title text, gap_detail text, priority text, target_module text,\n            action_type text, linked_record_id text, development_plan_id text, due_date text,\n            status text, owner_id text, owner_name text, source_snapshot text, created_by text,\n            created_on text, updated_on text, completed_on text, completion_notes text\n        )', 'create table if not exists authorization_restrictions (\n            restriction_id text primary key, authorization_id text, user_id text, name text, scope text,\n            restriction_type text, restriction_detail text, effective_date text, expiry_date text, status text,\n            imposed_by text, created_on text\n        )', 'create table if not exists client_feedback (\n            feedback_id text primary key, user_id text, name text, client_name text, project_or_vessel text,\n            job_id text, rating integer, feedback_type text, comments text, impact_on_kpi text, received_on text\n        )', 'create table if not exists probation_reviews (\n            review_id text primary key, user_id text, name text, probation_start text, probation_end text, objectives text,\n            performance_summary text, training_status text, competency_status text, tutor_assessment text, decision text,\n            decision_notes text, reviewer_id text, reviewer_name text, review_date text, status text, created_on text, updated_on text\n        )', 'create table if not exists succession_plans (\n            succession_id text primary key, user_id text, name text, current_role_name text, target_role text,\n            readiness_level text, successor_for text, development_actions text, expected_ready_date text,\n            sponsor text, status text, created_on text\n        )', 'create table if not exists workforce_forecasts (\n            forecast_id text primary key, forecast_period text, department text, role text, demand_basis text, priority text,\n            discipline text, required_headcount integer, available_headcount integer, authorized_headcount integer,\n            expiring_authorizations integer, leave_or_unavailable integer, gap integer, risk_status text, mitigation_plan text,\n            notes text, created_by text, created_by_name text, created_on text, updated_on text\n        )', 'create table if not exists accreditation_evidence (\n            evidence_id text primary key, standard text, clause text, requirement text, linked_table text,\n            linked_id text, evidence_summary text, status text, owner text, last_reviewed text\n        )', 'create table if not exists technical_interpretations (\n            interpretation_id text primary key, title text, discipline text, related_rule text, question text,\n            interpretation text, approved_by text, approval_status text, revision text, issue_date text,\n            created_on text\n        )']
    # SQLite/local-test schema for the professional Practical/Witness workflow.
    stmts.extend([
        '''create table if not exists practical_requirement_templates (
            requirement_id text primary key, requirement_code text unique, title text, description text,
            target_role text, trainee_path text, scope text, job_type text, discipline text,
            required_observations integer, criteria_json text, eligible_witness_roles text, active text,
            created_by text, created_on text, updated_on text)''',
        '''create table if not exists practical_activities (
            activity_id text primary key, requirement_id text, user_id text, name text, source_type text,
            job_id text, vessel_or_project text, job_type text, scope text, discipline text, activity_date text,
            location text, proposed_witness_id text, proposed_witness_name text, witness_authorization_id text,
            status text, notes text, created_by text, created_on text, updated_on text)''',
        '''create table if not exists practical_assessments (
            assessment_id text primary key, activity_id text, requirement_id text, user_id text, name text,
            witness_id text, witness_name text, witness_authorization_id text, witness_scope text, assessed_on text,
            criteria_scores_json text, strengths text, development_areas text, technical_observations text,
            follow_up text, outcome text, declaration_json text, status text, amendment_of text,
            created_on text, updated_on text)''',
        '''create table if not exists practical_evidence_links (
            link_id text primary key, activity_id text, user_id text, source_table text, source_record_id text,
            file_id text, evidence_type text, linked_by text, linked_on text, notes text)''',
        '''create table if not exists qualification_paths (
            path_id text primary key, path_code text unique, path_name text unique, department text,
            technical_role text, description text, active text, created_by text, created_on text, updated_on text)''',
        '''create table if not exists qualification_path_training (
            path_training_id text primary key, path_id text, training_id text, mandatory text, sequence_no integer,
            active text, created_by text, created_on text)''',
        '''create table if not exists qualification_assignments (
            qualification_assignment_id text primary key, user_id text, path_id text, trainer_id text, tutor_id text,
            status text, assigned_by text, assigned_on text, updated_on text)''',
    ])
    is_postgres = DATABASE_URL.startswith(('postgresql://','postgres://','postgresql+psycopg2://'))
    migration_result = run_pending_migrations(DATABASE_URL, Path(__file__).resolve().parents[2])
    if migration_result.get('errors'):
        logging.getLogger('psb.migrations').error('migration_errors=%s', migration_result['errors'])
    if not is_postgres:
        exec_sql("create table if not exists login_security_state (login_key text primary key, failure_count integer default 0, blocked_until text, last_failure_on text, updated_on text)")
        exec_sql("create table if not exists case_correspondence (correspondence_id text primary key, authorization_id text, actor_id text, actor_name text, actor_role text, message_type text, message text, visibility text, created_on text)")
        for col, typ in [('mfa_secret','text'),('mfa_enabled','text'),('mfa_verified_on','text')]:
            try: exec_sql(f'alter table users add column {col} {typ}')
            except Exception: pass
        for col, typ in [('size_bytes','integer'),('security_status','text'),('information_classification','text')]:
            try: exec_sql(f'alter table files add column {col} {typ}')
            except Exception: pass
        exec_sql("create table if not exists gm_watchlist (watch_id text primary key, gm_user_id text, record_type text, record_ref text, title text, risk_level text, status text, due_date text, route text, added_on text)")
        for s in stmts:
            exec_sql(s)
        # The production migration runner intentionally targets PostgreSQL only.
        # Keep the local SQLite development database aligned with the qualification
        # curriculum migrations so the Trainer workspace exercises the same tables.
        migration_dir = Path(__file__).resolve().parents[2] / 'database' / 'migrations'
        for migration_no in range(38, 46):
            for migration_file in migration_dir.glob(f'{migration_no:03d}_*.sql'):
                sql_text='\n'.join(line for line in migration_file.read_text(encoding='utf-8').splitlines() if not line.lstrip().startswith('--'))
                for statement in sql_text.split(';'):
                    statement=statement.strip()
                    if not statement or ' enable row level security' in statement.lower() or 'public.schema_migrations' in statement.lower():
                        continue
                    try:
                        exec_sql(statement)
                    except Exception:
                        # PostgreSQL-only clauses and already-applied additive changes
                        # are harmless here; each CREATE TABLE statement is independent.
                        pass
        for row in [
            ('QP-NSC','NSC-SURV','NSC Surveyor','Survey NSC','Surveyor','Qualification path for new ship construction survey personnel.'),
            ('QP-IS','IS-SURV','In-Service Surveyor','Survey Inservice','Surveyor','Qualification path for in-service survey personnel.'),
            ('QP-IND','IND-SURV','Industrial Surveyor','Survey Inservice','Industrial Surveyor','Qualification path for industrial survey personnel.'),
            ('QP-PA','PLAN-APP','Plan Appraiser','Plan Appraisal','Plan Appraiser','Qualification path for plan appraisal personnel.'),
        ]:
            try:
                exec_sql("insert or ignore into qualification_paths(path_id,path_code,path_name,department,technical_role,description,active,created_by,created_on,updated_on) values (:p,:c,:n,:d,:r,:x,'Yes','SYSTEM',:t,:t)", {'p':row[0],'c':row[1],'n':row[2],'d':row[3],'r':row[4],'x':row[5],'t':today()})
            except Exception:
                pass
        for col in [('tutor_id', 'text'), ('tutor_name', 'text'), ('trainer_id', 'text'), ('trainer_name', 'text'), ('assigner_id', 'text'), ('assigner_name', 'text'), ('employee_id', 'text'), ('phone', 'text'), ('date_joined', 'text'), ('primary_department', 'text'), ('auth_user_id', 'text'), ('account_status', 'text'), ('force_password_change', 'text'), ('created_by', 'text'), ('deactivated_on', 'text'), ('deactivation_reason', 'text')]:
            try:
                exec_sql(f'alter table users add column {col[0]} {col[1]}')
            except Exception:
                pass
        try:
            exec_sql('alter table departments add column deputy_user_id text')
        except Exception:
            pass
        try:
            exec_sql("update users set account_status = status where account_status is null or account_status = ''")
            exec_sql("update users set primary_department = department where primary_department is null or primary_department = ''")
        except Exception:
            pass
        for col in [('delivery_mode', 'text'), ('duration_hours', 'real'), ('location_or_platform', 'text'), ('capacity', 'integer'), ('enrollment_open', 'text'), ('course_version', 'text'), ('prerequisite_text', 'text'), ('assessment_required', 'text'), ('certificate_required', 'text'), ('archived_on', 'text'), ('archived_by', 'text'), ('archive_reason', 'text')]:
            try:
                exec_sql(f'alter table trainings add column {col[0]} {col[1]}')
            except Exception:
                pass
        for col in [('assigned_on', 'text'), ('assigned_by', 'text'), ('attendance_marked_on', 'text'), ('assessment_attempts', 'integer'), ('last_assessment_on', 'text'), ('certificate_id', 'text'), ('certificate_issued_on', 'text'), ('certificate_issued_by', 'text')]:
            try:
                exec_sql(f'alter table training_records add column {col[0]} {col[1]}')
            except Exception:
                pass
        for col in [('scheduled_date', 'text'), ('scheduled_time', 'text'), ('assessor_id', 'text'), ('assessor_name', 'text'), ('evidence_file_id', 'text'), ('evidence_status', 'text'), ('verification_status', 'text'), ('verified_by', 'text'), ('verified_on', 'text'), ('verification_notes', 'text'), ('overall_score', 'real')]:
            for table_name in ['witness_surveys', 'supervised_activities']:
                try:
                    exec_sql(f'alter table {table_name} add column {col[0]} {col[1]}')
                except Exception:
                    pass
        try:
            exec_sql('create index if not exists witness_surveys_user_scope_idx on witness_surveys(user_id, scope)')
            exec_sql('create index if not exists witness_surveys_status_idx on witness_surveys(verification_status, outcome)')
            exec_sql('create index if not exists supervised_user_scope_idx on supervised_activities(user_id, scope)')
            exec_sql('create index if not exists supervised_status_idx on supervised_activities(verification_status, outcome)')
        except Exception:
            pass
        for col in [('source_record_id', 'text'), ('category', 'text'), ('incident_date', 'text'), ('likelihood', 'integer'), ('risk_score', 'integer'), ('priority', 'text'), ('owner_id', 'text'), ('owner_name', 'text'), ('containment_action', 'text'), ('root_cause', 'text'), ('corrective_action_owner_id', 'text'), ('corrective_action_owner_name', 'text'), ('due_date', 'text'), ('verification_status', 'text'), ('verified_by', 'text'), ('verified_on', 'text'), ('effectiveness_check', 'text'), ('effectiveness_notes', 'text'), ('closure_notes', 'text'), ('closed_by', 'text'), ('linked_development_plan_id', 'text'), ('linked_gap_action_id', 'text'), ('updated_on', 'text')]:
            try:
                exec_sql(f'alter table competency_ncrs add column {col[0]} {col[1]}')
            except Exception:
                pass
        try:
            exec_sql('create index if not exists competency_ncrs_status_due_idx on competency_ncrs(status, due_date)')
            exec_sql('create index if not exists competency_ncrs_source_idx on competency_ncrs(source, source_record_id)')
            exec_sql('create index if not exists competency_ncrs_user_scope_idx on competency_ncrs(user_id, scope)')
            exec_sql('create index if not exists competency_ncrs_priority_idx on competency_ncrs(priority, severity)')
        except Exception:
            pass
        for col in [('plan_group_id', 'text'), ('plan_title', 'text'), ('objective', 'text'), ('development_type', 'text'), ('priority', 'text'), ('owner_id', 'text'), ('owner_name', 'text'), ('progress_percent', 'integer'), ('evidence_required', 'text'), ('evidence_status', 'text'), ('review_date', 'text'), ('completed_on', 'text'), ('source_gap', 'text'), ('success_criteria', 'text'), ('updated_by', 'text')]:
            try:
                exec_sql(f'alter table development_plans add column {col[0]} {col[1]}')
            except Exception:
                pass
        try:
            exec_sql('create table if not exists user_departments (user_department_id text primary key, user_id text, department text, is_primary text, effective_from text, effective_to text, status text, created_on text)')
            exec_sql('alter table user_departments add column is_primary text')
            exec_sql('alter table user_departments add column effective_from text')
            exec_sql('alter table user_departments add column effective_to text')
            exec_sql('alter table user_departments add column status text')
        except Exception:
            pass
        for col, typ in [('employee_id', 'text'), ('primary_department', 'text'), ('account_status', 'text'), ('force_password_change', 'text'), ('password_changed_on', 'text'), ('deactivated_on', 'text'), ('deactivation_reason', 'text')]:
            try:
                exec_sql(f'alter table users add column {col} {typ}')
            except Exception:
                pass
        try:
            exec_sql('create index if not exists users_employee_id_idx on users(employee_id)')
            exec_sql('create index if not exists users_primary_department_idx on users(primary_department)')
        except Exception:
            pass
        for col in [('entity_type', 'text'), ('entity_id', 'text'), ('reason', 'text'), ('before_value', 'text'), ('after_value', 'text'), ('session_id', 'text')]:
            try:
                exec_sql(f'alter table audit_trail add column {col[0]} {col[1]}')
            except Exception:
                pass
        ensure_indexes()
        _ensure_authorization_schema_compat()
        _ensure_knowledge_schema_compat()
    else:
        # PostgreSQL schema changes are migration-only. No startup DDL is executed here.
        logging.getLogger('psb.migrations').info('postgres_schema_mode=migrations_only')
    if db_all('users').empty:
        seed_demo()
    else:
        # Permission baselines are additive and must also be applied to existing
        # databases; demo seeding intentionally returns early once users exist.
        try:
            _runtime._ensure_role_permission_baseline()
        except Exception:
            logging.getLogger('psb.permissions').exception('role_permission_baseline_update_failed')
def ensure_indexes() -> None:
    """Create common PostgreSQL/Supabase indexes used by dashboards and trainee pages."""
    for col, typ in [('activity_date', 'text'), ('description', 'text'), ('learning_outcome', 'text'), ('evidence_status', 'text'), ('verified_by', 'text'), ('verified_on', 'text'), ('verification_notes', 'text'), ('development_plan_id', 'text'), ('source_type', 'text')]:
        try:
            exec_sql(f'alter table cpd_records add column {col} {typ}')
        except Exception:
            pass
    indexes = ['create index if not exists users_login_id_idx on users(login_id)', 'create index if not exists auth_sessions_token_idx on auth_sessions(token_hash)', 'create index if not exists auth_sessions_user_idx on auth_sessions(user_id, revoked_on, expires_at)', 'create index if not exists users_email_idx on users(email)', 'create index if not exists trainings_trainer_id_idx on trainings(trainer_id)', 'create index if not exists trainings_status_idx on trainings(status)', 'create index if not exists training_records_user_id_idx on training_records(user_id)', 'create index if not exists training_records_training_id_idx on training_records(training_id)', 'create index if not exists training_records_user_training_idx on training_records(user_id, training_id)', 'create index if not exists files_owner_user_id_idx on files(owner_user_id)', 'create index if not exists user_departments_user_id_idx on user_departments(user_id)', 'create index if not exists user_departments_department_idx on user_departments(department)', 'create index if not exists files_linked_idx on files(linked_table, linked_id)', 'create index if not exists notifications_user_id_idx on notifications(user_id)', 'create index if not exists question_bank_training_id_idx on question_bank(training_id)', 'create index if not exists assessment_history_user_training_idx on assessment_history(user_id, training_id)', 'create index if not exists competency_matrix_user_id_idx on competency_matrix(user_id)', 'create index if not exists authorization_requests_user_id_idx on authorization_requests(user_id)', 'create index if not exists job_requests_assigned_user_id_idx on job_requests(assigned_user_id)', 'create index if not exists kpi_records_user_id_idx on kpi_records(user_id)', 'create index if not exists kpi_snapshots_user_period_idx on kpi_snapshots(user_id, period)', 'create index if not exists kpi_snapshots_status_idx on kpi_snapshots(status)', 'create index if not exists development_plans_user_id_idx on development_plans(user_id)', 'create index if not exists development_plans_owner_id_idx on development_plans(owner_id)', 'create index if not exists development_plans_status_idx on development_plans(status)', 'create index if not exists cpd_records_user_id_idx on cpd_records(user_id)', 'create index if not exists audit_trail_actor_idx on audit_trail(actor_id)', 'create index if not exists audit_trail_entity_idx on audit_trail(entity_type, entity_id)', 'create index if not exists role_permissions_role_idx on role_permissions(role_name)', 'create index if not exists user_permission_overrides_user_idx on user_permission_overrides(user_id)', 'create index if not exists system_settings_group_idx on system_settings(setting_group)', 'create index if not exists backup_records_status_idx on backup_records(status)', 'create index if not exists recovery_requests_status_idx on recovery_requests(status)', 'create index if not exists user_assignments_user_idx on user_assignments(user_id)', 'create index if not exists qms_audits_status_idx on qms_audits(status, planned_date)', 'create index if not exists qms_audits_department_idx on qms_audits(department)', 'create index if not exists qms_compliance_status_idx on qms_compliance_items(status, next_review_due)', 'create index if not exists qms_compliance_owner_idx on qms_compliance_items(owner_department)', 'create index if not exists qms_management_reviews_status_idx on qms_management_reviews(status, review_date)', 'create index if not exists qms_evidence_source_idx on qms_evidence_reviews(source_module, source_record_id)']
    for idx in indexes:
        try:
            exec_sql(idx)
        except Exception:
            pass
def _ensure_authorization_schema_compat():
    """Additive migrations for the unified authorization lifecycle."""
    stmts = ['alter table authorization_requests add column if not exists application_reason text', 'alter table authorization_requests add column if not exists requested_by text', 'alter table authorization_requests add column if not exists requested_on text', 'alter table authorization_requests add column if not exists current_stage text', 'alter table authorization_requests add column if not exists risk_category text', 'alter table authorization_requests add column if not exists validity_months integer', 'alter table authorization_requests add column if not exists decision_date text', 'alter table authorization_requests add column if not exists rejection_reason text', 'alter table authorization_requests add column if not exists withdrawn_on text', 'alter table authorization_requests add column if not exists withdrawn_reason text', 'alter table authorization_requests add column if not exists last_reviewed_on text', 'alter table authorization_requests add column if not exists updated_by text', 'alter table authorization_requests add column if not exists certificate_status text', 'alter table authorization_certificates add column if not exists revoked_on text', 'alter table authorization_certificates add column if not exists revocation_reason text', 'alter table authorization_certificates add column if not exists public_status text', 'alter table authorization_restrictions add column if not exists reason text', 'alter table authorization_restrictions add column if not exists revoked_on text', 'alter table authorization_restrictions add column if not exists revoked_by text', 'alter table authorization_restrictions add column if not exists revoked_reason text', 'alter table technical_authorities add column if not exists effective_from text', 'alter table technical_authorities add column if not exists effective_to text', 'alter table technical_authorities add column if not exists decision_scope text', 'alter table annual_reviews add column if not exists training_summary text', 'alter table annual_reviews add column if not exists competency_summary text', 'alter table annual_reviews add column if not exists authorization_summary text', 'alter table annual_reviews add column if not exists ncr_summary text', 'alter table annual_reviews add column if not exists cpd_summary text', 'alter table annual_reviews add column if not exists client_feedback_summary text', 'alter table revalidation_requests add column if not exists initiated_on text', 'alter table revalidation_requests add column if not exists initiated_by text', 'alter table revalidation_requests add column if not exists readiness_status text', 'alter table revalidation_requests add column if not exists evidence_snapshot text', 'alter table revalidation_requests add column if not exists decision text', 'alter table revalidation_requests add column if not exists decision_reason text', 'alter table revalidation_requests add column if not exists decided_by text', 'alter table revalidation_requests add column if not exists decided_on text', 'create table if not exists authorization_events (event_id text primary key, authorization_id text, user_id text, event_type text, from_status text, to_status text, actor_id text, actor_name text, reason text, created_on text)', 'create index if not exists authorization_events_auth_idx on authorization_events(authorization_id, created_on)', 'create index if not exists authorization_requests_status_idx on authorization_requests(status)', 'create index if not exists authorization_requests_scope_idx on authorization_requests(scope, job_type)', 'create index if not exists authorization_restrictions_user_status_idx on authorization_restrictions(user_id, status)', 'create index if not exists revalidation_requests_user_status_idx on revalidation_requests(user_id, final_status)', 'create index if not exists annual_reviews_user_year_idx on annual_reviews(user_id, review_year)', 'create index if not exists technical_authorities_user_active_idx on technical_authorities(user_id, active)']
    for sql in stmts:
        try:
            exec_sql(sql)
        except Exception:
            pass
    try:
        exec_sql("update authorization_requests set current_stage = case when status='Department Recommended' then 'CRB Review' when status='CRB Review' then 'CRB Review' when status='CRB Recommended' then 'Final Authorization Decision' when status='Management Approved' then 'Authorized' when status in ('CRB Rejected','CRB Deferred','Returned for Clarification','Deferred','Rejected') then 'Decision / Clarification' else coalesce(current_stage,'Draft') end where current_stage is null or current_stage=''")
    except Exception:
        pass
def _ensure_knowledge_schema_compat():
    """Additive knowledge-library migrations for older deployments."""
    stmts = ['alter table knowledge_library add column if not exists summary text', 'alter table knowledge_library add column if not exists effective_from text', 'alter table knowledge_library add column if not exists review_due_date text', 'alter table knowledge_library add column if not exists status text', 'alter table knowledge_library add column if not exists audience text', 'alter table knowledge_library add column if not exists owner_name text', 'alter table knowledge_library add column if not exists approved_by text', 'alter table knowledge_library add column if not exists approved_on text', 'alter table knowledge_library add column if not exists supersedes_id text', 'alter table knowledge_library add column if not exists keywords text', 'alter table knowledge_library add column if not exists updated_on text', 'create table if not exists knowledge_versions (version_id text primary key, knowledge_id text, version_no text, revision_date text, change_summary text, file_link text, uploaded_by text, approved_by text, status text, created_on text)', 'create index if not exists knowledge_versions_knowledge_idx on knowledge_versions(knowledge_id)', "update knowledge_library set status = coalesce(nullif(status, ''), 'Published') where status is null or status = ''", "update knowledge_library set audience = coalesce(nullif(audience, ''), 'All technical staff') where audience is null or audience = ''", "update knowledge_library set updated_on = coalesce(nullif(updated_on, ''), created_on) where updated_on is null or updated_on = ''"]
    for sql in stmts:
        try:
            exec_sql(sql)
        except Exception:
            pass
def ensure_client_feedback_schema() -> None:
    """Additive migration for the closed-loop client feedback workflow."""
    stmts = ['alter table client_feedback add column if not exists feedback_channel text', 'alter table client_feedback add column if not exists contact_person text', 'alter table client_feedback add column if not exists source_reference text', 'alter table client_feedback add column if not exists service_area text', 'alter table client_feedback add column if not exists scope text', 'alter table client_feedback add column if not exists severity text', 'alter table client_feedback add column if not exists sentiment text', 'alter table client_feedback add column if not exists confidentiality text', 'alter table client_feedback add column if not exists response_due text', 'alter table client_feedback add column if not exists owner_id text', 'alter table client_feedback add column if not exists owner_name text', 'alter table client_feedback add column if not exists response_text text', 'alter table client_feedback add column if not exists action_required text', 'alter table client_feedback add column if not exists linked_ncr_id text', 'alter table client_feedback add column if not exists linked_job_id text', 'alter table client_feedback add column if not exists submitted_by text', 'alter table client_feedback add column if not exists submitted_by_name text', 'alter table client_feedback add column if not exists status text', 'alter table client_feedback add column if not exists created_on text', 'alter table client_feedback add column if not exists updated_on text', 'alter table client_feedback add column if not exists resolved_on text', 'alter table client_feedback add column if not exists resolution_notes text', 'create index if not exists client_feedback_user_idx on client_feedback(user_id, received_on)', 'create index if not exists client_feedback_status_idx on client_feedback(status, action_required)', 'create index if not exists client_feedback_job_idx on client_feedback(linked_job_id)', 'create index if not exists client_feedback_ncr_idx on client_feedback(linked_ncr_id)', "update client_feedback set status=coalesce(nullif(status,''),'New') where status is null or status=''", "update client_feedback set action_required=coalesce(nullif(action_required,''), case when feedback_type in ('Complaint','Technical Concern') then 'Yes' else 'No' end) where action_required is null or action_required=''", "update client_feedback set created_on=coalesce(nullif(created_on,''), received_on) where created_on is null or created_on=''", "update client_feedback set updated_on=coalesce(nullif(updated_on,''), created_on) where updated_on is null or updated_on=''"]
    for sql in stmts:
        try:
            exec_sql(sql)
        except Exception:
            pass
@st.cache_resource(show_spinner=False)
def ensure_accreditation_schema() -> None:
    stmts = ['create table if not exists accreditation_assessments (assessment_id text primary key, standard text, assessment_period text, overall_score numeric, readiness_status text, assessed_on text, assessed_by text, approved_by text, approval_status text, executive_summary text, created_on text, updated_on text)', 'create table if not exists accreditation_evidence (evidence_id text primary key, standard text, clause text, requirement text, linked_table text, linked_id text, evidence_summary text, status text, owner text, last_reviewed text, evidence_type text, severity text, due_date text, verified_by text, verified_on text, assessment_id text, source_module text, created_on text, updated_on text)', 'create index if not exists accreditation_assessments_standard_idx on accreditation_assessments(standard, assessment_period)', 'create index if not exists accreditation_evidence_assessment_idx on accreditation_evidence(assessment_id, status)', 'create index if not exists accreditation_evidence_due_idx on accreditation_evidence(due_date, status)']
    for sql in stmts:
        try:
            exec_sql(sql)
        except Exception:
            pass
    for col, typ in [('evidence_type', 'text'), ('severity', 'text'), ('due_date', 'text'), ('verified_by', 'text'), ('verified_on', 'text'), ('assessment_id', 'text'), ('source_module', 'text'), ('created_on', 'text'), ('updated_on', 'text')]:
        try:
            exec_sql(f'alter table accreditation_evidence add column if not exists {col} {typ}')
        except Exception:
            pass
def ensure_interpretation_schema() -> None:
    """Ensure the Interpretation / Rule Development workflow has its own governed schema."""
    statements = ['create table if not exists interpretation_reviews (\n            review_id text primary key, interpretation_id text, reviewer_id text, reviewer_name text,\n            stage text, decision text, comments text, reviewed_on text, created_on text\n        )', 'create table if not exists rule_change_requests (\n            change_id text primary key, title text, related_rule text, change_type text, reason text,\n            impact_summary text, affected_departments text, affected_modules text, priority text,\n            owner_id text, owner_name text, status text, proposed_revision text, effective_date text,\n            source_interpretation_id text, approved_by text, approved_on text, created_by text,\n            created_on text, updated_on text\n        )', 'create index if not exists interpretation_reviews_interp_idx on interpretation_reviews(interpretation_id, reviewed_on)', 'create index if not exists rule_change_status_idx on rule_change_requests(status, priority)']
    for sql in statements:
        try:
            exec_sql(sql)
        except Exception:
            pass
    for col, typ in [('requester_id', 'text'), ('requester_name', 'text'), ('submitted_on', 'text'), ('review_due_date', 'text'), ('status', 'text'), ('priority', 'text'), ('rule_family', 'text'), ('effective_date', 'text'), ('impact_summary', 'text'), ('affected_departments', 'text'), ('affected_modules', 'text'), ('published_knowledge_id', 'text'), ('approval_date', 'text'), ('updated_on', 'text'), ('withdrawn_on', 'text'), ('withdrawal_reason', 'text')]:
        try:
            exec_sql(f'alter table technical_interpretations add column if not exists {col} {typ}')
        except Exception:
            pass
    try:
        exec_sql('create index if not exists technical_interp_status_idx on technical_interpretations(approval_status, discipline)')
    except Exception:
        pass
    try:
        exec_sql('alter table knowledge_library add column if not exists source_interpretation_id text')
    except Exception:
        pass
def seed_demo() -> None:
    if not db_all('users').empty:
        return
    if INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_LOGIN and INITIAL_ADMIN_PASSWORD:
        db_insert('users', {'user_id': 'USR-INITIAL-ADMIN', 'name': INITIAL_ADMIN_NAME, 'role': 'Admin', 'trainee_path': '', 'department': 'Administration', 'primary_department': 'Administration', 'assigned_duty': 'System Administration', 'email': INITIAL_ADMIN_EMAIL, 'login_id': INITIAL_ADMIN_LOGIN, 'password_hash': phash(INITIAL_ADMIN_PASSWORD), 'status': 'Active', 'account_status': 'Active', 'force_password_change': 'No', 'availability': 'Available', 'current_location': '', 'created_on': today(), 'last_login': '', 'password_changed_on': today()})
    elif not ENABLE_DEMO_SEED:
        return
    demo_users = [('USR-GM', 'Global Manager', 'GM', '', 'Management', 'Executive Governance', 'gm@psbureau.org', 'gm', '', '', ''), ('USR-ADMIN', 'PSB Admin', 'Admin', '', 'Administration', 'System Control', 'admin@psbureau.org', 'admin', '', '', ''), ('USR-MGMT', 'Management User', 'Management', '', 'Management', 'Oversight', 'management@psbureau.org', 'management', '', '', ''), ('USR-TRAINER', 'Training Officer', 'Trainer', '', 'Training', 'Qualification Path Training, Mentoring and Development', 'trainer@psbureau.org', 'trainer', '', '', ''), ('USR-DEPT-MGR', 'NSC Department Manager', 'Department Manager', '', 'Survey NSC', 'Department Qualification Governance', 'deptmanager@psbureau.org', 'deptmanager', '', '', ''), ('USR-QMR', 'QMS Representative', 'QMR', '', 'QMS', 'QMS Review', 'qmr@psbureau.org', 'qmr', '', '', ''), ('USR-SURVEYOR', 'Sample NSC Trainee', 'Trainee', 'NSC Surveyor', 'Survey NSC', 'NSC Surveyor Path', 'surveyor@psbureau.org', 'surveyor', '', 'USR-TRAINER', 'Training Officer'), ('USR-APPRAISER', 'Sample Plan Appraisal Trainee', 'Trainee', 'Plan Appraiser', 'Plan Appraisal', 'Plan Appraiser Path', 'appraiser@psbureau.org', 'appraiser', '', 'USR-TRAINER', 'Training Officer')]
    if not ENABLE_DEMO_SEED or (INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_LOGIN and INITIAL_ADMIN_PASSWORD):
        demo_users = []
    elif not DEMO_PASSWORD:
        st.warning('ENABLE_DEMO_SEED is enabled but DEMO_PASSWORD is not configured. Demo users were not created.')
        demo_users = []
    for u in demo_users:
        password = DEMO_PASSWORD if DEMO_PASSWORD else temp_password(16)
        db_insert('users', {'user_id': u[0], 'name': u[1], 'role': u[2], 'trainee_path': u[3], 'department': u[4], 'primary_department': u[4].split(',')[0].strip(), 'assigned_duty': u[5], 'email': u[6], 'login_id': u[7], 'password_hash': phash(password), 'status': 'Active', 'account_status': 'Active', 'force_password_change': 'No', 'availability': 'Available', 'current_location': 'Karachi', 'mentor_id': u[9], 'mentor_name': u[10], 'tutor_id': u[9], 'tutor_name': u[10], 'competency_level': 'Level 0 - Trainee', 'created_on': today(), 'last_login': '', 'password_changed_on': today()})
    existing_roles = db_all('roles')
    existing_role_names = set(existing_roles['role_name'].astype(str)) if (not existing_roles.empty and 'role_name' in existing_roles.columns) else set()
    for role_name in ROLES:
        if role_name not in existing_role_names:
            db_insert('roles', {'role_id': uid('ROLE'), 'role_name': role_name, 'description': DEFAULT_ROLE_DESCRIPTIONS.get(role_name, ''), 'status': 'Active', 'created_on': today(), 'updated_on': now()})
    perms_existing = db_all('permissions')
    for module_name in PERMISSION_MODULES:
        for action_name in PERMISSION_ACTIONS:
            for scope_name in PERMISSION_SCOPES:
                exists = perms_existing[(perms_existing['module_name'].astype(str) == module_name) & (perms_existing['action'].astype(str) == action_name) & (perms_existing['scope'].astype(str) == scope_name)] if not perms_existing.empty else pd.DataFrame()
                if exists.empty:
                    db_insert('permissions', {'permission_id': uid('PERM'), 'module_name': module_name, 'action': action_name, 'scope': scope_name, 'description': f'{action_name} {module_name} at {scope_name} scope', 'status': 'Active', 'created_on': today()})
    if db_all('system_settings').empty:
        defaults = [('organization_name', 'Pakistan Shipping Bureau', 'General', 'Organization display name'), ('timezone', 'Asia/Karachi', 'General', 'Application timezone'), ('date_format', 'DD-MMM-YYYY', 'General', 'Display date format'), ('session_timeout_minutes', '60', 'Security', 'Inactive session timeout'), ('max_login_attempts', str(MAX_LOGIN_ATTEMPTS), 'Security', 'Maximum failed login attempts'), ('login_block_minutes', str(LOGIN_BLOCK_MINUTES), 'Security', 'Account/login block duration'), ('minimum_password_length', '12', 'Security', 'Minimum password length'), ('password_expiry_days', '90', 'Security', 'Password expiry interval'), ('require_2fa', 'No', 'Security', 'Require two-factor authentication'), ('email_notifications_enabled', 'Yes', 'Notifications', 'Enable email notifications'), ('in_app_notifications_enabled', 'Yes', 'Notifications', 'Enable in-app notifications'), ('training_notifications_enabled', 'Yes', 'Notifications', 'Enable training reminders'), ('authorization_notifications_enabled', 'Yes', 'Notifications', 'Enable authorization expiry reminders'), ('ncr_notifications_enabled', 'Yes', 'Notifications', 'Enable NCR due reminders'), ('revalidation_notifications_enabled', 'Yes', 'Notifications', 'Enable revalidation reminders'), ('training_reminder_days', '30', 'Workflow', 'Training due reminder lead time'), ('authorization_reminder_days', '90', 'Workflow', 'Authorization expiry reminder lead time'), ('revalidation_reminder_days', '90', 'Workflow', 'Revalidation reminder lead time'), ('ncr_reminder_days', '7', 'Workflow', 'NCR due reminder lead time'), ('scheduler_enabled', 'Yes', 'Scheduler', 'Enable scheduled notifications/jobs'), ('scheduler_last_tick', 'Not recorded', 'Scheduler', 'Last successful scheduler tick'), ('scheduler_next_tick', 'Not recorded', 'Scheduler', 'Next expected scheduler tick'), ('default_language', 'English', 'General', 'Default application language')]
        for key, value, group, desc in defaults:
            db_insert('system_settings', {'setting_key': key, 'setting_value': value, 'setting_group': group, 'description': desc, 'updated_by': 'System', 'updated_on': now()})
    if db_all('role_permissions').empty:
        baseline = {
            'Admin': {'Administration': {'View','Create','Edit','Manage','Export'}},
            'Trainer': {'Training': {'View','Create','Edit','Assign','Review'}, 'Development Plans': {'View','Create','Edit'}, 'Competency': {'View'}, 'Practical / Witness': {'View'}},
            'Department Manager': {'Training': {'View'}, 'Competency': {'View','Review'}, 'Practical / Witness': {'View','Review'}, 'Authorization': {'View','Review'}},
            'Management': {'Dashboard': {'View'}, 'Authorization': {'View','Review','Approve'}},
        }
        perms = db_all('permissions')
        for role_name, modules in baseline.items():
            for module_name, actions in modules.items():
                for action_name in actions:
                    matches = perms[(perms['module_name'] == module_name) & (perms['action'] == action_name) & (perms['scope'] == 'Organization-wide')]
                    if not matches.empty:
                        db_insert('role_permissions', {'role_permission_id': uid('RPERM'), 'role_name': role_name, 'permission_id': matches.iloc[0]['permission_id'], 'enabled': 'Yes', 'created_on': now(), 'updated_on': now()})
    _runtime._ensure_role_permission_baseline()
    for module in CORE_THEORETICAL_MODULES:
        db_insert('training_modules', {'module_id': module[0], 'title': module[1], 'module_group': module[3], 'target_path': module[2], 'mandatory': 'Yes', 'refresher_required': 'Yes', 'cpd_hours': module[4], 'validity_months': 36, 'added_by': 'System', 'created_on': today()})
    for row in DEFAULT_AUTH_MATRIX:
        db_insert('authorization_matrix', {'matrix_id': uid('MATRIX'), 'scope': row[0], 'job_type': row[1], 'required_witness_count': row[2], 'required_supervised_count': row[3], 'required_joint_plan_count': row[4], 'required_independent_plan_count': row[5], 'required_level_for_auth': f'Level {row[6]} - Authorized' if row[6] == 3 else f'Level {row[6]} - Senior Authorized', 'minimum_job_level': f'Level {row[7]} - Authorized' if row[7] == 3 else f'Level {row[7]} - Senior Authorized', 'risk_category': row[8], 'validity_months': row[9], 'active': 'Yes'})
    for rule in [('RULE-IMO-RO', 'IMO Recognized Organization Code', 'IMO RO Code', 'Current', 'Statutory', 'https://www.imo.org'), ('RULE-ISO9001', 'Quality Management System Requirements', 'ISO 9001', '2015', 'QMS', 'https://www.iso.org'), ('RULE-ISO17020', 'Inspection Body Competence Requirements', 'ISO/IEC 17020', '2012', 'Inspection', 'https://www.iso.org'), ('RULE-IACS-PR7', 'IACS Training and Qualification Principles', 'IACS PR7', 'Current', 'Competency', 'https://iacs.org.uk')]:
        db_insert('rule_library', {'rule_id': rule[0], 'title': rule[1], 'standard': rule[2], 'revision': rule[3], 'category': rule[4], 'link': rule[5], 'mandatory': 'Yes', 'current_version_id': '', 'created_on': today(), 'updated_on': today()})
    audit('Database Seeded', 'World-class PSB HRDM data seeded', actor={'name': 'System', 'role': 'System'})
