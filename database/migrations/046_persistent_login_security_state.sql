create table if not exists public.login_security_state (
    login_key text primary key,
    failure_count integer not null default 0,
    blocked_until text,
    last_failure_on text,
    updated_on text
);

alter table public.login_security_state enable row level security;
revoke all on table public.login_security_state from anon, authenticated;

create table if not exists public.auth_sessions (
    session_id text primary key,
    user_id text not null,
    token_hash text unique not null,
    created_on text,
    last_seen text,
    expires_at text,
    revoked_on text
);

create index if not exists auth_sessions_user_idx
    on public.auth_sessions(user_id, revoked_on, expires_at);
alter table public.auth_sessions enable row level security;
revoke all on table public.auth_sessions from anon, authenticated;

alter table public.audit_trail add column if not exists entity_type text;
alter table public.audit_trail add column if not exists entity_id text;
alter table public.audit_trail add column if not exists reason text;
alter table public.audit_trail add column if not exists before_value text;
alter table public.audit_trail add column if not exists after_value text;
alter table public.audit_trail add column if not exists session_id text;
create index if not exists audit_trail_entity_idx
    on public.audit_trail(entity_type, entity_id);
