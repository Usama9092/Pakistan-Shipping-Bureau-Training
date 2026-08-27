create table if not exists scheduler_runs (run_id text primary key, job_name text, started_on text, finished_on text, status text, attempt integer, error_message text, duration_ms real);
create index if not exists scheduler_runs_job_idx on scheduler_runs(job_name, started_on);
