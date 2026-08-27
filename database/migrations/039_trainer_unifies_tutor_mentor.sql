-- PSB: Trainer is the single qualification, mentoring and development role.
-- Tutor/Mentor is retired as an account role. Legacy tutor/mentor columns are retained
-- only as compatibility aliases so historical records and old reports remain readable.

update public.users
set role = 'Trainer'
where role = 'Tutor/Mentor';

-- Prefer an existing Trainer assignment; otherwise adopt the former tutor/mentor assignment.
update public.users
set trainer_id = coalesce(nullif(trainer_id,''), nullif(tutor_id,''), nullif(mentor_id,'')),
    trainer_name = coalesce(nullif(trainer_name,''), nullif(tutor_name,''), nullif(mentor_name,''))
where coalesce(nullif(trainer_id,''), nullif(tutor_id,''), nullif(mentor_id,'')) is not null;

-- Synchronize legacy aliases to the canonical Trainer for backward compatibility.
update public.users
set tutor_id = trainer_id,
    tutor_name = trainer_name,
    mentor_id = trainer_id,
    mentor_name = trainer_name
where nullif(trainer_id,'') is not null;

update public.qualification_assignments
set tutor_id = trainer_id
where trainer_id is not null;

-- Retire old assignment type and deduplicate active Trainer relationships.
update public.user_assignments
set assignment_type = 'Trainer'
where assignment_type in ('Tutor/Mentor','Tutor','Mentor');

with ranked as (
  select assignment_id,
         row_number() over (
           partition by user_id, assignment_type, assigned_user_id, status
           order by created_on desc nulls last, assignment_id desc
         ) as rn
  from public.user_assignments
  where assignment_type='Trainer' and status='Active'
)
update public.user_assignments ua
set status='Historical', effective_to=coalesce(nullif(effective_to,''), current_date::text)
from ranked r
where ua.assignment_id=r.assignment_id and r.rn>1;

update public.authorization_requests
set status='Trainer Recommended'
where status='Tutor Recommended';

-- Preserve role audit/history while retiring the selectable role profile.
update public.roles
set status='Retired', updated_on=now()::text
where role_name='Tutor/Mentor';

insert into public.schema_migrations(version, applied_on)
select '039', now()::text
where not exists (select 1 from public.schema_migrations where version='039');
