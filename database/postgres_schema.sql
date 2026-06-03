-- PostgreSQL schema for Pakistan Shipping Bureau HRDM Training System
-- This schema reflects the application tables and recommended indexes.

set search_path = public;

-- Core user and training tables
create table if not exists users (
    user_id text primary key,
    name text,
    role text,
    trainee_path text,
    department text,
    assigned_duty text,
    email text unique,
    login_id text unique,
    password_hash text,
    temp_password text,
    status text,
    availability text,
    current_location text,
    mentor_id text,
    mentor_name text,
    competency_level text,
    created_on text,
    last_login text
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

create table if not exists field_exposure_matrix (
    exposure_id text primary key,
    user_id text,
    name text,
    trainee_path text,
    scope text,
    activity_type text,
    required_count integer,
    completed_count integer,
    status text,
    updated_on text,
    foreign key (user_id) references users(user_id)
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
    status text,
    created_by text,
    assigned_user_id text,
    assigned_user_name text,
    assignment_reason text,
    created_on text,
    updated_on text,
    foreign key (assigned_user_id) references users(user_id)
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
    evidence_file_id text,
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

create table if not exists document_versions (
    version_id text primary key,
    rule_id text,
    version_no text,
    revision_date text,
    change_summary text,
    file_link text,
    uploaded_by text,
    approved_by text,
    status text,
    created_on text,
    foreign key (rule_id) references rule_library(rule_id)
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

create table if not exists survey_report_reviews (
    review_id text primary key,
    user_id text,
    name text,
    survey_scope text,
    vessel_name text,
    report_file_id text,
    reviewer_id text,
    reviewer_name text,
    technical_quality integer,
    deficiency_identification integer,
    rule_interpretation integer,
    report_writing integer,
    decision_quality integer,
    overall_score real,
    decision text,
    comments text,
    created_on text,
    foreign key (user_id) references users(user_id),
    foreign key (reviewer_id) references users(user_id)
);

create table if not exists plan_review_quality (
    planqa_id text primary key,
    user_id text,
    name text,
    plan_scope text,
    project_name text,
    plan_file_id text,
    reviewer_id text,
    reviewer_name text,
    comments_quality integer,
    missed_findings integer,
    turnaround_days integer,
    accuracy_score integer,
    overall_score real,
    result text,
    comments text,
    created_on text,
    foreign key (user_id) references users(user_id),
    foreign key (reviewer_id) references users(user_id)
);

create table if not exists competency_ncrs (
    ncr_id text primary key,
    user_id text,
    name text,
    source text,
    scope text,
    ncr_type text,
    description text,
    severity text,
    impact_on_authorization text,
    status text,
    corrective_action text,
    raised_by text,
    raised_on text,
    closed_on text,
    foreign key (user_id) references users(user_id)
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
    discipline text,
    required_headcount integer,
    available_headcount integer,
    expiring_authorizations integer,
    leave_or_unavailable integer,
    gap integer,
    risk_status text,
    mitigation_plan text,
    created_on text
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
create index if not exists revalidation_requests_authorization_id_idx on revalidation_requests(authorization_id);
create index if not exists job_requests_assigned_user_id_idx on job_requests(assigned_user_id);
create index if not exists kpi_records_user_id_idx on kpi_records(user_id);
create index if not exists cpd_records_user_id_idx on cpd_records(user_id);
create index if not exists knowledge_acknowledgements_user_id_idx on knowledge_acknowledgements(user_id);
create index if not exists knowledge_acknowledgements_knowledge_id_idx on knowledge_acknowledgements(knowledge_id);
create index if not exists document_versions_rule_id_idx on document_versions(rule_id);
create index if not exists survey_report_reviews_user_id_idx on survey_report_reviews(user_id);
create index if not exists plan_review_quality_user_id_idx on plan_review_quality(user_id);
create index if not exists competency_ncrs_user_id_idx on competency_ncrs(user_id);
create index if not exists authorization_restrictions_authorization_id_idx on authorization_restrictions(authorization_id);
create index if not exists client_feedback_user_id_idx on client_feedback(user_id);
create index if not exists succession_plans_user_id_idx on succession_plans(user_id);
