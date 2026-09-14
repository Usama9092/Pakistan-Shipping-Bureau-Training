-- Ensure each PSB-PTQ20-F03 attestation identifies the actual completed training,
-- not only its parent qualification module. Curriculum course titles follow
-- "CODE — Training Name" and are parsed into the certificate fields.

CREATE OR REPLACE FUNCTION public.psb_fill_training_attestation_labels()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  course_title text;
  divider_pos integer;
BEGIN
  SELECT title INTO course_title
  FROM public.trainings
  WHERE training_id = NEW.training_id;

  course_title := COALESCE(course_title, NEW.training_title, '');
  NEW.training_title := course_title;
  divider_pos := strpos(course_title, ' — ');

  IF divider_pos > 0 THEN
    NEW.module_code := btrim(substr(course_title, 1, divider_pos - 1));
    NEW.module_name := btrim(substr(course_title, divider_pos + length(' — ')));
  ELSIF COALESCE(NEW.module_name, '') = '' THEN
    NEW.module_name := course_title;
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_psb_fill_training_attestation_labels ON public.training_attestation_certificates;
CREATE TRIGGER trg_psb_fill_training_attestation_labels
BEFORE INSERT OR UPDATE OF training_id, training_title
ON public.training_attestation_certificates
FOR EACH ROW
EXECUTE FUNCTION public.psb_fill_training_attestation_labels();
