-- Repair the production qualification baseline without broadening browser/database grants.
-- The application continues to enforce record-scoped RBAC; these rows only restore the
-- intended Trainer workflow and the four controlled qualification families.

insert into public.qualification_paths
  (path_id, path_code, path_name, department, technical_role, description, active, created_by, created_on, updated_on)
values
  ('QP-NSC', 'NSC-SURV', 'NSC Surveyor', 'Survey NSC', 'Surveyor', 'Qualification path for new ship construction survey personnel.', 'Yes', 'SYSTEM', current_date::text, current_date::text),
  ('QP-IS', 'IS-SURV', 'In-Service Surveyor', 'Survey Inservice', 'Surveyor', 'Qualification path for in-service survey personnel.', 'Yes', 'SYSTEM', current_date::text, current_date::text),
  ('QP-IND', 'IND-SURV', 'Industrial Surveyor', 'Survey Inservice', 'Industrial Surveyor', 'Qualification path for industrial survey personnel.', 'Yes', 'SYSTEM', current_date::text, current_date::text),
  ('QP-PA', 'PLAN-APP', 'Plan Appraiser', 'Plan Appraisal', 'Plan Appraiser', 'Qualification path for plan appraisal personnel.', 'Yes', 'SYSTEM', current_date::text, current_date::text)
on conflict (path_id) do update
set path_code = excluded.path_code,
    path_name = excluded.path_name,
    department = excluded.department,
    technical_role = excluded.technical_role,
    description = excluded.description,
    active = 'Yes',
    updated_on = excluded.updated_on;

insert into public.qualification_path_versions
  (path_version_id, path_id, version_no, status, effective_from, created_by, created_on, updated_on)
values
  ('QPV-NSC-1', 'QP-NSC', '1.0', 'Active', current_date::text, 'SYSTEM', current_date::text, current_date::text),
  ('QPV-IS-1', 'QP-IS', '1.0', 'Active', current_date::text, 'SYSTEM', current_date::text, current_date::text),
  ('QPV-IND-1', 'QP-IND', '1.0', 'Active', current_date::text, 'SYSTEM', current_date::text, current_date::text),
  ('QPV-PA-1', 'QP-PA', '1.0', 'Active', current_date::text, 'SYSTEM', current_date::text, current_date::text)
on conflict (path_id, version_no) do update
set status = 'Active',
    effective_from = coalesce(nullif(qualification_path_versions.effective_from, ''), excluded.effective_from),
    effective_to = null,
    updated_on = excluded.updated_on;

insert into public.qualification_path_levels
  (level_id, path_version_id, level_code, level_name, sequence_no, description, active, created_by, created_on, updated_on)
values
  ('QL-NSC-1',(select path_version_id from public.qualification_path_versions where path_id='QP-NSC' and version_no='1.0'),'L1','Foundation',1,'Foundation and probation-stage learning.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-NSC-2',(select path_version_id from public.qualification_path_versions where path_id='QP-NSC' and version_no='1.0'),'L2','Technical Development',2,'NSC technical development modules.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-NSC-3',(select path_version_id from public.qualification_path_versions where path_id='QP-NSC' and version_no='1.0'),'L3','Practical Qualification',3,'Practical and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-NSC-4',(select path_version_id from public.qualification_path_versions where path_id='QP-NSC' and version_no='1.0'),'L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IS-1',(select path_version_id from public.qualification_path_versions where path_id='QP-IS' and version_no='1.0'),'L1','Foundation',1,'Foundation and probation-stage learning.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IS-2',(select path_version_id from public.qualification_path_versions where path_id='QP-IS' and version_no='1.0'),'L2','Technical Development',2,'In-service technical development modules.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IS-3',(select path_version_id from public.qualification_path_versions where path_id='QP-IS' and version_no='1.0'),'L3','Practical Qualification',3,'Practical and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IS-4',(select path_version_id from public.qualification_path_versions where path_id='QP-IS' and version_no='1.0'),'L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IND-1',(select path_version_id from public.qualification_path_versions where path_id='QP-IND' and version_no='1.0'),'L1','Foundation',1,'Industrial survey foundation learning.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IND-2',(select path_version_id from public.qualification_path_versions where path_id='QP-IND' and version_no='1.0'),'L2','Technical Development',2,'Industrial survey technical development.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IND-3',(select path_version_id from public.qualification_path_versions where path_id='QP-IND' and version_no='1.0'),'L3','Practical Qualification',3,'Industrial practical and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-IND-4',(select path_version_id from public.qualification_path_versions where path_id='QP-IND' and version_no='1.0'),'L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-PA-1',(select path_version_id from public.qualification_path_versions where path_id='QP-PA' and version_no='1.0'),'L1','Foundation',1,'Foundation and probation-stage learning.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-PA-2',(select path_version_id from public.qualification_path_versions where path_id='QP-PA' and version_no='1.0'),'L2','Technical Development',2,'Plan appraisal technical development.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-PA-3',(select path_version_id from public.qualification_path_versions where path_id='QP-PA' and version_no='1.0'),'L3','Practical Qualification',3,'Practical appraisal and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
  ('QL-PA-4',(select path_version_id from public.qualification_path_versions where path_id='QP-PA' and version_no='1.0'),'L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text)
on conflict (level_id) do update
set path_version_id = excluded.path_version_id,
    level_code = excluded.level_code,
    level_name = excluded.level_name,
    sequence_no = excluded.sequence_no,
    description = excluded.description,
    active = 'Yes',
    updated_on = excluded.updated_on;

-- Ensure the canonical permission definitions exist. Fixed identifiers make the
-- repair repeatable even on deployments whose original permission seed was partial.
insert into public.permissions
  (permission_id, module_name, action, scope, description, status, created_on)
select 'PERM-TRAINING-' || upper(action_name) || '-ASSIGNED', 'Training', action_name, 'Assigned',
       action_name || ' Training at Assigned scope', 'Active', current_date::text
from (values ('View'), ('Create'), ('Edit'), ('Assign'), ('Review')) as actions(action_name)
where not exists (
  select 1 from public.permissions p
  where p.module_name = 'Training' and p.action = action_name and p.scope = 'Assigned'
);

update public.permissions
set status = 'Active'
where module_name = 'Training'
  and action in ('View', 'Create', 'Edit', 'Assign', 'Review')
  and scope = 'Assigned';

insert into public.role_permissions
  (role_permission_id, role_name, permission_id, enabled, created_on, updated_on)
select 'RPERM-TRAINER-' || p.permission_id, 'Trainer', p.permission_id, 'Yes', current_timestamp::text, current_timestamp::text
from public.permissions p
where p.module_name = 'Training'
  and p.action in ('View', 'Create', 'Edit', 'Assign', 'Review')
  and p.scope = 'Assigned'
  and not exists (
    select 1 from public.role_permissions rp
    where rp.role_name = 'Trainer' and rp.permission_id = p.permission_id
  );

update public.role_permissions rp
set enabled = 'Yes', updated_on = current_timestamp::text
from public.permissions p
where rp.permission_id = p.permission_id
  and rp.role_name = 'Trainer'
  and p.module_name = 'Training'
  and p.action in ('View', 'Create', 'Edit', 'Assign', 'Review')
  and p.scope = 'Assigned';

-- These are server-owned tables. Browser roles remain unable to access them
-- directly; Streamlit uses its server-side database credential.
revoke all on table public.permissions, public.role_permissions,
  public.qualification_paths, public.qualification_path_versions,
  public.qualification_path_levels from anon, authenticated;
alter table public.permissions enable row level security;
alter table public.role_permissions enable row level security;
alter table public.qualification_paths enable row level security;
alter table public.qualification_path_versions enable row level security;
alter table public.qualification_path_levels enable row level security;
