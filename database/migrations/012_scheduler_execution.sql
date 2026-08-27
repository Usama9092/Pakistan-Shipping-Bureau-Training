-- Scheduler execution reliability metadata.
alter table if exists public.scheduler_runs add column if not exists retry_count integer default 0;
alter table if exists public.scheduler_runs add column if not exists next_retry_at timestamp null;
alter table if exists public.scheduler_runs add column if not exists error_code text null;
