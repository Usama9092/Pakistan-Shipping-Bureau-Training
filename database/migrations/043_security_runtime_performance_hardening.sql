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
