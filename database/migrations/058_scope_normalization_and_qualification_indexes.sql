-- Repair a schema-drift gap that caused every record-scoped read to fail closed
-- when the normalized user-department table was absent in production.
create table if not exists public.user_departments (
    user_department_id text primary key,
    user_id text not null references public.users(user_id) on delete cascade,
    department text not null,
    is_primary text,
    effective_from text,
    effective_to text,
    status text default 'Active',
    created_on text
);

alter table public.user_departments enable row level security;
revoke all on table public.user_departments from anon, authenticated;

-- Relationship and qualification-workspace indexes.  Partial indexes keep the
-- hot active/assigned paths small while preserving the audit/history rows.
create index if not exists users_trainer_active_idx
    on public.users (trainer_id, user_id)
    where trainer_id is not null and trainer_id <> '' and status = 'Active';
create index if not exists user_departments_user_status_idx
    on public.user_departments (user_id, status);
create index if not exists user_departments_department_status_idx
    on public.user_departments (department, status);
create index if not exists qualification_path_versions_active_idx
    on public.qualification_path_versions (path_id, version_no)
    where status = 'Active';
create index if not exists qualification_path_levels_version_active_idx
    on public.qualification_path_levels (path_version_id, sequence_no)
    where active = 'Yes';
create index if not exists qualification_level_modules_level_active_idx
    on public.qualification_level_modules (level_id, sequence_no)
    where active = 'Yes';
create index if not exists qualification_level_modules_module_idx
    on public.qualification_level_modules (module_id);
create index if not exists qualification_assignments_trainer_active_idx
    on public.qualification_assignments (trainer_id, user_id)
    where status = 'Active';
create index if not exists qualification_assignments_path_status_idx
    on public.qualification_assignments (path_id, status);
create index if not exists qualification_assignment_state_version_idx
    on public.qualification_assignment_state (path_version_id);
create index if not exists qualification_assignment_state_current_level_idx
    on public.qualification_assignment_state (current_level_id);
create index if not exists qualification_module_progress_assignment_idx
    on public.qualification_module_progress (qualification_assignment_id);
create index if not exists qualification_module_progress_module_idx
    on public.qualification_module_progress (module_id);
create index if not exists qualification_module_training_training_idx
    on public.qualification_module_training (training_id);
create index if not exists qualification_practical_requirements_module_active_idx
    on public.qualification_practical_requirements (module_id)
    where active = 'Yes';
create index if not exists training_live_sessions_training_idx
    on public.training_live_sessions (training_id);
create index if not exists training_live_sessions_trainer_schedule_idx
    on public.training_live_sessions (trainer_id, status, session_date);
