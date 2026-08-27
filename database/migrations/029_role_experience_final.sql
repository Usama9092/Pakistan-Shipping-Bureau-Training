-- Final role-experience controls: explicit technical-review assignment and certificate history index.
alter table if exists public.technical_reviews add column if not exists assigned_reviewer_id text;
alter table if exists public.technical_reviews add column if not exists assigned_reviewer_name text;
create index if not exists technical_reviews_assigned_reviewer_idx on public.technical_reviews(assigned_reviewer_id, status);
create index if not exists authorization_certificates_status_idx on public.authorization_certificates(status, expiry_date);
