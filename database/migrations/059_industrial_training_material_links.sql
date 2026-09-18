-- Reuse approved controlled objects for the matching Industrial Survey courses.
-- The underlying private object remains in Supabase Storage; each course gets
-- its own metadata row so learner access and progress stay course-specific.

update trainings
set trainer_id = trainer.user_id,
    trainer_name = trainer.name,
    updated_on = current_timestamp::text
from (
    select user_id, name
    from users
    where lower(login_id) = 'yahyahafiz'
    limit 1
) trainer
where training_id like 'TRN-CURR-IND-%'
  and (coalesce(trainings.trainer_id, '') = '' or coalesce(trainings.trainer_name, '') = '');

with material_map(target_training_id, source_file_id) as (
    values
        ('TRN-CURR-IND-MAT-01', 'FILE-4F44A43C'),
        ('TRN-CURR-IND-MAT-01', 'FILE-84E03F89'),
        ('TRN-CURR-IND-MAT-02', 'FILE-84E03F89'),
        ('TRN-CURR-IND-NDE-01', 'FILE-7249E74E'),
        ('TRN-CURR-IND-NDE-01', 'FILE-2E461839'),
        ('TRN-CURR-IND-WELD-01', 'FILE-84E03F89'),
        ('TRN-CURR-IND-WELD-01', 'FILE-3CE9986D'),
        ('TRN-CURR-IND-WELD-01', 'FILE-828E1E50'),
        ('TRN-CURR-IND-WELD-02', 'FILE-84E03F89'),
        ('TRN-CURR-IND-WELD-02', 'FILE-FF179879')
), trainer as (
    select user_id, name
    from users
    where lower(login_id) = 'yahyahafiz'
    limit 1
)
insert into files (
    file_id, owner_user_id, owner_name, linked_table, linked_id, category,
    file_name, file_ext, mime_type, storage_provider, storage_path, public_url,
    extracted_text, ocr_status, review_status, created_on, updated_on, size_bytes,
    security_status, information_classification, mandatory, sequence_no
)
select
    'FILE-' || upper(substr(md5(m.target_training_id || ':' || m.source_file_id), 1, 8)),
    trainer.user_id,
    trainer.name,
    'trainings',
    m.target_training_id,
    'Training Material',
    source.file_name,
    source.file_ext,
    source.mime_type,
    source.storage_provider,
    source.storage_path,
    source.public_url,
    source.extracted_text,
    source.ocr_status,
    'Pending Review',
    current_timestamp::text,
    current_timestamp::text,
    source.size_bytes,
    source.security_status,
    source.information_classification,
    'Yes',
    1
from material_map m
join files source on source.file_id = m.source_file_id
cross join trainer
where exists (select 1 from trainings t where t.training_id = m.target_training_id)
on conflict (file_id) do nothing;
