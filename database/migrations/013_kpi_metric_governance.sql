-- KPI governance metadata to make historical scorecards reproducible.
alter table if exists public.kpi_definitions add column if not exists calculation_version text default '1.0';
alter table if exists public.kpi_definitions add column if not exists data_owner_role text null;
alter table if exists public.kpi_definitions add column if not exists effective_to text null;
