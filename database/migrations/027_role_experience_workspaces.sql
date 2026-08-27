-- Role experience: exact CRB evidence linkage and explicit review assignment.
create table if not exists authorization_evidence_links (
    link_id text primary key,
    authorization_id text not null,
    source_module text not null,
    source_record_id text not null,
    linked_by text not null,
    linked_on timestamp not null default current_timestamp,
    reason text,
    unique(authorization_id, source_module, source_record_id)
);
create index if not exists auth_evidence_links_auth_idx on authorization_evidence_links(authorization_id);
create index if not exists auth_evidence_links_source_idx on authorization_evidence_links(source_module, source_record_id);

alter table if exists public.technical_reviews add column if not exists assigned_reviewer_id text;
alter table if exists public.technical_reviews add column if not exists assigned_reviewer_name text;
alter table if exists public.qms_audits add column if not exists assigned_auditor_id text;
alter table if exists public.qms_audits add column if not exists assigned_auditor_name text;
alter table if exists public.probation_reviews add column if not exists performance_score real;
alter table if exists public.probation_reviews add column if not exists tutor_assessment_status text;

create index if not exists technical_reviews_assigned_reviewer_idx on public.technical_reviews(assigned_reviewer_id, status);
create index if not exists qms_audits_assigned_auditor_idx on public.qms_audits(assigned_auditor_id, status);
