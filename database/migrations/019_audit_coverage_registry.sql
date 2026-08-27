-- Machine-auditable registry of business events that must emit audit records.
create table if not exists public.audit_event_requirements (
  requirement_id text primary key,
  module_name text not null,
  action_name text not null,
  severity text not null default 'Required',
  enabled text not null default 'Yes',
  notes text,
  created_on text not null default CURRENT_TIMESTAMP
);
create unique index if not exists audit_event_requirement_uk on public.audit_event_requirements(module_name, action_name);
insert into public.audit_event_requirements(requirement_id,module_name,action_name,notes) values
('AUD-USER','Users & Roles','Create','User creation must emit audit event'),
('AUD-USER-EDIT','Users & Roles','Edit','User/assignment/department changes must emit audit event'),
('AUD-TRAIN-COMPLETE','Training','Complete','Training completion must emit audit event'),
('AUD-COMPETENCY','Competency','Approve','Competency decision must emit audit event'),
('AUD-AUTH','Authorization','Approve','Authorization state transition must emit audit event'),
('AUD-CRB','CRB','Approve','CRB decision must emit audit event'),
('AUD-TECH','Technical Reviews','Approve','Technical review decision must emit audit event'),
('AUD-QMS','QMS','Review','QMS review decision must emit audit event'),
('AUD-NCR','NCR / Corrective Action','Close','NCR closure must emit audit event'),
('AUD-JOB','Job Allocation','Assign','Job assignment/reassignment must emit audit event'),
('AUD-FEEDBACK','Client Feedback','Close','Feedback closure must emit audit event'),
('AUD-KPI','Performance & KPI','Snapshot','KPI snapshot creation must emit audit event'),
('AUD-RULE','Rule Development','Approve','Rule/interpretation publication must emit audit event')
on conflict (module_name, action_name) do nothing;
