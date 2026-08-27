-- Case-level CRB assignment prevents department-wide CRB visibility.
alter table if exists public.authorization_requests add column if not exists crb_member_id text;
alter table if exists public.authorization_requests add column if not exists crb_member_name text;
create index if not exists authorization_requests_crb_member_idx on public.authorization_requests(crb_member_id, status);
