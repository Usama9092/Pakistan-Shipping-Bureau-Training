-- Authorization/digital certificate + Trainer curriculum publishing closure.
create table if not exists training_mcq_drafts (
  draft_id text primary key,
  training_id text not null references trainings(training_id),
  question text not null,
  option_a text not null,
  option_b text not null,
  option_c text not null,
  option_d text not null,
  correct_answer text not null,
  marks integer default 1,
  status text default 'Draft',
  source_fingerprint text,
  generation_method text,
  generated_by text,
  generated_on text,
  reviewed_by text,
  reviewed_on text,
  published_on text,
  updated_on text
);

create table if not exists qualification_practical_requirements (
  practical_requirement_id text primary key,
  module_id text not null references qualification_modules(module_id),
  activity_domain text not null,
  activity_title text not null,
  activity_mode text not null,
  required_count integer default 1,
  description text,
  mandatory text default 'Yes',
  active text default 'Yes',
  created_by text,
  created_on text,
  updated_on text
);

revoke all on table training_mcq_drafts, qualification_practical_requirements from anon, authenticated;
alter table training_mcq_drafts enable row level security;
alter table qualification_practical_requirements enable row level security;

alter table guided_practical_training add column practical_requirement_id text references qualification_practical_requirements(practical_requirement_id);
alter table independent_practical_records add column practical_requirement_id text references qualification_practical_requirements(practical_requirement_id);
