-- Professional practical training / witness workflow.
create table if not exists practical_requirement_templates (
    requirement_id text primary key,
    requirement_code text not null unique,
    title text not null,
    description text,
    target_role text,
    trainee_path text,
    scope text,
    job_type text,
    discipline text,
    required_observations integer not null default 1,
    criteria_json text,
    eligible_witness_roles text,
    active text not null default 'Yes',
    created_by text,
    created_on text,
    updated_on text
);
create index if not exists practical_requirement_scope_idx on practical_requirement_templates(scope, target_role, active);

create table if not exists practical_activities (
    activity_id text primary key,
    requirement_id text not null,
    user_id text not null,
    name text,
    source_type text,
    job_id text,
    vessel_or_project text,
    job_type text,
    scope text,
    discipline text,
    activity_date text,
    location text,
    proposed_witness_id text,
    proposed_witness_name text,
    witness_authorization_id text,
    status text not null default 'Requested',
    notes text,
    created_by text,
    created_on text,
    updated_on text,
    foreign key(requirement_id) references practical_requirement_templates(requirement_id),
    foreign key(user_id) references users(user_id),
    foreign key(proposed_witness_id) references users(user_id)
);
create index if not exists practical_activities_user_idx on practical_activities(user_id, scope, status);
create index if not exists practical_activities_witness_idx on practical_activities(proposed_witness_id, status, activity_date);
create index if not exists practical_activities_job_idx on practical_activities(job_id);

create table if not exists practical_assessments (
    assessment_id text primary key,
    activity_id text not null,
    requirement_id text not null,
    user_id text not null,
    name text,
    witness_id text not null,
    witness_name text,
    witness_authorization_id text,
    witness_scope text,
    assessed_on text,
    criteria_scores_json text,
    strengths text,
    development_areas text,
    technical_observations text,
    follow_up text,
    outcome text,
    declaration_json text,
    status text not null default 'Submitted',
    amendment_of text,
    created_on text,
    updated_on text,
    foreign key(activity_id) references practical_activities(activity_id),
    foreign key(requirement_id) references practical_requirement_templates(requirement_id),
    foreign key(user_id) references users(user_id),
    foreign key(witness_id) references users(user_id)
);
create index if not exists practical_assessments_user_idx on practical_assessments(user_id, requirement_id, outcome);
create index if not exists practical_assessments_witness_idx on practical_assessments(witness_id, assessed_on);

create table if not exists practical_evidence_links (
    link_id text primary key,
    activity_id text not null,
    user_id text not null,
    source_table text,
    source_record_id text,
    file_id text,
    evidence_type text,
    linked_by text,
    linked_on text,
    notes text,
    unique(activity_id, source_table, source_record_id),
    foreign key(activity_id) references practical_activities(activity_id),
    foreign key(user_id) references users(user_id)
);
create index if not exists practical_evidence_activity_idx on practical_evidence_links(activity_id);
create index if not exists practical_evidence_user_idx on practical_evidence_links(user_id);

-- Seed one practical requirement per active authorization scope. The requirement library
-- can be refined by Technical Management without creating per-employee duplicates.
insert into practical_requirement_templates(
    requirement_id, requirement_code, title, description, target_role, trainee_path,
    scope, job_type, discipline, required_observations, criteria_json,
    eligible_witness_roles, active, created_by, created_on, updated_on
)
select
    'PREQ-' || substr(md5(coalesce(scope,'') || ':' || coalesce(job_type,'')),1,12),
    'PR-' || upper(substr(md5(coalesce(scope,'') || ':' || coalesce(job_type,'')),1,8)),
    coalesce(scope,'Practical') || ' Practical Demonstration',
    'Demonstrate practical capability for the authorization scope using real work, supervised activity or an approved simulation.',
    'All', 'All', scope, job_type,
    case
      when lower(coalesce(scope,'')) like '%hull%' then 'Hull'
      when lower(coalesce(scope,'')) like '%machinery%' then 'Machinery'
      when lower(coalesce(scope,'')) like '%electrical%' then 'Electrical'
      when lower(coalesce(scope,'')) like '%industrial%' then 'Industrial'
      when lower(coalesce(scope,'')) like '%plan%' then 'Plan Appraisal'
      when lower(coalesce(scope,'')) like '%audit%' then 'QMS / Audit'
      when lower(coalesce(scope,'')) like '%rule%' then 'Rule Development'
      else 'General'
    end,
    greatest(1, coalesce(required_witness_count,0) + coalesce(required_supervised_count,0) + coalesce(required_joint_plan_count,0) + coalesce(required_independent_plan_count,0)),
    case when lower(coalesce(scope,'')) like '%plan%' then
      '["Drawing review","Rule identification","Technical calculations","Deficiency/comment preparation","Rule interpretation","Communication with designer","Final recommendation","Document control"]'
    else
      '["Preparation & planning","Rules & procedures","Technical execution","Deficiency identification","Objective evidence","Reporting","Professional judgement","Communication"]'
    end,
    '["Surveyor","Industrial Surveyor","Plan Appraiser","Principal Surveyor","Chief Plan Appraiser","Technical Manager"]',
    'Yes', 'System', current_timestamp::text, current_timestamp::text
from authorization_matrix
where coalesce(active,'Yes') = 'Yes'
on conflict(requirement_code) do nothing;
