-- One-time bootstrap administrator lifecycle.
-- Existing administrators keep their passwords; only the configured
-- bootstrap account is required to replace its predefined first-login secret.
alter table users add column if not exists force_password_change text default 'No';
alter table users add column if not exists password_changed_on text;
alter table users add column if not exists account_status text;

update users
set role = 'Admin',
    status = 'Active',
    account_status = 'Active',
    force_password_change = 'Yes'
where lower(coalesce(email, '')) = 'admin@psbureau.org'
  and lower(coalesce(login_id, '')) = 'admin'
  and coalesce(password_changed_on, '') in ('', to_char(current_date, 'YYYY-MM-DD'));

create index if not exists users_active_login_idx on users (lower(login_id), status);
create index if not exists users_active_email_idx on users (lower(email), status);
