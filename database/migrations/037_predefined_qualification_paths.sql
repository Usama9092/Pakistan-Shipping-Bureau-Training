-- PSB predefined qualification paths and controlled trainer/tutor assignment
create table if not exists qualification_paths (path_id text primary key, path_code text unique not null, path_name text unique not null, department text not null, technical_role text not null, description text, active text default 'Yes', created_by text, created_on text, updated_on text);
create table if not exists qualification_path_training (path_training_id text primary key, path_id text not null references qualification_paths(path_id), training_id text not null references trainings(training_id), mandatory text default 'Yes', sequence_no integer default 1, active text default 'Yes', created_by text, created_on text);
create table if not exists qualification_assignments (qualification_assignment_id text primary key, user_id text not null references users(user_id), path_id text not null references qualification_paths(path_id), trainer_id text not null references users(user_id), tutor_id text references users(user_id), status text default 'Active', assigned_by text, assigned_on text, updated_on text);
create index if not exists qualification_path_training_path_idx on qualification_path_training(path_id);
create index if not exists qualification_assignments_user_idx on qualification_assignments(user_id);
create index if not exists qualification_assignments_trainer_idx on qualification_assignments(trainer_id);
insert into qualification_paths(path_id,path_code,path_name,department,technical_role,description,active,created_by,created_on,updated_on) values
('QP-NSC','NSC-SURV','NSC Surveyor','Survey NSC','Surveyor','Qualification path for new ship construction survey personnel.','Yes','SYSTEM',current_date::text,current_date::text),
('QP-IS','IS-SURV','In-Service Surveyor','Survey Inservice','Surveyor','Qualification path for in-service survey personnel.','Yes','SYSTEM',current_date::text,current_date::text),
('QP-IND','IND-SURV','Industrial Surveyor','Survey Inservice','Industrial Surveyor','Qualification path for industrial survey personnel.','Yes','SYSTEM',current_date::text,current_date::text),
('QP-PA','PLAN-APP','Plan Appraiser','Plan Appraisal','Plan Appraiser','Qualification path for plan appraisal personnel.','Yes','SYSTEM',current_date::text,current_date::text)
on conflict(path_id) do update set path_name=excluded.path_name,department=excluded.department,technical_role=excluded.technical_role,description=excluded.description,active='Yes',updated_on=excluded.updated_on;

-- Removed legacy role titles must be explicitly reassigned by Admin; do not silently grant the new Department Manager authority.
update users set account_status='Suspended', status='Suspended' where role in ('Principal Surveyor','Chief Plan Appraiser','Technical Manager') and coalesce(account_status,status,'Active') <> 'Deactivated';
