-- Close qualification delivery gaps: resource completion, live-session attendance,
-- explicit trainer readiness, module progress, probation approval, independent practical assessment.
create table if not exists training_resource_progress (
  resource_progress_id text primary key,
  user_id text not null references users(user_id),
  training_id text not null references trainings(training_id),
  item_type text not null,
  item_id text not null,
  status text default 'Completed',
  completed_on text,
  updated_on text,
  unique(user_id, training_id, item_type, item_id)
);
create table if not exists training_session_attendance (
  attendance_id text primary key,
  session_id text not null references training_live_sessions(session_id),
  training_id text not null references trainings(training_id),
  user_id text not null references users(user_id),
  attendance_status text default 'Not Marked',
  remarks text,
  marked_by text,
  marked_on text,
  updated_on text,
  unique(session_id, user_id)
);
create table if not exists module_trainer_readiness (
  trainer_readiness_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  user_id text not null references users(user_id),
  trainer_id text not null references users(user_id),
  decision text not null,
  remarks text,
  declaration text default 'No',
  decided_on text,
  updated_on text,
  unique(user_id, module_id)
);
create table if not exists qualification_module_progress (
  module_progress_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  user_id text not null references users(user_id),
  theory_status text default 'Not Started',
  guided_practical_status text default 'Locked',
  trainer_gate_status text default 'Pending',
  independent_practical_status text default 'Locked',
  competency_status text default 'Pending',
  module_status text default 'Not Started',
  completion_percent integer default 0,
  completed_on text,
  updated_on text,
  unique(user_id, module_id)
);
create table if not exists probation_progression_approvals (
  progression_approval_id text primary key,
  transition_id text not null references probation_transitions(transition_id),
  user_id text not null references users(user_id),
  requested_by text,
  requested_on text,
  decision text default 'Pending',
  decision_remarks text,
  decided_by text,
  decided_on text,
  updated_on text,
  unique(transition_id)
);
create table if not exists independent_practical_assessments (
  independent_assessment_id text primary key,
  independent_practical_id text not null references independent_practical_records(independent_practical_id),
  user_id text not null references users(user_id),
  assessor_id text not null references users(user_id),
  assessor_name text,
  criteria_scores_json text,
  strengths text,
  development_areas text,
  technical_observations text,
  outcome text,
  declaration text default 'No',
  assessed_on text,
  status text default 'Submitted',
  created_on text,
  updated_on text,
  unique(independent_practical_id)
);

revoke all on table training_resource_progress, training_session_attendance,
 module_trainer_readiness, qualification_module_progress, probation_progression_approvals,
 independent_practical_assessments from anon, authenticated;
alter table training_resource_progress enable row level security;
alter table training_session_attendance enable row level security;
alter table module_trainer_readiness enable row level security;
alter table qualification_module_progress enable row level security;
alter table probation_progression_approvals enable row level security;
alter table independent_practical_assessments enable row level security;
