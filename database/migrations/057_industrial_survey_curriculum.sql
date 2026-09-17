-- Controlled Industrial Surveyor curriculum.
-- Theoretical courses remain Draft until a Trainer uploads authoritative source
-- material and publishes source-grounded MCQs. Practical requirements are active
-- immediately so the Trainer can record guided/witness development.

update public.qualification_path_levels
set description='Common Foundation',
    completion_criteria='Complete the controlled common foundation before industrial-survey specialization.',
    updated_on=current_timestamp::text
where level_id='QL-IND-1';

update public.qualification_path_levels
set description='Technical Development',
    completion_criteria='Complete industrial quality, material, welding, NDE, testing and release theory.',
    updated_on=current_timestamp::text
where level_id='QL-IND-2';

update public.qualification_path_levels
set description='Practical Qualification',
    completion_criteria='Complete guided industrial inspections, Trainer readiness gates and independent practical assessments.',
    updated_on=current_timestamp::text
where level_id='QL-IND-3';

update public.qualification_path_levels
set description='Authorization Readiness',
    completion_criteria='Controlled evidence, Department recommendation, CRB and final authorization govern progression.',
    updated_on=current_timestamp::text
where level_id='QL-IND-4';

insert into public.qualification_modules
  (module_id,module_code,module_name,module_type,description,mandatory,passing_score,evidence_required,
   assessment_required,practical_observations_required,witness_required,active,created_by,created_on,updated_on,
   practical_training_required)
values
  ('QMOD-IND-QA','IND-QA','Industrial Quality and Inspection Planning','Theoretical Training','Vendor capability, quality-plan, inspection-test-plan, hold/witness points and inspection reporting.','Yes',70,'No','Yes',0,'No','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text,'No'),
  ('QMOD-IND-MATWELD','IND-MAT-WELD','Industrial Materials and Welding','Theoretical Training','Material identification, traceability, certificates, mechanical testing, welding procedures, welder qualification and heat treatment.','Yes',70,'No','Yes',0,'No','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text,'No'),
  ('QMOD-IND-NDETEST','IND-NDE-TEST','Industrial NDE, Testing and Final Release','Theoretical Training','Visual and surface/volumetric NDE, dimensional/coating inspection, pressure/load/shop tests, FAT, NCR closure and final release.','Yes',70,'No','Yes',0,'No','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text,'No'),
  ('QMOD-IND-QA-OJT','IND-QA-OJT','Industrial Quality Planning Practical','Practical Training','Guided vendor capability, QAP/ITP and inspection planning activities.','Yes',0,'Yes','Yes',2,'Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text,'Yes'),
  ('QMOD-IND-MAT-OJT','IND-MAT-OJT','Industrial Materials and Welding Practical','Practical Training','Guided material, mechanical-test, welding and heat-treatment activities.','Yes',0,'Yes','Yes',2,'Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text,'Yes'),
  ('QMOD-IND-NDE-OJT','IND-NDE-OJT','Industrial NDE and Fabrication Practical','Practical Training','Guided fabrication, dimensional, weld and NDE activities.','Yes',0,'Yes','Yes',2,'Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text,'Yes'),
  ('QMOD-IND-FAT-OJT','IND-FAT-OJT','Industrial Testing and Release Practical','Practical Training','Guided pressure/load/shop/electrical/FAT, coating, packing, final-release and NCR activities.','Yes',0,'Yes','Yes',2,'Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text,'Yes')
on conflict (module_id) do update set
  module_code=excluded.module_code,module_name=excluded.module_name,module_type=excluded.module_type,
  description=excluded.description,mandatory=excluded.mandatory,passing_score=excluded.passing_score,
  evidence_required=excluded.evidence_required,assessment_required=excluded.assessment_required,
  practical_observations_required=excluded.practical_observations_required,witness_required=excluded.witness_required,
  active='Yes',practical_training_required=excluded.practical_training_required,updated_on=current_timestamp::text;

insert into public.qualification_level_modules
  (level_module_id,level_id,module_id,sequence_no,prerequisite_module_ids,completion_criteria,active,created_by,created_on)
values
  ('QLM-IND-COMMON','QL-IND-1','QMOD-COMMON-FOUNDATION',1,'','Complete all mandatory common theoretical training and assessments.','Yes','controlled-curriculum',current_timestamp::text),
  ('QLM-IND-QA','QL-IND-2','QMOD-IND-QA',1,'QMOD-COMMON-FOUNDATION','Complete industrial quality and inspection-planning theory.','Yes','controlled-curriculum',current_timestamp::text),
  ('QLM-IND-MATWELD','QL-IND-2','QMOD-IND-MATWELD',2,'QMOD-IND-QA','Complete industrial materials and welding theory.','Yes','controlled-curriculum',current_timestamp::text),
  ('QLM-IND-NDETEST','QL-IND-2','QMOD-IND-NDETEST',3,'QMOD-IND-MATWELD','Complete NDE, testing and final-release theory.','Yes','controlled-curriculum',current_timestamp::text),
  ('QLM-IND-QA-OJT','QL-IND-3','QMOD-IND-QA-OJT',1,'QMOD-IND-QA','Complete quality-planning guided practical and independent assessment.','Yes','controlled-curriculum',current_timestamp::text),
  ('QLM-IND-MAT-OJT','QL-IND-3','QMOD-IND-MAT-OJT',2,'QMOD-IND-MATWELD','Complete materials/welding guided practical and independent assessment.','Yes','controlled-curriculum',current_timestamp::text),
  ('QLM-IND-NDE-OJT','QL-IND-3','QMOD-IND-NDE-OJT',3,'QMOD-IND-NDETEST','Complete fabrication/NDE guided practical and independent assessment.','Yes','controlled-curriculum',current_timestamp::text),
  ('QLM-IND-FAT-OJT','QL-IND-3','QMOD-IND-FAT-OJT',4,'QMOD-IND-NDETEST','Complete industrial testing/release guided practical and independent assessment.','Yes','controlled-curriculum',current_timestamp::text)
on conflict (level_module_id) do update set
  level_id=excluded.level_id,module_id=excluded.module_id,sequence_no=excluded.sequence_no,
  prerequisite_module_ids=excluded.prerequisite_module_ids,completion_criteria=excluded.completion_criteria,active='Yes';

with src(training_id,module_id,title,category,standards,sequence_no) as (values
  ('TRN-CURR-IND-QA-01','QMOD-IND-QA','IND-QA-01 — Industrial Survey Governance and Professional Conduct','Industrial Quality','PSB controlled industrial-survey curriculum',1),
  ('TRN-CURR-IND-QA-02','QMOD-IND-QA','IND-QA-02 — Vendor and Works Capability Assessment','Industrial Quality','ISO 9001 / ISO/IEC 17020 principles',2),
  ('TRN-CURR-IND-QA-03','QMOD-IND-QA','IND-QA-03 — Quality Plan and Inspection Test Plan Review','Industrial Quality','Controlled QAP/ITP review, hold and witness points',3),
  ('TRN-CURR-IND-MAT-01','QMOD-IND-MATWELD','IND-MAT-01 — Material Identification, Traceability and Certification','Industrial Materials','Controlled material traceability and certification',1),
  ('TRN-CURR-IND-MAT-02','QMOD-IND-MATWELD','IND-MAT-02 — Chemical, Tensile, Impact and Mechanical Testing','Industrial Materials','Controlled material-test witnessing',2),
  ('TRN-CURR-IND-WELD-01','QMOD-IND-MATWELD','IND-WELD-01 — WPS, PQR and Welder Qualification','Industrial Welding','Controlled welding qualification review and witnessing',3),
  ('TRN-CURR-IND-WELD-02','QMOD-IND-MATWELD','IND-WELD-02 — Consumable Control, Heat Treatment and PWHT','Industrial Welding','Controlled consumable and heat-treatment records',4),
  ('TRN-CURR-IND-NDE-01','QMOD-IND-NDETEST','IND-NDE-01 — Visual, RT, UT, MT and PT Inspection','Industrial NDE','Applicable approved NDE procedures and acceptance criteria',1),
  ('TRN-CURR-IND-NDE-02','QMOD-IND-NDETEST','IND-NDE-02 — NDE Procedure and Personnel Qualification Review','Industrial NDE','Controlled NDE procedure/personnel qualification review',2),
  ('TRN-CURR-IND-TEST-01','QMOD-IND-NDETEST','IND-TEST-01 — Dimensional, Coating and Fabrication Inspection','Industrial Testing','Controlled fabrication and coating inspection',3),
  ('TRN-CURR-IND-TEST-02','QMOD-IND-NDETEST','IND-TEST-02 — Pressure, Load, Shop, Electrical and Factory Acceptance Tests','Industrial Testing','Controlled test witnessing and acceptance',4),
  ('TRN-CURR-IND-REL-01','QMOD-IND-NDETEST','IND-REL-01 — NCR Closure, Packing, Marking and Final Release','Industrial Release','Controlled NCR verification and final release',5)
)
insert into public.trainings
  (training_id,module_id,title,category,standards,target_roles,target_paths,trainer_id,trainer_name,
   slides_link,video_link,reference_link,scorm_package_link,lms_course_id,schedule_date,schedule_time,
   meeting_link,recording_link,passing_marks,validity_months,max_attempts,retest_wait_days,status,created_on,
   updated_on,delivery_mode,duration_hours,location_or_platform,capacity,enrollment_open,course_version,
   prerequisite_text,assessment_required,certificate_required,content_status,minimum_mcqs,
   slides_required,video_required,reference_required,scorm_required,attendance_required,attestation_required)
select training_id,'',title,category,standards,'Industrial Surveyor, Trainee, On Probation','Industrial Surveyor','','',
       '','','','','','','','','',70,36,2,0,'Active',current_timestamp::text,current_timestamp::text,
       'Self-paced',0,'PSB Qualification Workspace',0,'No','1.0','','Yes','Yes','Draft',10,
       'Yes','No','Yes','No','No','Yes'
from src
on conflict (training_id) do update set
  title=excluded.title,category=excluded.category,standards=excluded.standards,target_roles=excluded.target_roles,
  target_paths=excluded.target_paths,status='Active',course_version='1.0',assessment_required='Yes',
  certificate_required='Yes',minimum_mcqs=10,attestation_required='Yes',updated_on=current_timestamp::text;

with src(training_id,module_id,sequence_no) as (values
  ('TRN-CURR-IND-QA-01','QMOD-IND-QA',1),('TRN-CURR-IND-QA-02','QMOD-IND-QA',2),('TRN-CURR-IND-QA-03','QMOD-IND-QA',3),
  ('TRN-CURR-IND-MAT-01','QMOD-IND-MATWELD',1),('TRN-CURR-IND-MAT-02','QMOD-IND-MATWELD',2),('TRN-CURR-IND-WELD-01','QMOD-IND-MATWELD',3),('TRN-CURR-IND-WELD-02','QMOD-IND-MATWELD',4),
  ('TRN-CURR-IND-NDE-01','QMOD-IND-NDETEST',1),('TRN-CURR-IND-NDE-02','QMOD-IND-NDETEST',2),('TRN-CURR-IND-TEST-01','QMOD-IND-NDETEST',3),('TRN-CURR-IND-TEST-02','QMOD-IND-NDETEST',4),('TRN-CURR-IND-REL-01','QMOD-IND-NDETEST',5)
)
insert into public.qualification_module_training
  (module_training_id,module_id,training_id,sequence_no,mandatory,active,created_by,created_on)
select 'QMT-'||training_id,module_id,training_id,sequence_no,'Yes','Yes','controlled-curriculum',current_timestamp::text from src
on conflict (module_training_id) do update set
  module_id=excluded.module_id,training_id=excluded.training_id,sequence_no=excluded.sequence_no,mandatory='Yes',active='Yes';

insert into public.training_assessment_configs
  (assessment_config_id,training_id,title,duration_minutes,passing_score,max_attempts,randomize_questions,
   randomize_answers,show_result_immediately,show_correct_answers,available_from,available_until,active,
   created_by,created_on,updated_on)
select 'TAC-'||training_id,training_id,title||' Knowledge Assessment',30,70,2,'Yes','Yes','Yes',
       'After Final Attempt','','','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text
from public.trainings where training_id like 'TRN-CURR-IND-%'
on conflict (assessment_config_id) do update set
  title=excluded.title,duration_minutes=30,passing_score=70,max_attempts=2,active='Yes',updated_on=current_timestamp::text;

with req(practical_requirement_id,module_id,activity_title) as (values
  ('PWR-IND-QA-01','QMOD-IND-QA-OJT','Vendor / Works Capability Assessment'),
  ('PWR-IND-QA-02','QMOD-IND-QA-OJT','Quality Plan and Inspection Test Plan Review'),
  ('PWR-IND-MAT-01','QMOD-IND-MAT-OJT','Raw Material Identification and Traceability Inspection'),
  ('PWR-IND-MAT-02','QMOD-IND-MAT-OJT','Material Certificate Review'),
  ('PWR-IND-MAT-03','QMOD-IND-MAT-OJT','Chemical Composition Test Witness'),
  ('PWR-IND-MAT-04','QMOD-IND-MAT-OJT','Mechanical / Tensile / Impact Test Witness'),
  ('PWR-IND-WELD-01','QMOD-IND-MAT-OJT','Welding Procedure Specification Review'),
  ('PWR-IND-WELD-02','QMOD-IND-MAT-OJT','Welding Procedure Qualification Test Witness'),
  ('PWR-IND-WELD-03','QMOD-IND-MAT-OJT','Welder Qualification Test Witness'),
  ('PWR-IND-WELD-04','QMOD-IND-MAT-OJT','Welding Consumable Control Inspection'),
  ('PWR-IND-WELD-05','QMOD-IND-MAT-OJT','Heat Treatment / PWHT Record Review'),
  ('PWR-IND-NDE-01','QMOD-IND-NDE-OJT','Fabrication Fit-up and Dimensional Inspection'),
  ('PWR-IND-NDE-02','QMOD-IND-NDE-OJT','Visual Weld Inspection'),
  ('PWR-IND-NDE-03','QMOD-IND-NDE-OJT','Radiographic Testing Witness'),
  ('PWR-IND-NDE-04','QMOD-IND-NDE-OJT','Ultrasonic Testing Witness'),
  ('PWR-IND-NDE-05','QMOD-IND-NDE-OJT','Magnetic Particle Testing Witness'),
  ('PWR-IND-NDE-06','QMOD-IND-NDE-OJT','Dye Penetrant Testing Witness'),
  ('PWR-IND-FAT-01','QMOD-IND-FAT-OJT','Pressure / Hydrostatic Test Witness'),
  ('PWR-IND-FAT-02','QMOD-IND-FAT-OJT','Pneumatic / Leak Test Witness'),
  ('PWR-IND-FAT-03','QMOD-IND-FAT-OJT','Load / Proof Test Witness'),
  ('PWR-IND-FAT-04','QMOD-IND-FAT-OJT','Machinery Shop Test Witness'),
  ('PWR-IND-FAT-05','QMOD-IND-FAT-OJT','Electrical Equipment Routine Test Witness'),
  ('PWR-IND-FAT-06','QMOD-IND-FAT-OJT','Factory Acceptance Test'),
  ('PWR-IND-FAT-07','QMOD-IND-FAT-OJT','Coating Surface Preparation and DFT Inspection'),
  ('PWR-IND-FAT-08','QMOD-IND-FAT-OJT','Packing, Marking and Final Release Inspection'),
  ('PWR-IND-FAT-09','QMOD-IND-FAT-OJT','Non-conformity and Corrective Action Verification')
)
insert into public.qualification_practical_requirements
  (practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,
   mandatory,active,created_by,created_on,updated_on)
select practical_requirement_id,module_id,'Industrial Survey',activity_title,'Guided Practical',1,
       'Controlled Industrial Surveyor practical activity.','Yes','Yes','controlled-curriculum',
       current_timestamp::text,current_timestamp::text
from req
on conflict (practical_requirement_id) do update set
  module_id=excluded.module_id,activity_domain='Industrial Survey',activity_title=excluded.activity_title,
  activity_mode='Guided Practical',required_count=1,mandatory='Yes',active='Yes',updated_on=current_timestamp::text;

insert into public.qualification_practical_requirements
  (practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,
   mandatory,active,created_by,created_on,updated_on)
values
  ('PWR-IND-QA-IP','QMOD-IND-QA-OJT','Industrial Survey','Industrial Quality Planning Final Independent Practical Assessment','Independent Practical',1,'Final independent practical assessment for this scope.','Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text),
  ('PWR-IND-MAT-IP','QMOD-IND-MAT-OJT','Industrial Survey','Industrial Materials and Welding Final Independent Practical Assessment','Independent Practical',1,'Final independent practical assessment for this scope.','Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text),
  ('PWR-IND-NDE-IP','QMOD-IND-NDE-OJT','Industrial Survey','Industrial NDE and Fabrication Final Independent Practical Assessment','Independent Practical',1,'Final independent practical assessment for this scope.','Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text),
  ('PWR-IND-FAT-IP','QMOD-IND-FAT-OJT','Industrial Survey','Industrial Testing and Release Final Independent Practical Assessment','Independent Practical',1,'Final independent practical assessment for this scope.','Yes','Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text)
on conflict (practical_requirement_id) do update set
  module_id=excluded.module_id,activity_domain='Industrial Survey',activity_title=excluded.activity_title,
  activity_mode='Independent Practical',required_count=1,mandatory='Yes',active='Yes',updated_on=current_timestamp::text;

insert into public.module_practical_gates
  (practical_gate_id,module_id,minimum_guided_practical,trainer_satisfaction_required,
   independent_practical_required,active,created_by,created_on,updated_on)
values
  ('MPG-IND-QA','QMOD-IND-QA-OJT',2,'Yes',1,'Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text),
  ('MPG-IND-MAT','QMOD-IND-MAT-OJT',2,'Yes',1,'Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text),
  ('MPG-IND-NDE','QMOD-IND-NDE-OJT',2,'Yes',1,'Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text),
  ('MPG-IND-FAT','QMOD-IND-FAT-OJT',2,'Yes',1,'Yes','controlled-curriculum',current_timestamp::text,current_timestamp::text)
on conflict (practical_gate_id) do update set
  module_id=excluded.module_id,minimum_guided_practical=2,trainer_satisfaction_required='Yes',
  independent_practical_required=1,active='Yes',updated_on=current_timestamp::text;

revoke all on table public.qualification_modules, public.qualification_level_modules,
  public.qualification_module_training, public.qualification_practical_requirements,
  public.module_practical_gates, public.trainings, public.training_assessment_configs
from anon, authenticated;
