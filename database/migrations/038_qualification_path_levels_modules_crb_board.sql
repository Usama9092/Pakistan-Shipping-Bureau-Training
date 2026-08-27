-- PSB qualification curriculum: versioned paths -> levels -> modules -> requirements.
-- CRB remains a case-based board assignment, not a standalone account role.
create table if not exists qualification_path_versions (
  path_version_id text primary key,
  path_id text not null references qualification_paths(path_id),
  version_no text not null,
  status text default 'Draft',
  effective_from text,
  effective_to text,
  created_by text,
  created_on text,
  updated_on text,
  unique(path_id, version_no)
);
create table if not exists qualification_path_levels (
  level_id text primary key,
  path_version_id text not null references qualification_path_versions(path_version_id),
  level_code text not null,
  level_name text not null,
  sequence_no integer default 1,
  description text,
  entry_criteria text,
  completion_criteria text,
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text
);
create table if not exists qualification_modules (
  module_id text primary key,
  module_code text not null,
  module_name text not null,
  module_type text not null,
  description text,
  mandatory text default 'Yes',
  passing_score integer default 0,
  evidence_required text default 'No',
  assessment_required text default 'No',
  practical_observations_required integer default 0,
  witness_required text default 'No',
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text
);
create table if not exists qualification_level_modules (
  level_module_id text primary key,
  level_id text not null references qualification_path_levels(level_id),
  module_id text not null references qualification_modules(module_id),
  sequence_no integer default 1,
  prerequisite_module_ids text,
  completion_criteria text,
  active text default 'Yes',
  created_by text,
  created_on text,
  unique(level_id,module_id)
);
create table if not exists qualification_module_requirements (
  requirement_id text primary key,
  module_id text not null references qualification_modules(module_id),
  requirement_type text not null,
  requirement_ref_id text,
  requirement_title text not null,
  mandatory text default 'Yes',
  required_count integer default 1,
  notes text,
  active text default 'Yes',
  created_by text,
  created_on text
);
create table if not exists qualification_assignment_state (
  state_id text primary key,
  qualification_assignment_id text not null references qualification_assignments(qualification_assignment_id),
  path_version_id text references qualification_path_versions(path_version_id),
  starting_level_id text references qualification_path_levels(level_id),
  current_level_id text references qualification_path_levels(level_id),
  target_department text,
  person_stage text default 'Qualification',
  skip_reason text,
  skip_evidence_ref text,
  status text default 'Active',
  updated_by text,
  updated_on text,
  unique(qualification_assignment_id)
);
create table if not exists probation_transitions (
  transition_id text primary key,
  user_id text not null references users(user_id),
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  from_role text default 'On Probation',
  to_role text default 'Trainee',
  target_department text not null,
  trainer_recommendation text,
  tutor_comments text,
  decision text default 'Pending',
  decided_by text,
  decided_on text,
  created_by text,
  created_on text
);
create table if not exists crb_case_board_assignments (
  board_assignment_id text primary key,
  authorization_id text not null references authorization_requests(authorization_id),
  user_id text not null references users(user_id),
  system_role text not null,
  board_role text not null,
  voting_authority text default 'Yes',
  conflict_declared text default 'No',
  attendance_status text default 'Pending',
  decision text,
  comments text,
  assigned_by text,
  assigned_on text,
  decided_on text,
  unique(authorization_id,user_id)
);

insert into qualification_path_versions(path_version_id,path_id,version_no,status,effective_from,created_by,created_on,updated_on)
values
('QPV-NSC-1','QP-NSC','1.0','Active',current_date::text,'SYSTEM',current_date::text,current_date::text),
('QPV-IS-1','QP-IS','1.0','Active',current_date::text,'SYSTEM',current_date::text,current_date::text),
('QPV-IND-1','QP-IND','1.0','Active',current_date::text,'SYSTEM',current_date::text,current_date::text),
('QPV-PA-1','QP-PA','1.0','Active',current_date::text,'SYSTEM',current_date::text,current_date::text)
on conflict(path_version_id) do nothing;

insert into qualification_path_levels(level_id,path_version_id,level_code,level_name,sequence_no,description,active,created_by,created_on,updated_on)
values
('QL-NSC-1','QPV-NSC-1','L1','Foundation',1,'Foundation and probation-stage learning.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-NSC-2','QPV-NSC-1','L2','Technical Development',2,'NSC technical development modules.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-NSC-3','QPV-NSC-1','L3','Practical Qualification',3,'Practical and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-NSC-4','QPV-NSC-1','L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IS-1','QPV-IS-1','L1','Foundation',1,'Foundation and probation-stage learning.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IS-2','QPV-IS-1','L2','Technical Development',2,'In-service technical development modules.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IS-3','QPV-IS-1','L3','Practical Qualification',3,'Practical and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IS-4','QPV-IS-1','L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IND-1','QPV-IND-1','L1','Foundation',1,'Industrial survey foundation learning.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IND-2','QPV-IND-1','L2','Technical Development',2,'Industrial survey technical development.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IND-3','QPV-IND-1','L3','Practical Qualification',3,'Industrial practical and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-IND-4','QPV-IND-1','L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-PA-1','QPV-PA-1','L1','Foundation',1,'Plan appraisal foundation learning.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-PA-2','QPV-PA-1','L2','Technical Development',2,'Plan appraisal technical development.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-PA-3','QPV-PA-1','L3','Practical Qualification',3,'Practical appraisal and witness development.','Yes','SYSTEM',current_date::text,current_date::text),
('QL-PA-4','QPV-PA-1','L4','Authorization Readiness',4,'Final competency and authorization readiness.','Yes','SYSTEM',current_date::text,current_date::text)
on conflict(level_id) do nothing;

-- Legacy account roles removed from the active role model. Require explicit reassignment; do not silently elevate.
update users set account_status='Suspended', status='Suspended'
where role in ('Lead Auditor','CRB Member','Job Coordinator') and coalesce(account_status,status,'Active') <> 'Deactivated';

-- Browser roles must not receive direct table privileges; application/server policies are authoritative.
revoke all on table qualification_paths, qualification_path_training, qualification_assignments,
 qualification_path_versions, qualification_path_levels, qualification_modules,
 qualification_level_modules, qualification_module_requirements, qualification_assignment_state,
 probation_transitions, crb_case_board_assignments from anon, authenticated;
alter table qualification_paths enable row level security;
alter table qualification_path_training enable row level security;
alter table qualification_assignments enable row level security;
alter table qualification_path_versions enable row level security;
alter table qualification_path_levels enable row level security;
alter table qualification_modules enable row level security;
alter table qualification_level_modules enable row level security;
alter table qualification_module_requirements enable row level security;
alter table qualification_assignment_state enable row level security;
alter table probation_transitions enable row level security;
alter table crb_case_board_assignments enable row level security;
