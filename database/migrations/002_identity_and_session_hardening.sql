alter table users add column if not exists auth_user_id text unique;
create table if not exists auth_sessions (session_id text primary key, user_id text, token_hash text unique, created_on text, last_seen text, expires_at text, revoked_on text);
create index if not exists auth_sessions_user_idx on auth_sessions(user_id, revoked_on, expires_at);
