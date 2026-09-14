-- Controlled course-content completion, per-training attestation and authorization certificate metadata.

ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'Draft';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS slides_required text NOT NULL DEFAULT 'Yes';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS video_required text NOT NULL DEFAULT 'Yes';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS reference_required text NOT NULL DEFAULT 'Yes';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS scorm_required text NOT NULL DEFAULT 'Yes';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS attendance_required text NOT NULL DEFAULT 'No';
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS minimum_mcqs integer NOT NULL DEFAULT 5;
ALTER TABLE public.trainings ADD COLUMN IF NOT EXISTS attestation_required text NOT NULL DEFAULT 'Yes';

ALTER TABLE public.files ADD COLUMN IF NOT EXISTS mandatory text NOT NULL DEFAULT 'Yes';
ALTER TABLE public.files ADD COLUMN IF NOT EXISTS sequence_no integer NOT NULL DEFAULT 1;

ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS reference_opened text NOT NULL DEFAULT 'No';
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS assigned_on text NOT NULL DEFAULT '';
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS assigned_by text NOT NULL DEFAULT '';
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS assessment_attempts integer NOT NULL DEFAULT 0;
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS last_assessment_on text NOT NULL DEFAULT '';
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS certificate_id text NOT NULL DEFAULT '';
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS certificate_issued_on text NOT NULL DEFAULT '';
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS certificate_issued_by text NOT NULL DEFAULT '';
ALTER TABLE public.training_records ADD COLUMN IF NOT EXISTS completion_snapshot_json text NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS public.training_attestation_certificates (
  certificate_id text PRIMARY KEY,
  record_id text NOT NULL UNIQUE,
  training_id text NOT NULL,
  user_id text NOT NULL,
  name text NOT NULL DEFAULT '',
  training_title text NOT NULL DEFAULT '',
  module_code text NOT NULL DEFAULT '',
  module_name text NOT NULL DEFAULT '',
  conducted_on text NOT NULL DEFAULT '',
  issue_date text NOT NULL DEFAULT '',
  trainer_id text NOT NULL DEFAULT '',
  trainer_name text NOT NULL DEFAULT '',
  trainer_signed_on text NOT NULL DEFAULT '',
  ceo_name text NOT NULL DEFAULT 'Cdre Dr. M Saeed Khalid SI(M)',
  document_code text NOT NULL DEFAULT 'PSB-PTQ20-F03',
  revision_no text NOT NULL DEFAULT '01',
  revision_date text NOT NULL DEFAULT '11-02-2026',
  verification_url text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'Valid',
  created_on text NOT NULL DEFAULT '',
  updated_on text NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_training_attestation_user ON public.training_attestation_certificates(user_id);
CREATE INDEX IF NOT EXISTS idx_training_attestation_training ON public.training_attestation_certificates(training_id);
CREATE INDEX IF NOT EXISTS idx_training_attestation_trainer ON public.training_attestation_certificates(trainer_id);

ALTER TABLE public.authorization_certificates ADD COLUMN IF NOT EXISTS trainer_id text NOT NULL DEFAULT '';
ALTER TABLE public.authorization_certificates ADD COLUMN IF NOT EXISTS trainer_name text NOT NULL DEFAULT '';
ALTER TABLE public.authorization_certificates ADD COLUMN IF NOT EXISTS ceo_name text NOT NULL DEFAULT 'Cdre (R) Dr. M Saeed Khalid';
ALTER TABLE public.authorization_certificates ADD COLUMN IF NOT EXISTS completed_modules text NOT NULL DEFAULT '';
ALTER TABLE public.authorization_certificates ADD COLUMN IF NOT EXISTS document_code text NOT NULL DEFAULT 'PSB-PTQ20-F02';
ALTER TABLE public.authorization_certificates ADD COLUMN IF NOT EXISTS revision_no text NOT NULL DEFAULT '01';
ALTER TABLE public.authorization_certificates ADD COLUMN IF NOT EXISTS revision_date text NOT NULL DEFAULT '11-02-2026';

-- Preserve legacy learner history: courses already used by learners stay published.
UPDATE public.trainings t
SET content_status = 'Published'
WHERE EXISTS (SELECT 1 FROM public.training_records r WHERE r.training_id = t.training_id);

-- Qualification curriculum becomes controlled content. Trainer must validate/publish
-- learning material and MCQs before a learner can complete it.
UPDATE public.trainings t
SET certificate_required = 'Yes',
    attestation_required = 'Yes',
    content_status = CASE
      WHEN EXISTS (
        SELECT 1 FROM public.training_records r
        WHERE r.training_id=t.training_id AND r.certificate_status='Issued'
      ) THEN 'Published'
      ELSE 'Draft'
    END
WHERE EXISTS (
  SELECT 1 FROM public.qualification_module_training qmt
  WHERE qmt.training_id=t.training_id AND qmt.active='Yes'
);
