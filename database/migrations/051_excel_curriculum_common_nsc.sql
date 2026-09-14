-- Common Foundation + NSC curriculum derived from PSB-PTQ20-F01 and PSB-OJTP10-F04.

INSERT INTO public.qualification_modules
(module_id,module_code,module_name,module_type,description,mandatory,passing_score,evidence_required,assessment_required,practical_observations_required,witness_required,active,created_by,created_on,updated_on,practical_training_required)
VALUES
('QMOD-COMMON-FOUNDATION','COMMON','Common Foundation Training','Theoretical Training','Controlled common foundation for NSC Surveyors, In-Service Surveyors and Plan Appraisers based on PSB-PTQ20-F01 and PSB core requirements.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-NSC-TECH','NSC-TECH','NSC Technical Theory','Theoretical Training','New-building technical theory derived from PSB-PTQ20-F01 Special Modules.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-NSC-NDT','NSC-NDT','NSC NDT Level-II Awareness / Qualification','Theoretical Training','NDE Level-II modules from PSB-PTQ20-F01. Apply where relevant to the surveyor assigned technical scope.','No',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-NSC-HNC','HNC-OJT','Hull New Construction Practical / OJT','Practical Training','Hull new-construction field training and authorization evidence based on F01 field-survey breakup and PSB-OJTP10-F04.','Yes',0,'Yes','Yes',42,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes'),
('QMOD-NSC-MNC','MNC-OJT','Machinery / Electrical New Construction Practical / OJT','Practical Training','Machinery and electrical new-construction field training based on F01 field-survey breakup and PSB-OJTP10-F04.','Yes',0,'Yes','Yes',24,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes')
ON CONFLICT (module_id) DO UPDATE SET module_code=EXCLUDED.module_code,module_name=EXCLUDED.module_name,module_type=EXCLUDED.module_type,description=EXCLUDED.description,mandatory=EXCLUDED.mandatory,passing_score=EXCLUDED.passing_score,evidence_required=EXCLUDED.evidence_required,assessment_required=EXCLUDED.assessment_required,practical_observations_required=EXCLUDED.practical_observations_required,witness_required=EXCLUDED.witness_required,active='Yes',practical_training_required=EXCLUDED.practical_training_required,updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.qualification_level_modules
(level_module_id,level_id,module_id,sequence_no,prerequisite_module_ids,completion_criteria,active,created_by,created_on)
VALUES
('QLM-NSC-COMMON','QL-NSC-1','QMOD-COMMON-FOUNDATION',1,'','Complete all mandatory common theoretical training and assessments.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-NSC-TECH','QL-NSC-2','QMOD-NSC-TECH',1,'QMOD-COMMON-FOUNDATION','Complete NSC technical theory and assessments.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-NSC-NDT','QL-NSC-2','QMOD-NSC-NDT',2,'QMOD-COMMON-FOUNDATION','Complete where assigned to NDT-related scope.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-NSC-HNC','QL-NSC-3','QMOD-NSC-HNC',1,'QMOD-NSC-TECH','Complete F01/F04 hull OJT, Trainer gate and independent practical.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-NSC-MNC','QL-NSC-3','QMOD-NSC-MNC',2,'QMOD-NSC-TECH','Complete F01/F04 machinery/electrical OJT, Trainer gate and independent practical.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text)
ON CONFLICT (level_module_id) DO UPDATE SET level_id=EXCLUDED.level_id,module_id=EXCLUDED.module_id,sequence_no=EXCLUDED.sequence_no,prerequisite_module_ids=EXCLUDED.prerequisite_module_ids,completion_criteria=EXCLUDED.completion_criteria,active='Yes';

WITH src(training_id,title,category,source_ref,duration_hours) AS (VALUES
('TRN-CURR-CORE-001','CORE-001 — PSB Induction and Code of Ethics','Foundation','PSB core curriculum · 2 Hours',2.0),
('TRN-CURR-GMIM1','GMIM1 — Activity and Functions of IMO and Maritime Administrations','Foundation','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-GMCS2','GMCS2 — Activity and Functions of Classification Societies','Foundation','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-GMOI3','GMOI3 — Classification of Ships and Offshore Installations','Foundation','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-GMCR4','GMCR4 — Types of Certificates and Reports Issued on Completion of Surveys','Foundation','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-GMQM5','GMQM5 — Quality Management System','Foundation','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-CORE-004','CORE-004 — ISO/IEC 17020 Inspection Body Requirements','Foundation','PSB core curriculum · 3 Hours',3.0),
('TRN-CURR-CORE-005','CORE-005 — IACS PR7 Training and Qualification Principles','Foundation','PSB core curriculum · 2 Hours',2.0),
('TRN-CURR-GMPS6','GMPS6 — Personal Safety Regulations','Foundation','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-CORE-007','CORE-007 — HSE, Risk Assessment and Site Safety','Foundation','PSB core curriculum · 3 Hours',3.0),
('TRN-CURR-GMLE7','GMLE7 — Legal and Ethical Issues','Foundation','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-CORE-006','CORE-006 — Document Control and Record Retention','Foundation','PSB core curriculum · 2 Hours',2.0),
('TRN-CURR-SMC1-SMC2','SMC1 & SMC2 — Classification and Statutory Surveys – Part A and Part B','Foundation','PSB-PTQ20-F01 · 4 Hours',4.0),
('TRN-CURR-SMF3','SMF3 — Introduction to Flag State Control','Foundation','PSB-PTQ20-F01 · 4 Hours',4.0),
('TRN-CURR-SMDC8','SMDC8 — Drawing Understanding','Foundation','PSB-PTQ20-F01 · 8 Hours',8.0),
('TRN-CURR-CORE-008','CORE-008 — Survey Reporting and Deficiency Management','NSC Technical','PSB core survey curriculum · 3 Hours',3.0),
('TRN-CURR-SMMT4','SMMT4 — Material Testing and Verification','NSC Technical','PSB-PTQ20-F01 · 4 Hours',4.0),
('TRN-CURR-SMW5-SMW6','SMW5 & SMW6 — Welding Inspection, WPS, WQT and PQR','NSC Technical','PSB-PTQ20-F01 · 4 Hours',4.0),
('TRN-CURR-SMRE7','SMRE7 — Walk Through of IACS Recommendation 47','NSC Technical','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-SMHS9','SMHS9 — Hull Structure','NSC Technical','PSB-PTQ20-F01 · 6 Hours',6.0),
('TRN-CURR-SMMR10','SMMR10 — Machinery','NSC Technical','PSB-PTQ20-F01 · 5 Hours',5.0),
('TRN-CURR-SMS11','SMS11 — Stability','NSC Technical','PSB-PTQ20-F01 · 6 Hours',6.0),
('TRN-CURR-SMLL12','SMLL12 — Load Line','NSC Technical','PSB-PTQ20-F01 · 5 Hours',5.0),
('TRN-CURR-SMIT13','SMIT13 — Tonnage','NSC Technical','PSB-PTQ20-F01 · 5 Hours',5.0),
('TRN-CURR-SMSF14','SMSF14 — Structural Fire Protection','NSC Technical','PSB-PTQ20-F01 · 6 Hours',6.0),
('TRN-CURR-SMSE15','SMSE15 — Safety Equipment','NSC Technical','PSB-PTQ20-F01 · 6 Hours',6.0),
('TRN-CURR-SMOP16','SMOP16 — Oil Pollution Prevention','NSC Technical','PSB-PTQ20-F01 · 6 Hours',6.0),
('TRN-CURR-SMNX17','SMNX17 — Noxious Liquid Substances','NSC Technical','PSB-PTQ20-F01 · 5 Hours',5.0),
('TRN-CURR-SMDB18','SMDB18 — Carriage of Dangerous Substances in Bulk','NSC Technical','PSB-PTQ20-F01 · 5 Hours',5.0),
('TRN-CURR-SMRE19','SMRE19 — Radio Equipment','NSC Technical','PSB-PTQ20-F01 · 5 Hours',5.0),
('TRN-CURR-SMLB20','SMLB20 — Carriage of Liquid Substances in Bulk','NSC Technical','PSB-PTQ20-F01 · 6 Hours',6.0),
('TRN-CURR-SMH-M21','SMH&M21 — Guideline on Hull Inspection and Maintenance','NSC Technical','PSB-PTQ20-F01 · 6 Hours',6.0),
('TRN-CURR-SMTM22','SMTM22 — Thickness Measurement Guide','NSC Technical','PSB-PTQ20-F01 · 3 Hours',3.0),
('TRN-CURR-NDDT1','NDDT1 — Dye Penetrant Testing – Level II','NSC NDT','PSB-PTQ20-F01 · 2 Days',0.0),
('TRN-CURR-NDMT2','NDMT2 — Magnetic Particle Testing – Level II','NSC NDT','PSB-PTQ20-F01 · 2 Days',0.0),
('TRN-CURR-NDUT3','NDUT3 — Ultrasonic Testing – Level II','NSC NDT','PSB-PTQ20-F01 · 2 Days',0.0),
('TRN-CURR-NDRT4','NDRT4 — Radiographic Testing – Level II','NSC NDT','PSB-PTQ20-F01 · 2 Days',0.0)
)
INSERT INTO public.trainings
(training_id,module_id,title,category,standards,target_roles,target_paths,trainer_id,trainer_name,slides_link,video_link,reference_link,scorm_package_link,lms_course_id,schedule_date,schedule_time,meeting_link,recording_link,passing_marks,validity_months,max_attempts,retest_wait_days,status,created_on,updated_on,delivery_mode,duration_hours,location_or_platform,capacity,enrollment_open,course_version,prerequisite_text,assessment_required,certificate_required)
SELECT training_id,'',title,category,source_ref,
CASE WHEN category='Foundation' THEN 'Surveyor, NSC Surveyor, In-Service Surveyor, Plan Appraiser, Trainee, On Probation, Trainer' ELSE 'Surveyor, NSC Surveyor, Trainee, On Probation' END,
CASE WHEN category='Foundation' THEN 'NSC Surveyor, In-Service Surveyor, Plan Appraiser' ELSE 'NSC Surveyor' END,
'','','','','','','','','','','',70,36,2,0,'Active',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Self-paced',duration_hours,'PSB Qualification Workspace',0,'Yes','1.0','','Yes','No'
FROM src
ON CONFLICT (training_id) DO UPDATE SET title=EXCLUDED.title,category=EXCLUDED.category,standards=EXCLUDED.standards,target_roles=EXCLUDED.target_roles,target_paths=EXCLUDED.target_paths,passing_marks=70,max_attempts=2,status='Active',delivery_mode='Self-paced',duration_hours=EXCLUDED.duration_hours,location_or_platform='PSB Qualification Workspace',enrollment_open='Yes',assessment_required='Yes',certificate_required='No',updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.training_assessment_configs
(assessment_config_id,training_id,title,duration_minutes,passing_score,max_attempts,randomize_questions,randomize_answers,show_result_immediately,show_correct_answers,available_from,available_until,active,created_by,created_on,updated_on)
SELECT 'TAC-'||training_id,training_id,title||' Knowledge Assessment',30,70,2,'Yes','Yes','Yes','After Final Attempt','','','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text
FROM public.trainings WHERE training_id LIKE 'TRN-CURR-%' AND category IN ('Foundation','NSC Technical','NSC NDT')
ON CONFLICT (assessment_config_id) DO UPDATE SET title=EXCLUDED.title,duration_minutes=30,passing_score=70,max_attempts=2,randomize_questions='Yes',randomize_answers='Yes',active='Yes',updated_on=CURRENT_TIMESTAMP::text;

WITH links(module_training_id,module_id,training_id,sequence_no,mandatory) AS (VALUES
('QMT-COMMON-01','QMOD-COMMON-FOUNDATION','TRN-CURR-CORE-001',1,'Yes'),
('QMT-COMMON-02','QMOD-COMMON-FOUNDATION','TRN-CURR-GMIM1',2,'Yes'),
('QMT-COMMON-03','QMOD-COMMON-FOUNDATION','TRN-CURR-GMCS2',3,'Yes'),
('QMT-COMMON-04','QMOD-COMMON-FOUNDATION','TRN-CURR-GMOI3',4,'Yes'),
('QMT-COMMON-05','QMOD-COMMON-FOUNDATION','TRN-CURR-GMCR4',5,'Yes'),
('QMT-COMMON-06','QMOD-COMMON-FOUNDATION','TRN-CURR-GMQM5',6,'Yes'),
('QMT-COMMON-07','QMOD-COMMON-FOUNDATION','TRN-CURR-CORE-004',7,'Yes'),
('QMT-COMMON-08','QMOD-COMMON-FOUNDATION','TRN-CURR-CORE-005',8,'Yes'),
('QMT-COMMON-09','QMOD-COMMON-FOUNDATION','TRN-CURR-GMPS6',9,'Yes'),
('QMT-COMMON-10','QMOD-COMMON-FOUNDATION','TRN-CURR-CORE-007',10,'Yes'),
('QMT-COMMON-11','QMOD-COMMON-FOUNDATION','TRN-CURR-GMLE7',11,'Yes'),
('QMT-COMMON-12','QMOD-COMMON-FOUNDATION','TRN-CURR-CORE-006',12,'Yes'),
('QMT-COMMON-13','QMOD-COMMON-FOUNDATION','TRN-CURR-SMC1-SMC2',13,'Yes'),
('QMT-COMMON-14','QMOD-COMMON-FOUNDATION','TRN-CURR-SMF3',14,'Yes'),
('QMT-COMMON-15','QMOD-COMMON-FOUNDATION','TRN-CURR-SMDC8',15,'Yes'),
('QMT-NSC-TECH-01','QMOD-NSC-TECH','TRN-CURR-CORE-008',1,'Yes'),
('QMT-NSC-TECH-02','QMOD-NSC-TECH','TRN-CURR-SMMT4',2,'Yes'),
('QMT-NSC-TECH-03','QMOD-NSC-TECH','TRN-CURR-SMW5-SMW6',3,'Yes'),
('QMT-NSC-TECH-04','QMOD-NSC-TECH','TRN-CURR-SMRE7',4,'Yes'),
('QMT-NSC-TECH-05','QMOD-NSC-TECH','TRN-CURR-SMHS9',5,'Yes'),
('QMT-NSC-TECH-06','QMOD-NSC-TECH','TRN-CURR-SMMR10',6,'Yes'),
('QMT-NSC-TECH-07','QMOD-NSC-TECH','TRN-CURR-SMS11',7,'Yes'),
('QMT-NSC-TECH-08','QMOD-NSC-TECH','TRN-CURR-SMLL12',8,'Yes'),
('QMT-NSC-TECH-09','QMOD-NSC-TECH','TRN-CURR-SMIT13',9,'Yes'),
('QMT-NSC-TECH-10','QMOD-NSC-TECH','TRN-CURR-SMSF14',10,'Yes'),
('QMT-NSC-TECH-11','QMOD-NSC-TECH','TRN-CURR-SMSE15',11,'Yes'),
('QMT-NSC-TECH-12','QMOD-NSC-TECH','TRN-CURR-SMOP16',12,'Yes'),
('QMT-NSC-TECH-13','QMOD-NSC-TECH','TRN-CURR-SMNX17',13,'Yes'),
('QMT-NSC-TECH-14','QMOD-NSC-TECH','TRN-CURR-SMDB18',14,'Yes'),
('QMT-NSC-TECH-15','QMOD-NSC-TECH','TRN-CURR-SMRE19',15,'Yes'),
('QMT-NSC-TECH-16','QMOD-NSC-TECH','TRN-CURR-SMLB20',16,'Yes'),
('QMT-NSC-TECH-17','QMOD-NSC-TECH','TRN-CURR-SMH-M21',17,'Yes'),
('QMT-NSC-TECH-18','QMOD-NSC-TECH','TRN-CURR-SMTM22',18,'Yes'),
('QMT-NSC-NDT-01','QMOD-NSC-NDT','TRN-CURR-NDDT1',1,'Yes'),
('QMT-NSC-NDT-02','QMOD-NSC-NDT','TRN-CURR-NDMT2',2,'Yes'),
('QMT-NSC-NDT-03','QMOD-NSC-NDT','TRN-CURR-NDUT3',3,'Yes'),
('QMT-NSC-NDT-04','QMOD-NSC-NDT','TRN-CURR-NDRT4',4,'Yes')
)
INSERT INTO public.qualification_module_training(module_training_id,module_id,training_id,sequence_no,mandatory,active,created_by,created_on)
SELECT module_training_id,module_id,training_id,sequence_no,mandatory,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text FROM links
ON CONFLICT (module_training_id) DO UPDATE SET module_id=EXCLUDED.module_id,training_id=EXCLUDED.training_id,sequence_no=EXCLUDED.sequence_no,mandatory=EXCLUDED.mandatory,active='Yes';

WITH req(practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description) AS (VALUES
('PWR-NSC-HNC-01','QMOD-NSC-HNC','NSC Survey','Material Verification','Guided Practical',3,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-02','QMOD-NSC-HNC','NSC Survey','Block Fabrication / Fit-up Stage','Guided Practical',7,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-03','QMOD-NSC-HNC','NSC Survey','WPS, PQR and WQT Verification','Guided Practical',3,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-04','QMOD-NSC-HNC','NSC Survey','Block Final Welding Stage','Guided Practical',5,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-05','QMOD-NSC-HNC','NSC Survey','Block Erection Stage','Guided Practical',4,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-06','QMOD-NSC-HNC','NSC Survey','Tank Testing – Air / Hydro as per Tank Test Plan','Guided Practical',4,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-07','QMOD-NSC-HNC','NSC Survey','Hydro Test of Piping','Guided Practical',3,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-08','QMOD-NSC-HNC','NSC Survey','Verification of Draught Marks','Guided Practical',3,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-09','QMOD-NSC-HNC','NSC Survey','Verification of Freeboard and Plimsoll Marks','Guided Practical',3,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-10','QMOD-NSC-HNC','NSC Survey','Hull Dimensional Check','Guided Practical',3,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-11','QMOD-NSC-HNC','NSC Survey','Verification / Tightening of Bottom Plugs','Guided Practical',1,'F04 controlled practical item.'),
('PWR-NSC-HNC-12','QMOD-NSC-HNC','NSC Survey','NDT','Guided Practical',3,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-HNC-IP','QMOD-NSC-HNC','NSC Survey','Hull New Construction Final Independent Practical Assessment','Independent Practical',1,'Final independent practical after controlled F01/F04 development.'),
('PWR-NSC-MNC-01','QMOD-NSC-MNC','NSC Survey','Shaft Alignment','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-02','QMOD-NSC-MNC','NSC Survey','Main Engine Alignment','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-03','QMOD-NSC-MNC','NSC Survey','Rudder and Propeller Alignment','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-04','QMOD-NSC-MNC','NSC Survey','Commissioning of Engine Room Equipment – Generators, Pumps, etc.','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-05','QMOD-NSC-MNC','NSC Survey','Generator Load Testing','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-06','QMOD-NSC-MNC','NSC Survey','Cable Installation and Electrical Harness Verification','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-07','QMOD-NSC-MNC','NSC Survey','Limit Switch Verification','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-08','QMOD-NSC-MNC','NSC Survey','Steering Gear Operational Test','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-09','QMOD-NSC-MNC','NSC Survey','Pumping System Operation','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-10','QMOD-NSC-MNC','NSC Survey','Control Room Equipment Verification','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-11','QMOD-NSC-MNC','NSC Survey','Bridge Control Equipment Verification','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-12','QMOD-NSC-MNC','NSC Survey','HATs and SATs','Guided Practical',2,'PSB-PTQ20-F01 / F04 minimum field exposure.'),
('PWR-NSC-MNC-IP','QMOD-NSC-MNC','NSC Survey','Machinery / Electrical New Construction Final Independent Practical Assessment','Independent Practical',1,'Final independent practical after controlled F01/F04 development.')
)
INSERT INTO public.qualification_practical_requirements(practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,mandatory,active,created_by,created_on,updated_on)
SELECT practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text FROM req
ON CONFLICT (practical_requirement_id) DO UPDATE SET module_id=EXCLUDED.module_id,activity_domain=EXCLUDED.activity_domain,activity_title=EXCLUDED.activity_title,activity_mode=EXCLUDED.activity_mode,required_count=EXCLUDED.required_count,description=EXCLUDED.description,mandatory='Yes',active='Yes',updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.module_practical_gates(practical_gate_id,module_id,minimum_guided_practical,trainer_satisfaction_required,independent_practical_required,active,created_by,created_on,updated_on)
VALUES
('MPG-NSC-HNC','QMOD-NSC-HNC',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text),
('MPG-NSC-MNC','QMOD-NSC-MNC',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text)
ON CONFLICT (practical_gate_id) DO UPDATE SET module_id=EXCLUDED.module_id,minimum_guided_practical=EXCLUDED.minimum_guided_practical,trainer_satisfaction_required='Yes',independent_practical_required=1,active='Yes',updated_on=CURRENT_TIMESTAMP::text;
