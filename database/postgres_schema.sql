-- PostgreSQL schema for Pakistan Shipping Bureau HRDM Training System
-- This schema reflects the application tables and recommended indexes.

set search_path = public;

-- Core user and training tables
create table if not exists users (
    user_id text primary key,
    employee_id text unique,
    phone text,
    date_joined text,
    name text,
    role text,
    trainee_path text,
    department text,
    primary_department text,
    assigned_duty text,
    email text unique,
    login_id text unique,
    password_hash text,
    auth_user_id text unique,
    status text,
    account_status text,
    force_password_change text,
    created_by text,
    deactivated_on text,
    deactivation_reason text,
    availability text,
    current_location text,
    mentor_id text,
    mentor_name text,
    tutor_id text,
    tutor_name text,
    trainer_id text,
    trainer_name text,
    assigner_id text,
    assigner_name text,
    competency_level text,
    created_on text,
    last_login text
);

create table if not exists user_departments (
    user_department_id text primary key,
    user_id text not null references users(user_id) on delete cascade,
    department text not null,
    is_primary text,
    effective_from text,
    effective_to text,
    status text default 'Active',
    created_on text
);

create table if not exists training_modules (
    module_id text primary key,
    title text,
    module_group text,
    target_path text,
    mandatory text,
    refresher_required text,
    cpd_hours real,
    validity_months integer,
    added_by text,
    created_on text
);

create table if not exists trainings (
    training_id text primary key,
    module_id text,
    title text,
    category text,
    standards text,
    target_roles text,
    target_paths text,
    trainer_id text,
    trainer_name text,
    slides_link text,
    video_link text,
    reference_link text,
    scorm_package_link text,
    lms_course_id text,
    schedule_date text,
    schedule_time text,
    meeting_link text,
    recording_link text,
    passing_marks integer,
    validity_months integer,
    max_attempts integer,
    retest_wait_days integer,
    delivery_mode text,
    duration_hours real,
    location_or_platform text,
    capacity integer,
    enrollment_open text,
    course_version text,
    prerequisite_text text,
    assessment_required text,
    certificate_required text,
    archived_on text,
    archived_by text,
    archive_reason text,
    status text,
    created_on text,
    updated_on text,
    foreign key (module_id) references training_modules(module_id),
    foreign key (trainer_id) references users(user_id)
);

create table if not exists files (
    file_id text primary key,
    owner_user_id text,
    owner_name text,
    linked_table text,
    linked_id text,
    category text,
    file_name text,
    file_ext text,
    mime_type text,
    storage_provider text,
    storage_path text,
    public_url text,
    extracted_text text,
    ocr_status text,
    review_status text,
    created_on text,
    updated_on text,
    foreign key (owner_user_id) references users(user_id)
);

create table if not exists training_records (
    record_id text primary key,
    user_id text,
    name text,
    role text,
    trainee_path text,
    training_id text,
    training_title text,
    status text,
    slides_opened text,
    video_opened text,
    live_attendance text,
    recording_opened text,
    lms_completed text,
    test_status text,
    score real,
    passing_marks integer,
    certificate_status text,
    certificate_link text,
    due_date text,
    completed_on text,
    progress integer,
    remarks text,
    updated_on text,
    assigned_on text,
    assigned_by text,
    attendance_marked_on text,
    assessment_attempts integer,
    last_assessment_on text,
    certificate_id text,
    certificate_issued_on text,
    certificate_issued_by text,
    foreign key (user_id) references users(user_id),
    foreign key (training_id) references trainings(training_id)
);

create table if not exists question_bank (
    question_id text primary key,
    training_id text,
    question text,
    option_a text,
    option_b text,
    option_c text,
    option_d text,
    correct_answer text,
    marks integer,
    generated_on text,
    foreign key (training_id) references trainings(training_id)
);

create table if not exists assessment_history (
    assessment_id text primary key,
    user_id text,
    name text,
    training_id text,
    training_title text,
    attempt_no integer,
    score real,
    result text,
    attempted_on text,
    next_retest_allowed text,
    remarks text,
    foreign key (user_id) references users(user_id),
    foreign key (training_id) references trainings(training_id)
);

create table if not exists competency_matrix (
    competency_id text primary key,
    user_id text,
    name text,
    role text,
    trainee_path text,
    area text,
    competency_level text,
    scope text,
    job_type text,
    required_training_ids text,
    required_witness_count integer,
    required_supervised_count integer,
    required_joint_plan_count integer,
    required_independent_plan_count integer,
    required_level_for_auth text,
    status text,
    expiry_date text,
    evidence text,
    created_on text,
    updated_on text,
    foreign key (user_id) references users(user_id)
);

create table if not exists authorization_matrix (
    matrix_id text primary key,
    scope text,
    job_type text,
    required_witness_count integer,
    required_supervised_count integer,
    required_joint_plan_count integer,
    required_independent_plan_count integer,
    required_level_for_auth text,
    minimum_job_level text,
    risk_category text,
    validity_months integer,
    active text
);

create table if not exists development_plans (
    plan_id text primary key,
    user_id text,
    name text,
    trainee_path text,
    mentor_id text,
    mentor_name text,
    competency_scope text,
    month_no integer,
    activity text,
    target_date text,
    status text,
    mentor_comments text,
    created_on text,
    updated_on text,
    foreign key (user_id) references users(user_id),
    foreign key (mentor_id) references users(user_id)
);

create table if not exists witness_surveys (
    witness_id text primary key,
    user_id text,
    name text,
    trainee_path text,
    tutor_id text,
    tutor_name text,
    vessel_or_project text,
    job_type text,
    scope text,
    witness_date text,
    location text,
    technical_knowledge integer,
    rule_application integer,
    safety_awareness integer,
    communication integer,
    report_quality integer,
    professional_conduct integer,
    outcome text,
    comments text,
    status text,
    created_on text,
    updated_on text,
    foreign key (user_id) references users(user_id),
    foreign key (tutor_id) references users(user_id)
);

create table if not exists supervised_activities (
    supervised_id text primary key,
    user_id text,
    name text,
    trainee_path text,
    tutor_id text,
    tutor_name text,
    activity_kind text,
    vessel_or_project text,
    job_type text,
    scope text,
    activity_date text,
    location text,
    preparation integer,
    execution_quality integer,
    findings_quality integer,
    reporting_quality integer,
    rule_compliance integer,
    outcome text,
    comments text,
    status text,
    created_on text,
    updated_on text,
    foreign key (user_id) references users(user_id),
    foreign key (tutor_id) references users(user_id)
);

create table if not exists authorization_requests (
    authorization_id text primary key,
    user_id text,
    name text,
    trainee_path text,
    job_type text,
    scope text,
    competency_id text,
    status text,
    tutor_remarks text,
    tutor_signature text,
    tutor_signed_on text,
    principal_remarks text,
    principal_signature text,
    principal_signed_on text,
    technical_remarks text,
    technical_signature text,
    technical_signed_on text,
    qms_remarks text,
    qms_signature text,
    qms_signed_on text,
    crb_decision text,
    crb_remarks text,
    management_remarks text,
    management_signature text,
    management_signed_on text,
    expiry_date text,
    certificate_id text,
    certificate_html text,
    certificate_storage_link text,
    qr_data_uri text,
    created_on text,
    updated_on text,
    foreign key (user_id) references users(user_id),
    foreign key (competency_id) references competency_matrix(competency_id)
);

create table if not exists authorization_certificates (
    certificate_id text primary key,
    authorization_id text,
    user_id text,
    name text,
    scope text,
    job_type text,
    issue_date text,
    expiry_date text,
    certificate_html text,
    qr_data_uri text,
    storage_link text,
    verification_url text,
    status text,
    created_on text,
    foreign key (authorization_id) references authorization_requests(authorization_id),
    foreign key (user_id) references users(user_id)
);

create table if not exists crb_reviews (
    crb_id text primary key,
    authorization_id text,
    user_id text,
    name text,
    scope text,
    review_date text,
    tutor_decision text,
    technical_decision text,
    qmr_decision text,
    management_decision text,
    final_decision text,
    remarks text,
    signed_by text,
    crb_member_id text,
    created_on text,
    foreign key (authorization_id) references authorization_requests(authorization_id),
    foreign key (user_id) references users(user_id)
);

create table if not exists annual_reviews (
    review_id text primary key,
    user_id text,
    name text,
    scope text,
    review_year integer,
    training_status text,
    kpi_status text,
    complaint_status text,
    capa_status text,
    decision text,
    reviewer text,
    review_date text,
    remarks text,
    foreign key (user_id) references users(user_id)
);

create table if not exists revalidation_requests (
    revalidation_id text primary key,
    authorization_id text,
    user_id text,
    name text,
    scope text,
    refresher_training_status text,
    annual_review_status text,
    kpi_review_status text,
    tutor_confirmation text,
    crb_status text,
    final_status text,
    due_date text,
    created_on text,
    updated_on text,
    foreign key (authorization_id) references authorization_requests(authorization_id),
    foreign key (user_id) references users(user_id)
);

create table if not exists job_requests (
    job_id text primary key,
    job_title text,
    job_type text,
    required_scope text,
    vessel_name text,
    imo_number text,
    location text,
    planned_date text,
    priority text,
    risk_level text,
    minimum_level text,
    required_department text,
    estimated_days integer,
    client_name text,
    client_reference text,
    notes text,
    status text,
    created_by text,
    assigned_user_id text,
    assigned_user_name text,
    assignment_reason text,
    created_on text,
    updated_on text,
    completed_on text,
    cancelled_on text,
    cancellation_reason text,
    foreign key (assigned_user_id) references users(user_id)
);

create table if not exists job_assignments (
    assignment_id text primary key,
    job_id text references job_requests(job_id),
    user_id text references users(user_id),
    user_name text,
    assignment_type text,
    assigned_by text,
    assigned_on text,
    accepted_on text,
    released_on text,
    status text,
    reason text,
    eligibility_snapshot text,
    created_on text
);

create table if not exists kpi_records (
    kpi_id text primary key,
    user_id text,
    name text,
    period text,
    surveys_done integer,
    plans_reviewed integer,
    audits_done integer,
    reports_overdue integer,
    ncr_count integer,
    client_feedback real,
    training_compliance real,
    utilization_percent real,
    kpi_score real,
    created_on text,
    remarks text,
    foreign key (user_id) references users(user_id)
);

create table if not exists cpd_records (
    cpd_id text primary key,
    user_id text,
    name text,
    title text,
    category text,
    hours real,
    provider text,
    completion_date text,
    activity_date text,
    description text,
    learning_outcome text,
    evidence_file_id text,
    evidence_status text,
    verified_by text,
    verified_on text,
    verification_notes text,
    development_plan_id text,
    source_type text,
    status text,
    created_on text,
    foreign key (user_id) references users(user_id)
);

create table if not exists knowledge_library (
    knowledge_id text primary key,
    title text,
    category text,
    standard text,
    revision text,
    issue_date text,
    file_id text,
    mandatory_ack text,
    uploaded_by text,
    created_on text
);

create table if not exists knowledge_acknowledgements (
    ack_id text primary key,
    knowledge_id text,
    user_id text,
    name text,
    acknowledged_on text,
    status text,
    foreign key (knowledge_id) references knowledge_library(knowledge_id),
    foreign key (user_id) references users(user_id)
);

create table if not exists knowledge_versions (
    version_id text primary key,
    knowledge_id text,
    version_no text,
    revision_date text,
    change_summary text,
    file_link text,
    uploaded_by text,
    approved_by text,
    status text,
    created_on text,
    foreign key (knowledge_id) references knowledge_library(knowledge_id)
);

create table if not exists rule_library (
    rule_id text primary key,
    title text,
    standard text,
    revision text,
    category text,
    link text,
    mandatory text,
    current_version_id text,
    created_on text,
    updated_on text
);

create table if not exists capa_register (
    capa_id text primary key,
    source text,
    finding text,
    severity text,
    owner_id text,
    owner_name text,
    due_date text,
    status text,
    corrective_action text,
    created_on text,
    updated_on text,
    foreign key (owner_id) references users(user_id)
);

create table if not exists notifications (
    notification_id text primary key,
    user_id text,
    name text,
    email text,
    subject text,
    message text,
    type text,
    status text,
    created_on text,
    sent_on text,
    foreign key (user_id) references users(user_id)
);

create table if not exists audit_trail (
    audit_id text primary key,
    date_time text,
    actor_id text,
    actor_name text,
    actor_role text,
    action text,
    details text,
    result text,
    entity_type text,
    entity_id text,
    reason text,
    before_value text,
    after_value text,
    session_id text,
    foreign key (actor_id) references users(user_id)
);

create table if not exists technical_authorities (
    authority_id text primary key,
    user_id text,
    name text,
    discipline text,
    authority_level text,
    approval_limit text,
    active text,
    appointed_by text,
    appointed_on text,
    remarks text,
    foreign key (user_id) references users(user_id)
);

create table if not exists gap_advisor_actions (
    gap_action_id text primary key, user_id text, name text, scope text, gap_key text,
    gap_category text, gap_title text, gap_detail text, priority text, target_module text,
    action_type text, linked_record_id text, development_plan_id text, due_date text, status text,
    owner_id text, owner_name text, source_snapshot text, created_by text, created_on text,
    updated_on text, completed_on text, completion_notes text
);

create table if not exists competency_ncrs (
    ncr_id text primary key, user_id text, name text, source text, source_record_id text, scope text,
    ncr_type text, category text, description text, severity text, likelihood integer, risk_score integer, priority text,
    impact_on_authorization text, status text, incident_date text, containment_action text, root_cause text, corrective_action text,
    owner_id text, owner_name text, corrective_action_owner_id text, corrective_action_owner_name text, due_date text,
    verification_status text, verified_by text, verified_on text, effectiveness_check text, effectiveness_notes text,
    closure_notes text, raised_by text, raised_on text, closed_by text, closed_on text, linked_development_plan_id text,
    linked_gap_action_id text, updated_on text, foreign key (user_id) references users(user_id)
);

create table if not exists authorization_restrictions (
    restriction_id text primary key,
    authorization_id text,
    user_id text,
    name text,
    scope text,
    restriction_type text,
    restriction_detail text,
    effective_date text,
    expiry_date text,
    status text,
    imposed_by text,
    created_on text,
    foreign key (authorization_id) references authorization_requests(authorization_id),
    foreign key (user_id) references users(user_id)
);

create table if not exists client_feedback (
    feedback_id text primary key,
    user_id text,
    name text,
    client_name text,
    project_or_vessel text,
    job_id text,
    rating integer,
    feedback_type text,
    comments text,
    impact_on_kpi text,
    received_on text,
    foreign key (user_id) references users(user_id)
);

create table if not exists succession_plans (
    succession_id text primary key,
    user_id text,
    name text,
    current_role_name text,
    target_role text,
    readiness_level text,
    successor_for text,
    development_actions text,
    expected_ready_date text,
    sponsor text,
    status text,
    created_on text,
    foreign key (user_id) references users(user_id)
);

create table if not exists workforce_forecasts (
    forecast_id text primary key,
    forecast_period text,
    department text,
    role text,
    demand_basis text,
    priority text,
    discipline text,
    required_headcount integer,
    available_headcount integer,
    authorized_headcount integer,
    expiring_authorizations integer,
    leave_or_unavailable integer,
    gap integer,
    risk_status text,
    mitigation_plan text,
    notes text,
    created_by text,
    created_by_name text,
    created_on text,
    updated_on text
);

create table if not exists accreditation_evidence (
    evidence_id text primary key,
    standard text,
    clause text,
    requirement text,
    linked_table text,
    linked_id text,
    evidence_summary text,
    status text,
    owner text,
    last_reviewed text
);

create table if not exists technical_interpretations (
    interpretation_id text primary key,
    title text,
    discipline text,
    related_rule text,
    question text,
    interpretation text,
    approved_by text,
    approval_status text,
    revision text,
    issue_date text,
    created_on text
);

-- Recommended indexes for query performance
create index if not exists users_login_id_idx on users(login_id);
create index if not exists users_email_idx on users(email);
create index if not exists trainings_trainer_id_idx on trainings(trainer_id);
create index if not exists training_records_user_id_idx on training_records(user_id);
create index if not exists training_records_training_id_idx on training_records(training_id);
create index if not exists files_owner_user_id_idx on files(owner_user_id);
create index if not exists files_linked_idx on files(linked_table, linked_id);
create index if not exists competency_matrix_user_id_idx on competency_matrix(user_id);
create index if not exists authorization_requests_user_id_idx on authorization_requests(user_id);
create index if not exists authorization_requests_competency_id_idx on authorization_requests(competency_id);
create index if not exists authorization_certificates_user_id_idx on authorization_certificates(user_id);
create table if not exists authorization_certificate_history (
    history_id text primary key, certificate_id text not null, authorization_id text, user_id text,
    from_status text, to_status text, event_type text not null, reason text, actor_id text, actor_name text,
    event_on text not null, metadata text
);
create index if not exists cert_history_cert_idx on authorization_certificate_history(certificate_id,event_on);
create index if not exists cert_history_auth_idx on authorization_certificate_history(authorization_id,event_on);
create index if not exists revalidation_requests_authorization_id_idx on revalidation_requests(authorization_id);
create index if not exists job_requests_assigned_user_id_idx on job_requests(assigned_user_id);
create index if not exists kpi_records_user_id_idx on kpi_records(user_id);
create index if not exists cpd_records_user_id_idx on cpd_records(user_id);
create index if not exists knowledge_library_status_idx on knowledge_library(status);
create index if not exists knowledge_library_category_idx on knowledge_library(category);
create index if not exists knowledge_versions_knowledge_idx on knowledge_versions(knowledge_id);
create index if not exists knowledge_acknowledgements_user_id_idx on knowledge_acknowledgements(user_id);
create index if not exists knowledge_acknowledgements_knowledge_id_idx on knowledge_acknowledgements(knowledge_id);
create index if not exists competency_ncrs_user_id_idx on competency_ncrs(user_id);
create index if not exists competency_ncrs_status_due_idx on competency_ncrs(status, due_date);
create index if not exists competency_ncrs_source_idx on competency_ncrs(source, source_record_id);
create index if not exists competency_ncrs_priority_idx on competency_ncrs(priority, severity);
create index if not exists authorization_restrictions_authorization_id_idx on authorization_restrictions(authorization_id);
create index if not exists client_feedback_user_id_idx on client_feedback(user_id);
create index if not exists succession_plans_user_id_idx on succession_plans(user_id);


-- Administration master data and governance tables
create table if not exists departments (
    department_id text primary key, department_name text unique, description text,
    head_user_id text, status text, created_on text, updated_on text
);

create table if not exists roles (
    role_id text primary key, role_name text unique, description text, status text,
    created_on text, updated_on text
);

create table if not exists permissions (
    permission_id text primary key, module_name text, action text, scope text,
    description text, status text, created_on text
);

create table if not exists role_permissions (
    role_permission_id text primary key, role_name text, permission_id text, enabled text,
    created_on text, updated_on text
);

create table if not exists user_permission_overrides (
    override_id text primary key, user_id text references users(user_id) on delete cascade,
    permission_id text references permissions(permission_id), enabled text, reason text,
    effective_from text, effective_to text, created_by text, created_on text
);

create table if not exists system_settings (
    setting_key text primary key, setting_value text, setting_group text, description text,
    updated_by text, updated_on text
);

create table if not exists backup_records (
    backup_id text primary key, backup_type text, started_on text, completed_on text,
    status text, file_name text, size_bytes bigint, created_by text, notes text
);

create table if not exists recovery_requests (
    recovery_id text primary key, restore_point text, reason text, requested_by text,
    requested_on text, status text, approved_by text, approved_on text, completed_on text, result text
);

create table if not exists user_assignments (
    assignment_id text primary key, user_id text references users(user_id) on delete cascade,
    assignment_type text, assigned_user_id text, assigned_user_name text, effective_from text,
    effective_to text, status text, created_by text, created_on text
);

-- Safe migrations for existing installations
alter table users add column if not exists employee_id text;
alter table users add column if not exists phone text;
alter table users add column if not exists date_joined text;
alter table users add column if not exists primary_department text;
alter table users add column if not exists account_status text;
alter table users add column if not exists force_password_change text;
alter table users add column if not exists created_by text;
alter table users add column if not exists deactivated_on text;
alter table users add column if not exists deactivation_reason text;
alter table user_departments add column if not exists is_primary text;
alter table user_departments add column if not exists effective_from text;
alter table user_departments add column if not exists effective_to text;
alter table user_departments add column if not exists status text;
alter table departments add column if not exists deputy_user_id text;
alter table audit_trail add column if not exists entity_type text;
alter table audit_trail add column if not exists entity_id text;
alter table audit_trail add column if not exists reason text;
alter table audit_trail add column if not exists before_value text;
alter table audit_trail add column if not exists after_value text;
alter table audit_trail add column if not exists session_id text;

update users set account_status = status where account_status is null or account_status = '';
update users set primary_department = department where primary_department is null or primary_department = '';

create index if not exists audit_trail_actor_idx on audit_trail(actor_id);
create index if not exists audit_trail_entity_idx on audit_trail(entity_type, entity_id);
create index if not exists role_permissions_role_idx on role_permissions(role_name);
create index if not exists user_permission_overrides_user_idx on user_permission_overrides(user_id);
create index if not exists system_settings_group_idx on system_settings(setting_group);
create index if not exists backup_records_status_idx on backup_records(status);
create index if not exists recovery_requests_status_idx on recovery_requests(status);
create index if not exists user_assignments_user_idx on user_assignments(user_id);

-- Succession Planning extensions: structured governance without duplicating development actions.
alter table succession_plans add column if not exists current_department text;
alter table succession_plans add column if not exists target_position text;
alter table succession_plans add column if not exists target_department text;
alter table succession_plans add column if not exists criticality text default 'High';
alter table succession_plans add column if not exists readiness_date text;
alter table succession_plans add column if not exists potential_rating text default 'Medium';
alter table succession_plans add column if not exists risk_status text default 'Monitor';
alter table succession_plans add column if not exists sponsor_id text;
alter table succession_plans add column if not exists linked_development_plan_id text;
alter table succession_plans add column if not exists last_reviewed_on text;
alter table succession_plans add column if not exists review_notes text;
alter table succession_plans add column if not exists updated_on text;
create index if not exists succession_plans_status_idx on succession_plans(status);
create index if not exists succession_plans_target_position_idx on succession_plans(target_position);
create index if not exists succession_plans_candidate_idx on succession_plans(user_id);


create index if not exists cpd_records_user_id_idx on cpd_records(user_id);
create index if not exists cpd_records_evidence_status_idx on cpd_records(evidence_status);
create index if not exists cpd_records_development_plan_idx on cpd_records(development_plan_id);

-- Authorization lifecycle state extensions
alter table authorization_requests add column if not exists application_reason text;
alter table authorization_requests add column if not exists requested_by text;
alter table authorization_requests add column if not exists requested_on text;
alter table authorization_requests add column if not exists current_stage text;
alter table authorization_requests add column if not exists risk_category text;
alter table authorization_requests add column if not exists validity_months integer;
alter table authorization_requests add column if not exists decision_date text;
alter table authorization_requests add column if not exists rejection_reason text;
alter table authorization_requests add column if not exists withdrawn_on text;
alter table authorization_requests add column if not exists withdrawn_reason text;
alter table authorization_requests add column if not exists last_reviewed_on text;
alter table authorization_requests add column if not exists updated_by text;
alter table authorization_requests add column if not exists certificate_status text;
alter table authorization_certificates add column if not exists revoked_on text;
alter table authorization_certificates add column if not exists revocation_reason text;
alter table authorization_certificates add column if not exists public_status text;
alter table authorization_restrictions add column if not exists reason text;
alter table authorization_restrictions add column if not exists revoked_on text;
alter table authorization_restrictions add column if not exists revoked_by text;
alter table authorization_restrictions add column if not exists revoked_reason text;
alter table technical_authorities add column if not exists effective_from text;
alter table technical_authorities add column if not exists effective_to text;
alter table technical_authorities add column if not exists decision_scope text;
alter table annual_reviews add column if not exists training_summary text;
alter table annual_reviews add column if not exists competency_summary text;
alter table annual_reviews add column if not exists authorization_summary text;
alter table annual_reviews add column if not exists ncr_summary text;
alter table annual_reviews add column if not exists cpd_summary text;
alter table annual_reviews add column if not exists client_feedback_summary text;
alter table revalidation_requests add column if not exists initiated_on text;
alter table revalidation_requests add column if not exists initiated_by text;
alter table revalidation_requests add column if not exists readiness_status text;
alter table revalidation_requests add column if not exists evidence_snapshot text;
alter table revalidation_requests add column if not exists decision text;
alter table revalidation_requests add column if not exists decision_reason text;
alter table revalidation_requests add column if not exists decided_by text;
alter table revalidation_requests add column if not exists decided_on text;
create table if not exists authorization_events (event_id text primary key, authorization_id text, user_id text, event_type text, from_status text, to_status text, actor_id text, actor_name text, reason text, created_on text);
create index if not exists authorization_events_auth_idx on authorization_events(authorization_id, created_on);
create index if not exists authorization_requests_status_idx on authorization_requests(status);
create index if not exists authorization_requests_scope_idx on authorization_requests(scope, job_type);
create index if not exists authorization_restrictions_user_status_idx on authorization_restrictions(user_id, status);
create index if not exists revalidation_requests_user_status_idx on revalidation_requests(user_id, final_status);
create index if not exists annual_reviews_user_year_idx on annual_reviews(user_id, review_year);
create index if not exists technical_authorities_user_active_idx on technical_authorities(user_id, active);

-- Unified Technical Reviews workspace (Survey Report Review + Plan Review QA)
create table if not exists technical_reviews (
    review_id text primary key,
    review_type text not null,
    user_id text,
    name text,
    scope text,
    subject_name text,
    source_record_id text,
    reviewer_id text,
    reviewer_name text,
    overall_score real,
    decision text,
    status text,
    comments text,
    created_on text,
    updated_on text,
    due_date text,
    technical_quality integer,
    deficiency_identification integer,
    rule_interpretation integer,
    report_writing integer,
    decision_quality integer,
    report_file_id text,
    vessel_name text,
    comments_quality integer,
    missed_findings integer,
    turnaround_days integer,
    accuracy_score integer,
    project_name text,
    plan_file_id text,
    foreign key (user_id) references users(user_id),
    foreign key (reviewer_id) references users(user_id)
);
create index if not exists technical_reviews_type_idx on technical_reviews(review_type);
create index if not exists technical_reviews_user_scope_idx on technical_reviews(user_id, scope);
create index if not exists technical_reviews_status_idx on technical_reviews(status);
create index if not exists technical_reviews_source_idx on technical_reviews(source_record_id);
create index if not exists technical_reviews_created_idx on technical_reviews(created_on);

-- Professional QMS governance layer
create table if not exists qms_audits (
    audit_id text primary key, audit_type text, department text, standard text, audit_scope text,
    lead_auditor_id text, lead_auditor_name text, planned_date text, completed_date text,
    status text, overall_result text, objective text, report_summary text, created_by text, created_on text, updated_on text
);
create table if not exists qms_compliance_items (
    compliance_id text primary key, standard text, clause text, requirement text, owner_department text,
    owner_id text, owner_name text, frequency text, due_date text, status text, evidence_record text,
    last_reviewed text, next_review_due text, notes text, created_on text, updated_on text
);
create table if not exists qms_management_reviews (
    review_id text primary key, review_period text, chair_id text, chair_name text, review_date text,
    inputs_summary text, decisions text, actions text, responsible_owner_id text, responsible_owner_name text,
    due_date text, status text, created_by text, created_on text, updated_on text
);
create table if not exists qms_management_review_actions (
    action_id text primary key, review_id text not null, action_text text not null,
    owner_id text, owner_name text, due_date text, status text not null default 'Open',
    progress integer not null default 0, closure_note text, completed_on text,
    created_by text, created_on text, updated_on text
);
create index if not exists qms_mr_actions_review_idx on qms_management_review_actions(review_id);
create index if not exists qms_mr_actions_status_idx on qms_management_review_actions(status, due_date);
create table if not exists qms_evidence_reviews (
    evidence_review_id text primary key, source_module text, source_record_id text, evidence_title text,
    reviewer_id text, reviewer_name text, decision text, comments text, reviewed_on text, created_on text
);
create index if not exists qms_audits_status_idx on qms_audits(status, planned_date);
create index if not exists qms_audits_department_idx on qms_audits(department);
create index if not exists qms_compliance_status_idx on qms_compliance_items(status, next_review_due);
create index if not exists qms_compliance_owner_idx on qms_compliance_items(owner_department);
create index if not exists qms_management_reviews_status_idx on qms_management_reviews(status, review_date);
create index if not exists qms_evidence_source_idx on qms_evidence_reviews(source_module, source_record_id);


-- Accreditation readiness governance
create table if not exists accreditation_assessments (
    assessment_id text primary key,
    standard text,
    assessment_period text,
    overall_score numeric,
    readiness_status text,
    assessed_on text,
    assessed_by text,
    approved_by text,
    approval_status text,
    executive_summary text,
    created_on text,
    updated_on text
);
create index if not exists accreditation_assessments_standard_idx on accreditation_assessments(standard, assessment_period);

-- Existing accreditation_evidence table is extended by application migrations for new governance fields.
create index if not exists accreditation_evidence_assessment_idx on accreditation_evidence(assessment_id, status);
create index if not exists accreditation_evidence_due_idx on accreditation_evidence(due_date, status);


CREATE TABLE IF NOT EXISTS interpretation_reviews (
    review_id text primary key, interpretation_id text, reviewer_id text, reviewer_name text,
    stage text, decision text, comments text, reviewed_on text, created_on text
);
CREATE TABLE IF NOT EXISTS rule_change_requests (
    change_id text primary key, title text, related_rule text, change_type text, reason text,
    impact_summary text, affected_departments text, affected_modules text, priority text,
    owner_id text, owner_name text, status text, proposed_revision text, effective_date text,
    source_interpretation_id text, approved_by text, approved_on text, created_by text,
    created_on text, updated_on text
);
CREATE INDEX IF NOT EXISTS interpretation_reviews_interp_idx ON interpretation_reviews(interpretation_id, reviewed_on);
CREATE INDEX IF NOT EXISTS rule_change_status_idx ON rule_change_requests(status, priority);

create index if not exists job_requests_status_idx on job_requests(status);
create index if not exists job_requests_planned_date_idx on job_requests(planned_date);
create index if not exists job_assignments_job_id_idx on job_assignments(job_id);
create index if not exists job_assignments_user_id_idx on job_assignments(user_id);


create table if not exists kpi_snapshots (
  snapshot_id text primary key, user_id text, name text, period text,
  training_score numeric, competency_score numeric, authorization_score numeric,
  technical_review_score numeric, quality_score numeric, delivery_score numeric,
  client_feedback_score numeric, ncr_score numeric, utilization_score numeric,
  overall_score numeric, status text, calculation_version text, source_counts text,
  calculated_on text, calculated_by text, notes text
);
create index if not exists kpi_snapshots_user_period_idx on kpi_snapshots(user_id, period);
create index if not exists kpi_snapshots_status_idx on kpi_snapshots(status);


-- Architecture hardening: modern identity/account fields
alter table users add column if not exists employee_id text;
alter table users add column if not exists primary_department text;
alter table users add column if not exists account_status text;
alter table users add column if not exists force_password_change text;
alter table users add column if not exists password_changed_on text;
alter table users add column if not exists deactivated_on text;
alter table users add column if not exists deactivation_reason text;
create unique index if not exists users_employee_id_unique on users(employee_id) where employee_id is not null and employee_id <> '';

-- Architecture hardening: previously runtime-created tables are now first-class schema objects.
create table if not exists training_requirements (
    requirement_id text primary key, module_id text, requirement_name text, department text, role text, trainee_path text,
    requirement_type text, mandatory text, priority text, prerequisite_module_ids text, sequence_no integer, validity_months integer,
    effective_from text, effective_to text, active text, notes text, created_by text, created_on text, updated_by text, updated_on text
);
create index if not exists training_requirements_module_idx on training_requirements(module_id);
create index if not exists training_requirements_department_idx on training_requirements(department);
create index if not exists training_requirements_path_idx on training_requirements(trainee_path);
create index if not exists training_requirements_active_idx on training_requirements(active);

create table if not exists competency_reviews (
    review_id text primary key, competency_id text, user_id text, name text, scope text, current_level text, recommended_level text,
    decision text, rationale text, evidence_summary text, gaps text, reviewer_id text, reviewer_name text, reviewed_on text,
    next_review_date text, status text, created_on text, updated_on text
);
create index if not exists competency_reviews_user_scope_idx on competency_reviews(user_id, scope);

-- Phase 2 performance indexes: common dashboard/workflow filters.
create index if not exists users_status_department_idx on users(status, primary_department);
create index if not exists users_availability_idx on users(availability);
create index if not exists training_records_status_due_idx on training_records(status, due_date);
create index if not exists training_records_user_status_idx on training_records(user_id, status);
create index if not exists competency_matrix_user_status_idx on competency_matrix(user_id, status);
create index if not exists authorization_requests_user_status_idx on authorization_requests(user_id, status);
create index if not exists authorization_requests_expiry_idx on authorization_requests(expiry_date, status);
create index if not exists job_requests_status_date_idx on job_requests(status, planned_date);
create index if not exists client_feedback_status_due_idx on client_feedback(status, response_due_date);
create index if not exists qms_compliance_due_status_idx on qms_compliance_items(next_review_due, status);
create index if not exists technical_reviews_user_date_idx on technical_reviews(user_id, created_on);
create index if not exists cpd_records_user_completion_idx on cpd_records(user_id, completion_date);
create index if not exists audit_trail_date_actor_idx on audit_trail(date_time, actor_id);

create unique index if not exists users_auth_user_id_idx on users(auth_user_id) where auth_user_id is not null;

create table if not exists auth_sessions (
    session_id text primary key,
    token_hash text unique not null,
    user_id text,
    created_on text not null,
    last_seen text not null,
    expires_at text not null,
    revoked_on text
);
create index if not exists auth_sessions_token_idx on auth_sessions(token_hash);
create index if not exists auth_sessions_user_idx on auth_sessions(user_id, revoked_on, expires_at);

-- Gap-closure Phase: governed KPI definitions, scheduler runs, QR verification, migrations and deprecations.
create table if not exists kpi_definitions (
    kpi_id text primary key, name text unique not null, description text, formula text,
    weight real, target real, period_type text, source_modules text, owner_role text,
    version text, calculation_version text default '1.0', data_owner_role text, effective_from text, effective_to text, active text, business_owner text, approval_status text, approved_by text, approved_on text, approval_reason text, created_on text, updated_on text
);
create index if not exists kpi_definitions_active_idx on kpi_definitions(active, effective_from);

create table if not exists scheduler_runs (
    run_id text primary key, job_name text, started_on text, finished_on text,
    status text, attempt integer, error_message text, duration_ms real
);
create index if not exists scheduler_runs_job_idx on scheduler_runs(job_name, started_on);

create table if not exists qr_verification_events (
    event_id text primary key, certificate_id text, verified_on text, result text, client_fingerprint text
);
create index if not exists qr_verification_cert_idx on qr_verification_events(certificate_id, verified_on);

create table if not exists schema_migrations (
    version text primary key, checksum text not null, applied_on text not null
);

create table if not exists deprecated_table_registry (
    table_name text primary key, replacement_table text, deprecation_status text, notes text, registered_on text
);
insert into deprecated_table_registry(table_name,replacement_table,deprecation_status,notes,registered_on)
values
('legacy_survey_report_reviews','technical_reviews','archived','Historical data preserved after unified technical-review migration.',CURRENT_TIMESTAMP),
('legacy_plan_review_quality','technical_reviews','archived','Historical data preserved after unified technical-review migration.',CURRENT_TIMESTAMP),
('document_versions','knowledge_versions','archived','Replaced by controlled knowledge versioning.',CURRENT_TIMESTAMP),
('field_exposure_matrix','practical_witness','archived','Competency evidence now belongs to Practical/Witness.',CURRENT_TIMESTAMP)
on conflict (table_name) do nothing;

alter table if exists public.scheduler_runs add column if not exists retry_count integer default 0;
alter table if exists public.scheduler_runs add column if not exists next_retry_at timestamp null;
alter table if exists public.scheduler_runs add column if not exists error_code text null;
alter table if exists public.kpi_definitions add column if not exists calculation_version text default '1.0';
alter table if exists public.kpi_definitions add column if not exists data_owner_role text null;
alter table if exists public.kpi_definitions add column if not exists effective_to text null;
alter table if exists public.qr_verification_events add column if not exists response_code text null;
alter table if exists public.qr_verification_events add column if not exists requested_path text null;
alter table if exists public.notifications add column if not exists delivery_status text default 'Pending';
alter table if exists public.notifications add column if not exists sent_on text null;
alter table if exists public.notifications add column if not exists delivered_on text null;
alter table if exists public.notifications add column if not exists acknowledged_on text null;
alter table if exists public.notifications add column if not exists retry_count integer default 0;

-- Database-level audit immutability.
create or replace function psb_block_audit_mutation() returns trigger language plpgsql as $$
begin raise exception 'Audit trail is immutable'; end; $$;
drop trigger if exists trg_audit_trail_immutable on audit_trail;
create trigger trg_audit_trail_immutable before update or delete on audit_trail for each row execute function psb_block_audit_mutation();

-- Seed KPI governance definitions without overriding existing definitions.
insert into kpi_definitions(kpi_id,name,description,formula,weight,target,period_type,source_modules,owner_role,version,effective_from,active,created_on,updated_on)
values
('KPI-TRAINING','Training Compliance','Required training completed on time','completed_required / required_total * 100',0.15,95,'Monthly','Training,Training Matrix','Trainer','1.0','2026-01-01','Yes',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('KPI-TECH','Technical Review Quality','Quality of technical review decisions','accepted_reviews / reviewed_reviews * 100',0.15,95,'Monthly','Technical Reviews','Technical Manager','1.0','2026-01-01','Yes',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('KPI-JOB','Operational Delivery','Completed jobs against planned jobs','completed_jobs / planned_jobs * 100',0.15,90,'Monthly','Job Allocation','Job Coordinator','1.0','2026-01-01','Yes',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
on conflict (name) do nothing;

create table if not exists restore_tests (
    test_id text primary key, restore_point text, tested_on text, tested_by text, status text,
    duration_minutes integer, findings text, corrective_action text, created_on text
);
create index if not exists restore_tests_date_idx on restore_tests(tested_on, status);

-- Phase 6 governance additions.
create table if not exists audit_event_requirements (
  requirement_id text primary key, module_name text not null, action_name text not null,
  severity text not null default 'Required', enabled text not null default 'Yes', notes text, created_on text
);
create unique index if not exists audit_event_requirement_uk on audit_event_requirements(module_name, action_name);
create index if not exists qr_verification_fp_time_idx on qr_verification_events(client_fingerprint, verified_on desc);
alter table if exists restore_tests add column if not exists verified_by text;
alter table if exists restore_tests add column if not exists verified_on text;
alter table if exists restore_tests add column if not exists outcome text;
alter table if exists scheduler_runs add column if not exists heartbeat_on text;
alter table if exists notifications add column if not exists last_error text;
alter table if exists notifications add column if not exists next_retry_at text;
create index if not exists scheduler_runs_heartbeat_idx on scheduler_runs(job_name, heartbeat_on desc);
create index if not exists notifications_retry_idx on notifications(delivery_status, next_retry_at);


create table if not exists probation_reviews (
    review_id text primary key,
    user_id text,
    name text,
    probation_start text,
    probation_end text,
    objectives text,
    performance_summary text,
    training_status text,
    competency_status text,
    tutor_assessment text,
    decision text,
    decision_notes text,
    reviewer_id text,
    reviewer_name text,
    review_date text,
    status text,
    created_on text,
    updated_on text,
    foreign key (user_id) references users(user_id)
);
create index if not exists probation_reviews_user_idx on public.probation_reviews(user_id, status);
create index if not exists probation_reviews_reviewer_idx on public.probation_reviews(reviewer_id, status);

-- Role Experience finalization: exact case evidence and assignment metadata.
create table if not exists authorization_evidence_links (
    link_id text primary key,
    authorization_id text not null,
    source_module text not null,
    source_record_id text not null,
    linked_by text not null,
    linked_on timestamptz not null default current_timestamp,
    reason text,
    unique(authorization_id, source_module, source_record_id)
);
create index if not exists auth_evidence_links_auth_idx on public.authorization_evidence_links(authorization_id);
create index if not exists auth_evidence_links_source_idx on public.authorization_evidence_links(source_module, source_record_id);
alter table if exists public.technical_reviews add column if not exists assigned_reviewer_id text;
alter table if exists public.technical_reviews add column if not exists assigned_reviewer_name text;
alter table if exists public.qms_audits add column if not exists assigned_auditor_id text;
alter table if exists public.qms_audits add column if not exists assigned_auditor_name text;
alter table if exists public.probation_reviews add column if not exists performance_score real;
alter table if exists public.probation_reviews add column if not exists tutor_assessment_status text;

-- Gap 5: explicit technical review assignment lifecycle
create table if not exists technical_review_assignments (
    assignment_id text primary key,
    review_id text not null,
    assigned_reviewer_id text not null,
    assigned_reviewer_name text,
    assigned_by text,
    assigned_by_name text,
    assigned_on text,
    due_date text,
    accepted_on text,
    released_on text,
    status text not null default 'Assigned',
    reason text,
    created_on text,
    updated_on text,
    foreign key (review_id) references technical_reviews(review_id),
    foreign key (assigned_reviewer_id) references users(user_id)
);
create index if not exists technical_review_assignments_reviewer_idx on technical_review_assignments(assigned_reviewer_id, status, due_date);
create index if not exists technical_review_assignments_review_idx on technical_review_assignments(review_id, status);

alter table technical_reviews add column if not exists discipline text;
alter table technical_review_assignments add column if not exists discipline text;
create index if not exists technical_reviews_discipline_idx on technical_reviews(discipline,status);
create index if not exists technical_review_assignments_discipline_idx on technical_review_assignments(discipline,status,assigned_reviewer_id);


-- Professional practical training / witness workflow (migration 035)
create table if not exists practical_requirement_templates (
    requirement_id text primary key, requirement_code text not null unique, title text not null,
    description text, target_role text, trainee_path text, scope text, job_type text, discipline text,
    required_observations integer not null default 1, criteria_json text, eligible_witness_roles text,
    active text not null default 'Yes', created_by text, created_on text, updated_on text
);
create table if not exists practical_activities (
    activity_id text primary key, requirement_id text not null, user_id text not null, name text,
    source_type text, job_id text, vessel_or_project text, job_type text, scope text, discipline text,
    activity_date text, location text, proposed_witness_id text, proposed_witness_name text,
    witness_authorization_id text, status text not null default 'Requested', notes text,
    created_by text, created_on text, updated_on text,
    foreign key(requirement_id) references practical_requirement_templates(requirement_id),
    foreign key(user_id) references users(user_id), foreign key(proposed_witness_id) references users(user_id)
);
create table if not exists practical_assessments (
    assessment_id text primary key, activity_id text not null, requirement_id text not null, user_id text not null,
    name text, witness_id text not null, witness_name text, witness_authorization_id text, witness_scope text,
    assessed_on text, criteria_scores_json text, strengths text, development_areas text,
    technical_observations text, follow_up text, outcome text, declaration_json text,
    status text not null default 'Submitted', amendment_of text, created_on text, updated_on text,
    foreign key(activity_id) references practical_activities(activity_id),
    foreign key(requirement_id) references practical_requirement_templates(requirement_id),
    foreign key(user_id) references users(user_id), foreign key(witness_id) references users(user_id)
);
create table if not exists practical_evidence_links (
    link_id text primary key, activity_id text not null, user_id text not null, source_table text,
    source_record_id text, file_id text, evidence_type text, linked_by text, linked_on text, notes text,
    unique(activity_id, source_table, source_record_id),
    foreign key(activity_id) references practical_activities(activity_id), foreign key(user_id) references users(user_id)
);
create index if not exists practical_requirement_scope_idx on practical_requirement_templates(scope, target_role, active);
create index if not exists practical_activities_user_idx on practical_activities(user_id, scope, status);
create index if not exists practical_activities_witness_idx on practical_activities(proposed_witness_id, status, activity_date);
create index if not exists practical_assessments_user_idx on practical_assessments(user_id, requirement_id, outcome);
create index if not exists practical_assessments_witness_idx on practical_assessments(witness_id, assessed_on);
create index if not exists practical_evidence_activity_idx on practical_evidence_links(activity_id);

-- GM executive personal watchlist; references authoritative records and does not duplicate them.
create table if not exists gm_watchlist (
    watch_id text primary key,
    gm_user_id text not null,
    record_type text not null,
    record_ref text not null,
    title text,
    risk_level text,
    status text,
    due_date text,
    route text,
    added_on text,
    unique(gm_user_id, record_type, record_ref)
);
create index if not exists gm_watchlist_user_idx on gm_watchlist(gm_user_id, status, due_date);


-- Predefined qualification-path model (migration 037)
create table if not exists qualification_paths (
    path_id text primary key, path_code text unique not null, path_name text unique not null, department text not null,
    technical_role text not null, description text, active text default 'Yes', created_by text, created_on text, updated_on text
);
create table if not exists qualification_path_training (
    path_training_id text primary key, path_id text not null, training_id text not null, mandatory text default 'Yes',
    sequence_no integer default 1, active text default 'Yes', created_by text, created_on text,
    foreign key (path_id) references qualification_paths(path_id), foreign key (training_id) references trainings(training_id)
);
create table if not exists qualification_assignments (
    qualification_assignment_id text primary key, user_id text not null, path_id text not null, trainer_id text not null,
    tutor_id text, status text default 'Active', assigned_by text, assigned_on text, updated_on text,
    foreign key (user_id) references users(user_id), foreign key (path_id) references qualification_paths(path_id),
    foreign key (trainer_id) references users(user_id), foreign key (tutor_id) references users(user_id)
);
create index if not exists qualification_path_training_path_idx on qualification_path_training(path_id);
create index if not exists qualification_assignments_user_idx on qualification_assignments(user_id);
create index if not exists qualification_assignments_trainer_idx on qualification_assignments(trainer_id);

-- Qualification curriculum v2 (migration 038)
create table if not exists qualification_path_versions (
 path_version_id text primary key, path_id text not null, version_no text not null, status text default 'Draft', effective_from text, effective_to text, created_by text, created_on text, updated_on text, foreign key(path_id) references qualification_paths(path_id), unique(path_id,version_no));
create table if not exists qualification_path_levels (
 level_id text primary key, path_version_id text not null, level_code text not null, level_name text not null, sequence_no integer default 1, description text, entry_criteria text, completion_criteria text, active text default 'Yes', created_by text, created_on text, updated_on text, foreign key(path_version_id) references qualification_path_versions(path_version_id));
create table if not exists qualification_modules (
 module_id text primary key, module_code text not null, module_name text not null, module_type text not null, description text, mandatory text default 'Yes', passing_score integer default 0, evidence_required text default 'No', assessment_required text default 'No', practical_observations_required integer default 0, witness_required text default 'No', active text default 'Yes', created_by text, created_on text, updated_on text);
create table if not exists qualification_level_modules (
 level_module_id text primary key, level_id text not null, module_id text not null, sequence_no integer default 1, prerequisite_module_ids text, completion_criteria text, active text default 'Yes', created_by text, created_on text, foreign key(level_id) references qualification_path_levels(level_id), foreign key(module_id) references qualification_modules(module_id), unique(level_id,module_id));
create table if not exists qualification_module_requirements (
 requirement_id text primary key, module_id text not null, requirement_type text not null, requirement_ref_id text, requirement_title text not null, mandatory text default 'Yes', required_count integer default 1, notes text, active text default 'Yes', created_by text, created_on text, foreign key(module_id) references qualification_modules(module_id));
create table if not exists qualification_assignment_state (
 state_id text primary key, qualification_assignment_id text not null, path_version_id text, starting_level_id text, current_level_id text, target_department text, person_stage text default 'Qualification', skip_reason text, skip_evidence_ref text, status text default 'Active', updated_by text, updated_on text, foreign key(qualification_assignment_id) references qualification_assignments(qualification_assignment_id), foreign key(path_version_id) references qualification_path_versions(path_version_id), foreign key(starting_level_id) references qualification_path_levels(level_id), foreign key(current_level_id) references qualification_path_levels(level_id), unique(qualification_assignment_id));
create table if not exists probation_transitions (
 transition_id text primary key, user_id text not null, qualification_assignment_id text, from_role text default 'On Probation', to_role text default 'Trainee', target_department text not null, trainer_recommendation text, tutor_comments text, decision text default 'Pending', decided_by text, decided_on text, created_by text, created_on text, foreign key(user_id) references users(user_id), foreign key(qualification_assignment_id) references qualification_assignments(qualification_assignment_id));
create table if not exists crb_case_board_assignments (
 board_assignment_id text primary key, authorization_id text not null, user_id text not null, system_role text not null, board_role text not null, voting_authority text default 'Yes', conflict_declared text default 'No', attendance_status text default 'Pending', decision text, comments text, assigned_by text, assigned_on text, decided_on text, foreign key(authorization_id) references authorization_requests(authorization_id), foreign key(user_id) references users(user_id), unique(authorization_id,user_id));
-- Qualification curriculum delivery: multiple theory items, timed MCQ, guided practical training and independent-practical gate.
create table if not exists qualification_module_training (
  module_training_id text primary key,
  module_id text not null references qualification_modules(module_id),
  training_id text not null references trainings(training_id),
  sequence_no integer default 1,
  mandatory text default 'Yes',
  active text default 'Yes',
  created_by text,
  created_on text,
  unique(module_id, training_id)
);
create table if not exists training_resources (
  resource_id text primary key,
  training_id text not null references trainings(training_id),
  resource_type text not null,
  title text not null,
  url text,
  rule_reference text,
  mandatory text default 'Yes',
  sequence_no integer default 1,
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text
);
create table if not exists training_live_sessions (
  session_id text primary key,
  training_id text not null references trainings(training_id),
  session_title text not null,
  session_date text,
  start_time text,
  end_time text,
  delivery_mode text default 'Online',
  platform text,
  meeting_link text,
  venue text,
  attendance_required text default 'Yes',
  trainer_id text,
  trainer_name text,
  status text default 'Scheduled',
  created_by text,
  created_on text,
  updated_on text
);
create table if not exists training_assessment_configs (
  assessment_config_id text primary key,
  training_id text not null references trainings(training_id),
  title text not null,
  duration_minutes integer default 30,
  passing_score integer default 70,
  max_attempts integer default 2,
  randomize_questions text default 'Yes',
  randomize_answers text default 'Yes',
  show_result_immediately text default 'Yes',
  show_correct_answers text default 'After Final Attempt',
  available_from text,
  available_until text,
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text,
  unique(training_id)
);
create table if not exists training_assessment_sessions (
  assessment_session_id text primary key,
  user_id text not null references users(user_id),
  training_id text not null references trainings(training_id),
  attempt_no integer not null,
  started_at text not null,
  expires_at text not null,
  submitted_at text,
  status text default 'In Progress',
  score real,
  result text,
  correct_count integer default 0,
  question_count integer default 0,
  created_on text,
  updated_on text,
  unique(user_id, training_id, attempt_no)
);
create table if not exists guided_practical_training (
  guided_practical_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  practical_requirement_id text,
  user_id text not null references users(user_id),
  trainer_id text not null references users(user_id),
  trainer_name text,
  sequence_no integer default 1,
  activity_title text not null,
  activity_date text,
  location text,
  activity_reference text,
  learner_activity text,
  learner_preparation text,
  learner_rules_used text,
  learner_observations text,
  learner_deficiencies text,
  learner_evidence text,
  learner_learning text,
  learner_difficulties text,
  trainer_observations text,
  trainer_strengths text,
  trainer_development_areas text,
  trainer_technical_observations text,
  trainer_required_improvement text,
  trainer_decision text default 'Pending',
  trainer_declaration text default 'No',
  learner_submitted_on text,
  trainer_reviewed_on text,
  status text default 'Draft',
  created_on text,
  updated_on text
);
create table if not exists module_practical_gates (
  practical_gate_id text primary key,
  module_id text not null references qualification_modules(module_id),
  minimum_guided_practical integer default 2,
  trainer_satisfaction_required text default 'Yes',
  independent_practical_required integer default 1,
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text,
  unique(module_id)
);
create table if not exists independent_practical_records (
  independent_practical_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  practical_requirement_id text,
  user_id text not null references users(user_id),
  activity_title text not null,
  activity_date text,
  activity_reference text,
  assessor_id text,
  assessor_name text,
  prerequisite_snapshot text,
  report_summary text,
  evidence_reference text,
  assessment_outcome text default 'Pending',
  status text default 'Not Started',
  created_on text,
  updated_on text
);

revoke all on table qualification_module_training, training_resources, training_live_sessions,
 training_assessment_configs, training_assessment_sessions, guided_practical_training,
 module_practical_gates, independent_practical_records from anon, authenticated;
alter table qualification_module_training enable row level security;
alter table training_resources enable row level security;
alter table training_live_sessions enable row level security;
alter table training_assessment_configs enable row level security;
alter table training_assessment_sessions enable row level security;
alter table guided_practical_training enable row level security;
alter table module_practical_gates enable row level security;
alter table independent_practical_records enable row level security;
-- Close qualification delivery gaps: resource completion, live-session attendance,
-- explicit trainer readiness, module progress, probation approval, independent practical assessment.
create table if not exists training_resource_progress (
  resource_progress_id text primary key,
  user_id text not null references users(user_id),
  training_id text not null references trainings(training_id),
  item_type text not null,
  item_id text not null,
  status text default 'Completed',
  completed_on text,
  updated_on text,
  unique(user_id, training_id, item_type, item_id)
);
create table if not exists training_session_attendance (
  attendance_id text primary key,
  session_id text not null references training_live_sessions(session_id),
  training_id text not null references trainings(training_id),
  user_id text not null references users(user_id),
  attendance_status text default 'Not Marked',
  remarks text,
  marked_by text,
  marked_on text,
  updated_on text,
  unique(session_id, user_id)
);
create table if not exists module_trainer_readiness (
  trainer_readiness_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  user_id text not null references users(user_id),
  trainer_id text not null references users(user_id),
  decision text not null,
  remarks text,
  declaration text default 'No',
  decided_on text,
  updated_on text,
  unique(user_id, module_id)
);
create table if not exists qualification_module_progress (
  module_progress_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  user_id text not null references users(user_id),
  theory_status text default 'Not Started',
  guided_practical_status text default 'Locked',
  trainer_gate_status text default 'Pending',
  independent_practical_status text default 'Locked',
  competency_status text default 'Pending',
  module_status text default 'Not Started',
  completion_percent integer default 0,
  completed_on text,
  updated_on text,
  unique(user_id, module_id)
);
create table if not exists probation_progression_approvals (
  progression_approval_id text primary key,
  transition_id text not null references probation_transitions(transition_id),
  user_id text not null references users(user_id),
  requested_by text,
  requested_on text,
  decision text default 'Pending',
  decision_remarks text,
  decided_by text,
  decided_on text,
  updated_on text,
  unique(transition_id)
);
create table if not exists independent_practical_assessments (
  independent_assessment_id text primary key,
  independent_practical_id text not null references independent_practical_records(independent_practical_id),
  user_id text not null references users(user_id),
  assessor_id text not null references users(user_id),
  assessor_name text,
  criteria_scores_json text,
  strengths text,
  development_areas text,
  technical_observations text,
  outcome text,
  declaration text default 'No',
  assessed_on text,
  status text default 'Submitted',
  created_on text,
  updated_on text,
  unique(independent_practical_id)
);

revoke all on table training_resource_progress, training_session_attendance,
 module_trainer_readiness, qualification_module_progress, probation_progression_approvals,
 independent_practical_assessments from anon, authenticated;
alter table training_resource_progress enable row level security;
alter table training_session_attendance enable row level security;
alter table module_trainer_readiness enable row level security;
alter table qualification_module_progress enable row level security;
alter table probation_progression_approvals enable row level security;
alter table independent_practical_assessments enable row level security;


-- Migration 042 canonical additions
-- Authorization/digital certificate + Trainer curriculum publishing closure.
create table if not exists training_mcq_drafts (
  draft_id text primary key,
  training_id text not null references trainings(training_id),
  question text not null,
  option_a text not null,
  option_b text not null,
  option_c text not null,
  option_d text not null,
  correct_answer text not null,
  marks integer default 1,
  status text default 'Draft',
  source_fingerprint text,
  generation_method text,
  generated_by text,
  generated_on text,
  reviewed_by text,
  reviewed_on text,
  published_on text,
  updated_on text
);

create table if not exists qualification_practical_requirements (
  practical_requirement_id text primary key,
  module_id text not null references qualification_modules(module_id),
  activity_domain text not null,
  activity_title text not null,
  activity_mode text not null,
  required_count integer default 1,
  description text,
  mandatory text default 'Yes',
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text
);

revoke all on table training_mcq_drafts, qualification_practical_requirements from anon, authenticated;
alter table training_mcq_drafts enable row level security;
alter table qualification_practical_requirements enable row level security;



-- Migration 043 canonical additions
-- Security/runtime/performance hardening
alter table users add column if not exists mfa_secret text;
alter table users add column if not exists mfa_enabled text default 'No';
alter table users add column if not exists mfa_verified_on text;
alter table files add column if not exists size_bytes bigint;
alter table files add column if not exists security_status text default 'Validated';
alter table files add column if not exists information_classification text default 'Internal';
create table if not exists login_security_state (login_key text primary key, failure_count integer default 0, blocked_until text, last_failure_on text, updated_on text);
create table if not exists case_correspondence (correspondence_id text primary key, authorization_id text not null references authorization_requests(authorization_id), actor_id text, actor_name text, actor_role text, message_type text, message text not null, visibility text default 'Case Participants', created_on text);
create index if not exists case_correspondence_auth_idx on case_correspondence(authorization_id, created_on);
create index if not exists notifications_user_status_idx on notifications(user_id,status,created_on);
create index if not exists training_records_user_training_idx on training_records(user_id,training_id);
create index if not exists qualification_assignments_user_status_idx on qualification_assignments(user_id,status);
revoke all on table login_security_state, case_correspondence from anon, authenticated;
alter table login_security_state enable row level security;
alter table case_correspondence enable row level security;
