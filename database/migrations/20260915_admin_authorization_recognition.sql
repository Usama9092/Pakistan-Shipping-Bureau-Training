alter table public.training_records add column if not exists administrative_recognition text default 'No';
alter table public.training_records add column if not exists recognition_id text;
alter table public.training_records add column if not exists recognition_basis text;

alter table public.qualification_module_progress add column if not exists administrative_recognition text default 'No';
alter table public.qualification_module_progress add column if not exists recognition_id text;
alter table public.qualification_module_progress add column if not exists recognition_basis text;

alter table public.training_attestation_certificates add column if not exists completion_basis text;
alter table public.training_attestation_certificates add column if not exists recognition_id text;
alter table public.training_attestation_certificates add column if not exists administrative_signoff_id text;
alter table public.training_attestation_certificates add column if not exists administrative_signoff_name text;

alter table public.authorization_requests add column if not exists recognition_id text;
alter table public.authorization_requests add column if not exists authorization_basis text;

alter table public.authorization_certificates add column if not exists recognition_id text;
alter table public.authorization_certificates add column if not exists authorization_basis text;

create table if not exists public.administrative_authorization_recognitions (
    recognition_id text primary key,
    user_id text not null,
    name text,
    path_id text,
    path_name text,
    scope text,
    job_type text,
    trainer_id text,
    trainer_name text,
    effective_date text,
    recognition_reason text,
    declaration text,
    training_count integer default 0,
    attestation_count integer default 0,
    module_count integer default 0,
    authorization_id text,
    authorization_certificate_id text,
    status text default 'Draft',
    recognized_by_id text,
    recognized_by_name text,
    recognized_on text,
    created_on text,
    updated_on text
);

create index if not exists idx_admin_auth_recognition_user on public.administrative_authorization_recognitions(user_id);
create index if not exists idx_training_records_recognition on public.training_records(recognition_id);
create index if not exists idx_training_attestation_recognition on public.training_attestation_certificates(recognition_id);
create index if not exists idx_auth_requests_recognition on public.authorization_requests(recognition_id);
create index if not exists idx_auth_certificates_recognition on public.authorization_certificates(recognition_id);
