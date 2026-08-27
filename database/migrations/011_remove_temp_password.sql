-- Remove obsolete plaintext temporary-password storage. Temporary credentials are never persisted.
alter table if exists public.users drop column if exists temp_password;
