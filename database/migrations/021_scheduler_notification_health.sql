-- Scheduler and notification delivery health fields.
alter table if exists public.scheduler_runs add column if not exists heartbeat_on text;
alter table if exists public.notifications add column if not exists last_error text;
alter table if exists public.notifications add column if not exists next_retry_at text;
create index if not exists scheduler_runs_heartbeat_idx on public.scheduler_runs(job_name, heartbeat_on desc);
create index if not exists notifications_retry_idx on public.notifications(delivery_status, next_retry_at);
