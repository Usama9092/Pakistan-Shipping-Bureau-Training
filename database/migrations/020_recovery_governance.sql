-- Recovery governance metadata.
alter table if exists public.restore_tests add column if not exists verified_by text;
alter table if exists public.restore_tests add column if not exists verified_on text;
alter table if exists public.restore_tests add column if not exists outcome text;
