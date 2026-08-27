create table if not exists qr_verification_events (event_id text primary key, certificate_id text, verified_on text, result text, client_fingerprint text);
create index if not exists qr_verification_cert_idx on qr_verification_events(certificate_id, verified_on);
