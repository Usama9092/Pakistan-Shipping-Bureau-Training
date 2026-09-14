-- Plan Appraisal curriculum derived from PSB-PTQ20-F01 and PSB-OJTP10-F05.

INSERT INTO public.qualification_modules
(module_id,module_code,module_name,module_type,description,mandatory,passing_score,evidence_required,assessment_required,practical_observations_required,witness_required,active,created_by,created_on,updated_on,practical_training_required)
VALUES
('QMOD-PA-CORE','PA-CORE','Plan Appraisal Core','Theoretical Training','Core plan-appraisal rule interpretation and approval workflow.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-PA-STAT','PA-STAT','Plan Appraisal – Statutory','Theoretical Training','Statutory plan-appraisal subjects from PSB-OJTP10-F05.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-PA-HULL','PA-HULL','Plan Appraisal – Hull Structure','Theoretical Training','Hull structure plan-appraisal authorization subjects from PSB-OJTP10-F05.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-PA-MACH','PA-MACH','Plan Appraisal – Machinery','Theoretical Training','Machinery plan-appraisal authorization subjects from PSB-OJTP10-F05 and the theoretical seminar list.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-PA-ELEC','PA-ELEC','Plan Appraisal – Electrical','Theoretical Training','Electrical plan-appraisal authorization subjects from PSB-OJTP10-F05 and the theoretical seminar list.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-PA-STAB','PA-STAB','Plan Appraisal – Stability','Theoretical Training','Stability, longitudinal strength, inclining, freeboard and tonnage subjects from PSB-OJTP10-F05 and the theoretical seminar list.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-PA-PSTAT','PSTAT','Plan Appraisal Statutory Practical','Practical Training','Supervised and independent statutory plan-appraisal practical work linked to PSB-OJTP10-F05.','Yes',0,'Yes','Yes',10,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes'),
('QMOD-PA-PHULL','PHULL','Plan Appraisal Hull Practical','Practical Training','Supervised and independent hull plan-appraisal practical work linked to PSB-OJTP10-F05.','Yes',0,'Yes','Yes',5,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes'),
('QMOD-PA-PMACH','PMACH','Plan Appraisal Machinery Practical','Practical Training','Supervised and independent machinery plan-appraisal practical work linked to PSB-OJTP10-F05.','Yes',0,'Yes','Yes',13,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes'),
('QMOD-PA-PELEC','PELEC','Plan Appraisal Electrical Practical','Practical Training','Supervised and independent electrical plan-appraisal practical work linked to PSB-OJTP10-F05.','Yes',0,'Yes','Yes',5,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes'),
('QMOD-PA-PSTAB','PSTAB','Plan Appraisal Stability Practical','Practical Training','Supervised and independent stability plan-appraisal practical work linked to PSB-OJTP10-F05.','Yes',0,'Yes','Yes',10,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes')
ON CONFLICT (module_id) DO UPDATE SET module_code=EXCLUDED.module_code,module_name=EXCLUDED.module_name,module_type=EXCLUDED.module_type,description=EXCLUDED.description,mandatory=EXCLUDED.mandatory,passing_score=EXCLUDED.passing_score,evidence_required=EXCLUDED.evidence_required,assessment_required=EXCLUDED.assessment_required,practical_observations_required=EXCLUDED.practical_observations_required,witness_required=EXCLUDED.witness_required,active='Yes',practical_training_required=EXCLUDED.practical_training_required,updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.qualification_level_modules
(level_module_id,level_id,module_id,sequence_no,prerequisite_module_ids,completion_criteria,active,created_by,created_on)
VALUES
('QLM-PA-COMMON','QL-PA-1','QMOD-COMMON-FOUNDATION',1,'','Complete all mandatory common theoretical training and assessments.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-CORE','QL-PA-2','QMOD-PA-CORE',1,'QMOD-COMMON-FOUNDATION','Complete plan appraisal core theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-STAT','QL-PA-2','QMOD-PA-STAT',2,'QMOD-PA-CORE','Complete statutory plan appraisal theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-HULL','QL-PA-2','QMOD-PA-HULL',3,'QMOD-PA-CORE','Complete hull structure plan appraisal theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-MACH','QL-PA-2','QMOD-PA-MACH',4,'QMOD-PA-CORE','Complete machinery plan appraisal theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-ELEC','QL-PA-2','QMOD-PA-ELEC',5,'QMOD-PA-CORE','Complete electrical plan appraisal theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-STAB','QL-PA-2','QMOD-PA-STAB',6,'QMOD-PA-CORE','Complete stability plan appraisal theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-PSTAT','QL-PA-3','QMOD-PA-PSTAT',1,'QMOD-PA-STAT','Complete statutory plan appraisal practical work and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-PHULL','QL-PA-3','QMOD-PA-PHULL',2,'QMOD-PA-HULL','Complete hull plan appraisal practical work and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-PMACH','QL-PA-3','QMOD-PA-PMACH',3,'QMOD-PA-MACH','Complete machinery plan appraisal practical work and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-PELEC','QL-PA-3','QMOD-PA-PELEC',4,'QMOD-PA-ELEC','Complete electrical plan appraisal practical work and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-PA-PSTAB','QL-PA-3','QMOD-PA-PSTAB',5,'QMOD-PA-STAB','Complete stability plan appraisal practical work and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text)
ON CONFLICT (level_module_id) DO UPDATE SET level_id=EXCLUDED.level_id,module_id=EXCLUDED.module_id,sequence_no=EXCLUDED.sequence_no,prerequisite_module_ids=EXCLUDED.prerequisite_module_ids,completion_criteria=EXCLUDED.completion_criteria,active='Yes';

WITH src(training_id,title,category,source_ref) AS (VALUES
('TRN-CURR-PLAN-001','PLAN-001 — Plan Appraisal Rule Interpretation','Plan Appraisal Core','PSB Plan Appraisal curriculum'),
('TRN-CURR-PLAN-002','PLAN-002 — Plan Review Commenting and Approval Workflow','Plan Appraisal Core','PSB Plan Appraisal curriculum'),
('TRN-CURR-S1-S2','S1 & S2 — MARPOL Annex I, IV and V','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-S9','S9 — Damage Control Plan','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-S10','S10 — Freeboard Plan','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-F2','F2 — Water Fire Fighting System for All Ships','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-F3','F3 — Fixed Gas Fire Extinguishing Systems','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-F4','F4 — Fixed Gas Fire Extinguishing Systems Other Than CO₂','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-F5','F5 — Pressure Water Spraying System','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-F6','F6 — Fixed Foam Fire Extinguishing System','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-F8','F8 — Structural Fire Protection / Escape Plan','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-F9','F9 — Fire Control Plan','Plan Appraisal Statutory','PSB-OJTP10-F05'),
('TRN-CURR-GHQ','GHQ — Basic Hull Approval','Plan Appraisal Hull','PSB-OJTP10-F05'),
('TRN-CURR-VT','VT — Oil Tankers','Plan Appraisal Hull','PSB-OJTP10-F05'),
('TRN-CURR-NS','NS — Naval Ships','Plan Appraisal Hull','PSB-OJTP10-F05'),
('TRN-CURR-HSC','HSC — High-Speed Craft','Plan Appraisal Hull','PSB-OJTP10-F05'),
('TRN-CURR-VB','VB — Barges','Plan Appraisal Hull','PSB-OJTP10-F05'),
('TRN-CURR-M1','M1 — Internal Combustion Engines and Air Compressors','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-M4','M4 — Propellers','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-M5','M5 — Main Shafting, Propeller Brackets and Stern Tube','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-M8','M8 — Chockfast Foundation and Calculations','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-M9','M9 — Torsional Vibration Calculation','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-M10','M10 — Shaft Alignment','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-M12','M12 — Rudder and Maneuvering Arrangement','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-M13','M13 — General Strength','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-V1','V1 — Accommodation Spaces – HVAC','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-V2','V2 — Engine Room / Pump Room / Cargo Holds / Battery Room / Other Spaces Ventilation','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-HC','HC — Hull Outfitting – Internal / External Openings','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-P1','P1 — Pipe Components','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-P2','P2 — Piping Systems – General','Plan Appraisal Machinery','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-E1','E1 — Electrical Power Supply Systems','Plan Appraisal Electrical','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-E6','E6 — Ship Safety Systems','Plan Appraisal Electrical','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-E9','E9 — Main and Emergency Lighting Systems','Plan Appraisal Electrical','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-E16','E16 — Electrical Equipment Installations in Hazardous Areas','Plan Appraisal Electrical','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-E17','E17 — Navigation and Signalling Lights, Shapes and Sound Signals','Plan Appraisal Electrical','PSB-OJTP10-F05'),
('TRN-CURR-ISO','ISO — Introduction to Ship Stability','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-IS1','IS1 — Intact Stability of Cargo and Passenger Ships','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-IS3','IS3 — Intact Stability of Naval Ships','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-LSC','LSC — Longitudinal Strength Calculation','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-IE','IE — Inclining Experiment','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-DS','DS — Introduction to Damaged Stability','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-DS4','DS4 — Damaged Stability of High-Speed Craft','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-DS6','DS6 — Damaged Stability of Naval Ships','Plan Appraisal Stability','PSB-PTQ20-F01 / PSB-OJTP10-F05 · 3 Days'),
('TRN-CURR-LL','LL — Freeboard Computation','Plan Appraisal Stability','PSB-OJTP10-F05'),
('TRN-CURR-TM','TM — Tonnage Measurement','Plan Appraisal Stability','PSB-OJTP10-F05')
)
INSERT INTO public.trainings
(training_id,module_id,title,category,standards,target_roles,target_paths,trainer_id,trainer_name,slides_link,video_link,reference_link,scorm_package_link,lms_course_id,schedule_date,schedule_time,meeting_link,recording_link,passing_marks,validity_months,max_attempts,retest_wait_days,status,created_on,updated_on,delivery_mode,duration_hours,location_or_platform,capacity,enrollment_open,course_version,prerequisite_text,assessment_required,certificate_required)
SELECT training_id,'',title,category,source_ref,'Plan Appraiser, Trainee, On Probation','Plan Appraiser','','','','','','','','','','','',70,36,2,0,'Active',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Self-paced',0,'PSB Qualification Workspace',0,'Yes','1.0','','Yes','No'
FROM src
ON CONFLICT (training_id) DO UPDATE SET title=EXCLUDED.title,category=EXCLUDED.category,standards=EXCLUDED.standards,target_roles=EXCLUDED.target_roles,target_paths=EXCLUDED.target_paths,status='Active',delivery_mode='Self-paced',updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.training_assessment_configs
(assessment_config_id,training_id,title,duration_minutes,passing_score,max_attempts,randomize_questions,randomize_answers,show_result_immediately,show_correct_answers,available_from,available_until,active,created_by,created_on,updated_on)
SELECT 'TAC-'||training_id,training_id,title||' Knowledge Assessment',30,70,2,'Yes','Yes','Yes','After Final Attempt','','','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text
FROM public.trainings WHERE category LIKE 'Plan Appraisal%'
ON CONFLICT (assessment_config_id) DO UPDATE SET title=EXCLUDED.title,duration_minutes=30,passing_score=70,max_attempts=2,active='Yes',updated_on=CURRENT_TIMESTAMP::text;

WITH links(module_training_id,module_id,training_id,sequence_no,mandatory) AS (VALUES
('QMT-PA-CORE-01','QMOD-PA-CORE','TRN-CURR-PLAN-001',1,'Yes'),
('QMT-PA-CORE-02','QMOD-PA-CORE','TRN-CURR-PLAN-002',2,'Yes'),
('QMT-PA-STAT-01','QMOD-PA-STAT','TRN-CURR-S1-S2',1,'Yes'),
('QMT-PA-STAT-02','QMOD-PA-STAT','TRN-CURR-S9',2,'Yes'),
('QMT-PA-STAT-03','QMOD-PA-STAT','TRN-CURR-S10',3,'Yes'),
('QMT-PA-STAT-04','QMOD-PA-STAT','TRN-CURR-F2',4,'Yes'),
('QMT-PA-STAT-05','QMOD-PA-STAT','TRN-CURR-F3',5,'Yes'),
('QMT-PA-STAT-06','QMOD-PA-STAT','TRN-CURR-F4',6,'Yes'),
('QMT-PA-STAT-07','QMOD-PA-STAT','TRN-CURR-F5',7,'Yes'),
('QMT-PA-STAT-08','QMOD-PA-STAT','TRN-CURR-F6',8,'Yes'),
('QMT-PA-STAT-09','QMOD-PA-STAT','TRN-CURR-F8',9,'Yes'),
('QMT-PA-STAT-10','QMOD-PA-STAT','TRN-CURR-F9',10,'Yes'),
('QMT-PA-HULL-01','QMOD-PA-HULL','TRN-CURR-GHQ',1,'Yes'),
('QMT-PA-HULL-02','QMOD-PA-HULL','TRN-CURR-VT',2,'Yes'),
('QMT-PA-HULL-03','QMOD-PA-HULL','TRN-CURR-NS',3,'Yes'),
('QMT-PA-HULL-04','QMOD-PA-HULL','TRN-CURR-HSC',4,'Yes'),
('QMT-PA-HULL-05','QMOD-PA-HULL','TRN-CURR-VB',5,'Yes'),
('QMT-PA-MACH-01','QMOD-PA-MACH','TRN-CURR-M1',1,'Yes'),
('QMT-PA-MACH-02','QMOD-PA-MACH','TRN-CURR-M4',2,'Yes'),
('QMT-PA-MACH-03','QMOD-PA-MACH','TRN-CURR-M5',3,'Yes'),
('QMT-PA-MACH-04','QMOD-PA-MACH','TRN-CURR-M8',4,'Yes'),
('QMT-PA-MACH-05','QMOD-PA-MACH','TRN-CURR-M9',5,'Yes'),
('QMT-PA-MACH-06','QMOD-PA-MACH','TRN-CURR-M10',6,'Yes'),
('QMT-PA-MACH-07','QMOD-PA-MACH','TRN-CURR-M12',7,'Yes'),
('QMT-PA-MACH-08','QMOD-PA-MACH','TRN-CURR-M13',8,'Yes'),
('QMT-PA-MACH-09','QMOD-PA-MACH','TRN-CURR-V1',9,'Yes'),
('QMT-PA-MACH-10','QMOD-PA-MACH','TRN-CURR-V2',10,'Yes'),
('QMT-PA-MACH-11','QMOD-PA-MACH','TRN-CURR-HC',11,'Yes'),
('QMT-PA-MACH-12','QMOD-PA-MACH','TRN-CURR-P1',12,'Yes'),
('QMT-PA-MACH-13','QMOD-PA-MACH','TRN-CURR-P2',13,'Yes'),
('QMT-PA-ELEC-01','QMOD-PA-ELEC','TRN-CURR-E1',1,'Yes'),
('QMT-PA-ELEC-02','QMOD-PA-ELEC','TRN-CURR-E6',2,'Yes'),
('QMT-PA-ELEC-03','QMOD-PA-ELEC','TRN-CURR-E9',3,'Yes'),
('QMT-PA-ELEC-04','QMOD-PA-ELEC','TRN-CURR-E16',4,'Yes'),
('QMT-PA-ELEC-05','QMOD-PA-ELEC','TRN-CURR-E17',5,'Yes'),
('QMT-PA-STAB-01','QMOD-PA-STAB','TRN-CURR-ISO',1,'Yes'),
('QMT-PA-STAB-02','QMOD-PA-STAB','TRN-CURR-IS1',2,'Yes'),
('QMT-PA-STAB-03','QMOD-PA-STAB','TRN-CURR-IS3',3,'Yes'),
('QMT-PA-STAB-04','QMOD-PA-STAB','TRN-CURR-LSC',4,'Yes'),
('QMT-PA-STAB-05','QMOD-PA-STAB','TRN-CURR-IE',5,'Yes'),
('QMT-PA-STAB-06','QMOD-PA-STAB','TRN-CURR-DS',6,'Yes'),
('QMT-PA-STAB-07','QMOD-PA-STAB','TRN-CURR-DS4',7,'Yes'),
('QMT-PA-STAB-08','QMOD-PA-STAB','TRN-CURR-DS6',8,'Yes'),
('QMT-PA-STAB-09','QMOD-PA-STAB','TRN-CURR-LL',9,'Yes'),
('QMT-PA-STAB-10','QMOD-PA-STAB','TRN-CURR-TM',10,'Yes')
)
INSERT INTO public.qualification_module_training(module_training_id,module_id,training_id,sequence_no,mandatory,active,created_by,created_on)
SELECT module_training_id,module_id,training_id,sequence_no,mandatory,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text FROM links
ON CONFLICT (module_training_id) DO UPDATE SET module_id=EXCLUDED.module_id,training_id=EXCLUDED.training_id,sequence_no=EXCLUDED.sequence_no,mandatory=EXCLUDED.mandatory,active='Yes';

WITH req(practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description) AS (VALUES
('PWR-PA-STAT-01','QMOD-PA-PSTAT','Plan Appraisal','MARPOL Annex I, IV and V','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-02','QMOD-PA-PSTAT','Plan Appraisal','Damage Control Plan','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-03','QMOD-PA-PSTAT','Plan Appraisal','Freeboard Plan','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-04','QMOD-PA-PSTAT','Plan Appraisal','Water Fire Fighting System for All Ships','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-05','QMOD-PA-PSTAT','Plan Appraisal','Fixed Gas Fire Extinguishing Systems','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-06','QMOD-PA-PSTAT','Plan Appraisal','Fixed Gas Fire Extinguishing Systems Other Than CO₂','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-07','QMOD-PA-PSTAT','Plan Appraisal','Pressure Water Spraying System','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-08','QMOD-PA-PSTAT','Plan Appraisal','Fixed Foam Fire Extinguishing System','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-09','QMOD-PA-PSTAT','Plan Appraisal','Structural Fire Protection / Escape Plan','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-10','QMOD-PA-PSTAT','Plan Appraisal','Fire Control Plan','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAT-IP','QMOD-PA-PSTAT','Plan Appraisal','Plan Appraisal Statutory Final Independent Practical Assessment','Independent Practical',1,'Final independent plan-appraisal assessment.'),
('PWR-PA-HULL-01','QMOD-PA-PHULL','Plan Appraisal','Basic Hull Approval','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-HULL-02','QMOD-PA-PHULL','Plan Appraisal','Oil Tankers','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-HULL-03','QMOD-PA-PHULL','Plan Appraisal','Naval Ships','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-HULL-04','QMOD-PA-PHULL','Plan Appraisal','High-Speed Craft','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-HULL-05','QMOD-PA-PHULL','Plan Appraisal','Barges','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-HULL-IP','QMOD-PA-PHULL','Plan Appraisal','Plan Appraisal Hull Final Independent Practical Assessment','Independent Practical',1,'Final independent plan-appraisal assessment.'),
('PWR-PA-MACH-01','QMOD-PA-PMACH','Plan Appraisal','Internal Combustion Engines and Air Compressors','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-02','QMOD-PA-PMACH','Plan Appraisal','Propellers','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-03','QMOD-PA-PMACH','Plan Appraisal','Main Shafting, Propeller Brackets and Stern Tube','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-04','QMOD-PA-PMACH','Plan Appraisal','Chockfast Foundation and Calculations','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-05','QMOD-PA-PMACH','Plan Appraisal','Torsional Vibration Calculation','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-06','QMOD-PA-PMACH','Plan Appraisal','Shaft Alignment','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-07','QMOD-PA-PMACH','Plan Appraisal','Rudder and Maneuvering Arrangement','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-08','QMOD-PA-PMACH','Plan Appraisal','General Strength','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-09','QMOD-PA-PMACH','Plan Appraisal','Accommodation Spaces – HVAC','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-10','QMOD-PA-PMACH','Plan Appraisal','Engine Room / Pump Room / Cargo Holds / Battery Room / Other Spaces Ventilation','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-11','QMOD-PA-PMACH','Plan Appraisal','Hull Outfitting – Internal / External Openings','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-12','QMOD-PA-PMACH','Plan Appraisal','Pipe Components','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-13','QMOD-PA-PMACH','Plan Appraisal','Piping Systems – General','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-MACH-IP','QMOD-PA-PMACH','Plan Appraisal','Plan Appraisal Machinery Final Independent Practical Assessment','Independent Practical',1,'Final independent plan-appraisal assessment.'),
('PWR-PA-ELEC-01','QMOD-PA-PELEC','Plan Appraisal','Electrical Power Supply Systems','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-ELEC-02','QMOD-PA-PELEC','Plan Appraisal','Ship Safety Systems','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-ELEC-03','QMOD-PA-PELEC','Plan Appraisal','Main and Emergency Lighting Systems','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-ELEC-04','QMOD-PA-PELEC','Plan Appraisal','Electrical Equipment Installations in Hazardous Areas','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-ELEC-05','QMOD-PA-PELEC','Plan Appraisal','Navigation and Signalling Lights, Shapes and Sound Signals','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-ELEC-IP','QMOD-PA-PELEC','Plan Appraisal','Plan Appraisal Electrical Final Independent Practical Assessment','Independent Practical',1,'Final independent plan-appraisal assessment.'),
('PWR-PA-STAB-01','QMOD-PA-PSTAB','Plan Appraisal','Introduction to Ship Stability','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-02','QMOD-PA-PSTAB','Plan Appraisal','Intact Stability of Cargo and Passenger Ships','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-03','QMOD-PA-PSTAB','Plan Appraisal','Intact Stability of Naval Ships','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-04','QMOD-PA-PSTAB','Plan Appraisal','Longitudinal Strength Calculation','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-05','QMOD-PA-PSTAB','Plan Appraisal','Inclining Experiment','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-06','QMOD-PA-PSTAB','Plan Appraisal','Introduction to Damaged Stability','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-07','QMOD-PA-PSTAB','Plan Appraisal','Damaged Stability of High-Speed Craft','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-08','QMOD-PA-PSTAB','Plan Appraisal','Damaged Stability of Naval Ships','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-09','QMOD-PA-PSTAB','Plan Appraisal','Freeboard Computation','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-10','QMOD-PA-PSTAB','Plan Appraisal','Tonnage Measurement','Guided Practical',1,'PSB-OJTP10-F05 authorization item.'),
('PWR-PA-STAB-IP','QMOD-PA-PSTAB','Plan Appraisal','Plan Appraisal Stability Final Independent Practical Assessment','Independent Practical',1,'Final independent plan-appraisal assessment.')
)
INSERT INTO public.qualification_practical_requirements(practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,mandatory,active,created_by,created_on,updated_on)
SELECT practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text FROM req
ON CONFLICT (practical_requirement_id) DO UPDATE SET module_id=EXCLUDED.module_id,activity_domain=EXCLUDED.activity_domain,activity_title=EXCLUDED.activity_title,activity_mode=EXCLUDED.activity_mode,required_count=EXCLUDED.required_count,description=EXCLUDED.description,mandatory='Yes',active='Yes',updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.module_practical_gates(practical_gate_id,module_id,minimum_guided_practical,trainer_satisfaction_required,independent_practical_required,active,created_by,created_on,updated_on)
VALUES
('MPG-PA-PSTAT','QMOD-PA-PSTAT',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text),
('MPG-PA-PHULL','QMOD-PA-PHULL',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text),
('MPG-PA-PMACH','QMOD-PA-PMACH',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text),
('MPG-PA-PELEC','QMOD-PA-PELEC',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text),
('MPG-PA-PSTAB','QMOD-PA-PSTAB',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text)
ON CONFLICT (practical_gate_id) DO UPDATE SET module_id=EXCLUDED.module_id,minimum_guided_practical=EXCLUDED.minimum_guided_practical,trainer_satisfaction_required='Yes',independent_practical_required=1,active='Yes',updated_on=CURRENT_TIMESTAMP::text;
