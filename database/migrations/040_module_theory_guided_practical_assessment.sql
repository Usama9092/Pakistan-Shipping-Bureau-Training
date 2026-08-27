-- Qualification curriculum delivery: multiple theory items, timed MCQ, guided practical training and independent-practical gate.
create table if not exists qualification_module_training (
  module_training_id text primary key,
  module_id text not null references qualification_modules(module_id),
  training_id text not null references trainings(training_id),
  sequence_no integer default 1,
  mandatory text default 'Yes',
  active text default 'Yes',
  created_by text,
  created_on text,
  unique(module_id, training_id)
);
create table if not exists training_resources (
  resource_id text primary key,
  training_id text not null references trainings(training_id),
  resource_type text not null,
  title text not null,
  url text,
  rule_reference text,
  mandatory text default 'Yes',
  sequence_no integer default 1,
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text
);
create table if not exists training_live_sessions (
  session_id text primary key,
  training_id text not null references trainings(training_id),
  session_title text not null,
  session_date text,
  start_time text,
  end_time text,
  delivery_mode text default 'Online',
  platform text,
  meeting_link text,
  venue text,
  attendance_required text default 'Yes',
  trainer_id text,
  trainer_name text,
  status text default 'Scheduled',
  created_by text,
  created_on text,
  updated_on text
);
create table if not exists training_assessment_configs (
  assessment_config_id text primary key,
  training_id text not null references trainings(training_id),
  title text not null,
  duration_minutes integer default 30,
  passing_score integer default 70,
  max_attempts integer default 2,
  randomize_questions text default 'Yes',
  randomize_answers text default 'Yes',
  show_result_immediately text default 'Yes',
  show_correct_answers text default 'After Final Attempt',
  available_from text,
  available_until text,
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text,
  unique(training_id)
);
create table if not exists training_assessment_sessions (
  assessment_session_id text primary key,
  user_id text not null references users(user_id),
  training_id text not null references trainings(training_id),
  attempt_no integer not null,
  started_at text not null,
  expires_at text not null,
  submitted_at text,
  status text default 'In Progress',
  score real,
  result text,
  correct_count integer default 0,
  question_count integer default 0,
  created_on text,
  updated_on text,
  unique(user_id, training_id, attempt_no)
);
create table if not exists guided_practical_training (
  guided_practical_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  user_id text not null references users(user_id),
  trainer_id text not null references users(user_id),
  trainer_name text,
  sequence_no integer default 1,
  activity_title text not null,
  activity_date text,
  location text,
  activity_reference text,
  learner_activity text,
  learner_preparation text,
  learner_rules_used text,
  learner_observations text,
  learner_deficiencies text,
  learner_evidence text,
  learner_learning text,
  learner_difficulties text,
  trainer_observations text,
  trainer_strengths text,
  trainer_development_areas text,
  trainer_technical_observations text,
  trainer_required_improvement text,
  trainer_decision text default 'Pending',
  trainer_declaration text default 'No',
  learner_submitted_on text,
  trainer_reviewed_on text,
  status text default 'Draft',
  created_on text,
  updated_on text
);
create table if not exists module_practical_gates (
  practical_gate_id text primary key,
  module_id text not null references qualification_modules(module_id),
  minimum_guided_practical integer default 2,
  trainer_satisfaction_required text default 'Yes',
  independent_practical_required integer default 1,
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text,
  unique(module_id)
);
create table if not exists independent_practical_records (
  independent_practical_id text primary key,
  qualification_assignment_id text references qualification_assignments(qualification_assignment_id),
  module_id text not null references qualification_modules(module_id),
  user_id text not null references users(user_id),
  activity_title text not null,
  activity_date text,
  activity_reference text,
  assessor_id text,
  assessor_name text,
  prerequisite_snapshot text,
  report_summary text,
  evidence_reference text,
  assessment_outcome text default 'Pending',
  status text default 'Not Started',
  created_on text,
  updated_on text
);

revoke all on table qualification_module_training, training_resources, training_live_sessions,
 training_assessment_configs, training_assessment_sessions, guided_practical_training,
 module_practical_gates, independent_practical_records from anon, authenticated;
alter table qualification_module_training enable row level security;
alter table training_resources enable row level security;
alter table training_live_sessions enable row level security;
alter table training_assessment_configs enable row level security;
alter table training_assessment_sessions enable row level security;
alter table guided_practical_training enable row level security;
alter table module_practical_gates enable row level security;
alter table independent_practical_records enable row level security;
