-- Public certificate verification telemetry / throttling support.
alter table if exists public.qr_verification_events add column if not exists client_fingerprint text;
alter table if exists public.qr_verification_events add column if not exists response_code text;
alter table if exists public.qr_verification_events add column if not exists requested_path text;
create index if not exists qr_verification_fp_time_idx on public.qr_verification_events(client_fingerprint, verified_on desc);
