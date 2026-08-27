-- Notification delivery lifecycle fields for scheduler reliability.
alter table if exists public.notifications add column if not exists delivery_status text default 'Pending';
alter table if exists public.notifications add column if not exists sent_on text null;
alter table if exists public.notifications add column if not exists delivered_on text null;
alter table if exists public.notifications add column if not exists acknowledged_on text null;
alter table if exists public.notifications add column if not exists retry_count integer default 0;
