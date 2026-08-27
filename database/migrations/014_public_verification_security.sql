-- Public verification security metadata and anti-enumeration support.
alter table if exists public.qr_verification_events add column if not exists response_code text null;
alter table if exists public.qr_verification_events add column if not exists requested_path text null;
create index if not exists qr_verification_event_cert_time_idx on public.qr_verification_events(certificate_id, verified_on desc);
