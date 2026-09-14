-- Schema support for the Excel-derived PSB qualification curriculum.
-- Additive only: no existing user, training, assessment or authorization row is deleted.

ALTER TABLE public.users ADD COLUMN IF NOT EXISTS primary_department text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS trainer_id text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS trainer_name text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS tutor_id text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS tutor_name text;

ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS delivery_mode text DEFAULT 'Self-paced';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS duration_hours double precision DEFAULT 0;
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS location_or_platform text DEFAULT '';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS capacity integer DEFAULT 0;
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS enrollment_open text DEFAULT 'Yes';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS course_version text DEFAULT '1.0';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS prerequisite_text text DEFAULT '';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS assessment_required text DEFAULT 'Yes';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS certificate_required text DEFAULT 'No';

CREATE TABLE IF NOT EXISTS public.training_requirements (
    requirement_id text PRIMARY KEY,
    module_id text,
    requirement_name text,
    department text,
    role text,
    trainee_path text,
    requirement_type text,
    mandatory text DEFAULT 'Yes',
    priority text DEFAULT 'Medium',
    prerequisite_module_ids text DEFAULT '',
    sequence_no integer DEFAULT 0,
    validity_months integer DEFAULT 36,
    effective_from text DEFAULT '',
    effective_to text DEFAULT '',
    active text DEFAULT 'Yes',
    notes text DEFAULT '',
    created_by text DEFAULT '',
    created_on text DEFAULT '',
    updated_by text DEFAULT '',
    updated_on text DEFAULT ''
);

UPDATE public.qualification_path_levels SET description='Common Foundation', completion_criteria='Complete the controlled common foundation before job-specific NSC development.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-NSC-1';
UPDATE public.qualification_path_levels SET description='Technical Development', completion_criteria='Complete mandatory NSC technical theory; NDT Level-II modules are scope-dependent.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-NSC-2';
UPDATE public.qualification_path_levels SET description='Practical Qualification', completion_criteria='Complete F01/F04 hull and machinery/electrical OJT, Trainer readiness and independent practical assessment.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-NSC-3';
UPDATE public.qualification_path_levels SET description='Authorization Readiness', completion_criteria='Controlled F04 evidence, Department recommendation, CRB and final authorization govern progression.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-NSC-4';

UPDATE public.qualification_path_levels SET description='Common Foundation', completion_criteria='Complete the controlled common foundation before existing-ship specialization.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-IS-1';
UPDATE public.qualification_path_levels SET description='Technical Development', completion_criteria='Complete in-service technical theory, survey checklist training and assigned ship-type familiarization.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-IS-2';
UPDATE public.qualification_path_levels SET description='Practical Qualification', completion_criteria='Complete Existing Ship class, SOLAS and statutory practical development and independent assessment.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-IS-3';
UPDATE public.qualification_path_levels SET description='Authorization Readiness', completion_criteria='Existing Ships Survey Authorization Sheet defines the final ship-type and survey scope before authorization.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-IS-4';

UPDATE public.qualification_path_levels SET description='Common Foundation', completion_criteria='Complete the controlled common foundation before plan-appraisal specialization.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-PA-1';
UPDATE public.qualification_path_levels SET description='Technical Development', completion_criteria='Complete Plan Appraisal Core plus Statutory, Hull, Machinery, Electrical and Stability theory.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-PA-2';
UPDATE public.qualification_path_levels SET description='Practical Qualification', completion_criteria='Complete supervised and independent plan-appraisal practical work against F05.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-PA-3';
UPDATE public.qualification_path_levels SET description='Authorization Readiness', completion_criteria='PSB-OJTP10-F05 evidence, Department recommendation, CRB and final authorization govern progression.', updated_on=CURRENT_TIMESTAMP::text WHERE level_id='QL-PA-4';
