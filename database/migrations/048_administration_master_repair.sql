-- Repair Administration master tables for deployments whose historical
-- baseline migration was recorded before all statements completed.

create table if not exists departments (
    department_id text primary key, department_name text unique, description text,
    head_user_id text, deputy_user_id text, status text, created_on text, updated_on text
);

create table if not exists roles (
    role_id text primary key, role_name text unique, description text, status text,
    created_on text, updated_on text
);

create table if not exists permissions (
    permission_id text primary key, module_name text, action text, scope text,
    description text, status text, created_on text
);

create table if not exists role_permissions (
    role_permission_id text primary key, role_name text, permission_id text, enabled text,
    created_on text, updated_on text
);

create table if not exists user_permission_overrides (
    override_id text primary key, user_id text references users(user_id) on delete cascade,
    permission_id text references permissions(permission_id), enabled text, reason text,
    effective_from text, effective_to text, created_by text, created_on text
);

create table if not exists system_settings (
    setting_key text primary key, setting_value text, setting_group text, description text,
    updated_by text, updated_on text
);

create table if not exists backup_records (
    backup_id text primary key, backup_type text, started_on text, completed_on text,
    status text, file_name text, size_bytes bigint, created_by text, notes text
);

create table if not exists recovery_requests (
    recovery_id text primary key, restore_point text, reason text, requested_by text,
    requested_on text, status text, approved_by text, approved_on text, completed_on text, result text
);

create table if not exists user_assignments (
    assignment_id text primary key, user_id text references users(user_id) on delete cascade,
    assignment_type text, assigned_user_id text, assigned_user_name text, effective_from text,
    effective_to text, status text, created_by text, created_on text
);

create index if not exists role_permissions_role_idx on role_permissions(role_name, enabled);
create index if not exists role_permissions_permission_idx on role_permissions(permission_id);
create index if not exists permissions_lookup_idx on permissions(module_name, action, scope, status);
create index if not exists user_permission_overrides_user_idx on user_permission_overrides(user_id, effective_from, effective_to);

