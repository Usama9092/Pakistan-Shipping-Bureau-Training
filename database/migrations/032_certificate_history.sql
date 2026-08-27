-- Gap 18: immutable certificate lifecycle/history ledger
create table if not exists public.authorization_certificate_history (
    history_id text primary key,
    certificate_id text not null,
    authorization_id text,
    user_id text,
    from_status text,
    to_status text,
    event_type text not null,
    reason text,
    actor_id text,
    actor_name text,
    event_on text not null,
    metadata text
);
create index if not exists cert_history_cert_idx on public.authorization_certificate_history(certificate_id,event_on);
create index if not exists cert_history_auth_idx on public.authorization_certificate_history(authorization_id,event_on);
