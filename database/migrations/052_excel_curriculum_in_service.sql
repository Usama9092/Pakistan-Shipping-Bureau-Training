-- In-Service Surveyor curriculum derived from PSB-PTQ20-F01 and the Existing Ships Survey Authorization Sheet.

INSERT INTO public.qualification_modules
(module_id,module_code,module_name,module_type,description,mandatory,passing_score,evidence_required,assessment_required,practical_observations_required,witness_required,active,created_by,created_on,updated_on,practical_training_required)
VALUES
('QMOD-IS-TECH','IS-TECH','In-Service Technical Theory','Theoretical Training','Technical theory for existing-ship surveys based on PSB-PTQ20-F01 Special Modules.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-IS-PROC','IS-PROC','In-Service Survey Procedures and Checklists','Theoretical Training','Annual, Intermediate and Docking survey checklist training from PSB-PTQ20-F01.','Yes',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-IS-SHIPTYPE','IS-SHIP','Existing-Ship Type Familiarization','Theoretical Training','Ship-type familiarization derived from the Existing Ships Survey Authorization Sheet.','No',70,'No','Yes',0,'No','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'No'),
('QMOD-IS-CLASS','IS-CLASS-OJT','Existing Ship Class / Load Line Practical','Practical Training','Class and Load Line survey practical development derived from the Existing Ships Survey Authorization Sheet.','Yes',0,'Yes','Yes',7,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes'),
('QMOD-IS-SOLAS','IS-SOLAS-OJT','Existing Ship SOLAS Practical','Practical Training','SOLAS survey practical development derived from the Existing Ships Survey Authorization Sheet.','Yes',0,'Yes','Yes',4,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes'),
('QMOD-IS-MARPOL','IS-STAT-OJT','Existing Ship MARPOL / Specialized Statutory Practical','Practical Training','MARPOL, IBC, IGC, MODU, AFS, BWM, IHM and Cargo Gear practical development derived from the Existing Ships Survey Authorization Sheet.','Yes',0,'Yes','Yes',12,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Yes')
ON CONFLICT (module_id) DO UPDATE SET module_code=EXCLUDED.module_code,module_name=EXCLUDED.module_name,module_type=EXCLUDED.module_type,description=EXCLUDED.description,mandatory=EXCLUDED.mandatory,passing_score=EXCLUDED.passing_score,evidence_required=EXCLUDED.evidence_required,assessment_required=EXCLUDED.assessment_required,practical_observations_required=EXCLUDED.practical_observations_required,witness_required=EXCLUDED.witness_required,active='Yes',practical_training_required=EXCLUDED.practical_training_required,updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.qualification_level_modules
(level_module_id,level_id,module_id,sequence_no,prerequisite_module_ids,completion_criteria,active,created_by,created_on)
VALUES
('QLM-IS-COMMON','QL-IS-1','QMOD-COMMON-FOUNDATION',1,'','Complete all mandatory common theoretical training and assessments.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-IS-TECH','QL-IS-2','QMOD-IS-TECH',1,'QMOD-COMMON-FOUNDATION','Complete existing-ship technical theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-IS-PROC','QL-IS-2','QMOD-IS-PROC',2,'QMOD-IS-TECH','Complete Annual, Intermediate and Docking checklist theory.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-IS-SHIPTYPE','QL-IS-2','QMOD-IS-SHIPTYPE',3,'QMOD-COMMON-FOUNDATION','Complete ship-type familiarization where assigned.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-IS-CLASS','QL-IS-3','QMOD-IS-CLASS',1,'QMOD-IS-TECH,QMOD-IS-PROC','Complete class/Load Line practical scope and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-IS-SOLAS','QL-IS-3','QMOD-IS-SOLAS',2,'QMOD-IS-TECH,QMOD-IS-PROC','Complete SOLAS practical scope and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text),
('QLM-IS-MARPOL','QL-IS-3','QMOD-IS-MARPOL',3,'QMOD-IS-TECH,QMOD-IS-PROC','Complete MARPOL/specialized statutory practical scope and independent assessment.','Yes','excel-curriculum',CURRENT_TIMESTAMP::text)
ON CONFLICT (level_module_id) DO UPDATE SET level_id=EXCLUDED.level_id,module_id=EXCLUDED.module_id,sequence_no=EXCLUDED.sequence_no,prerequisite_module_ids=EXCLUDED.prerequisite_module_ids,completion_criteria=EXCLUDED.completion_criteria,active='Yes';

-- The following PSB-PTQ20-F01 courses are shared with NSC and are also applicable to In-Service Surveyors.
UPDATE public.trainings SET target_paths='NSC Surveyor, In-Service Surveyor', target_roles='Surveyor, NSC Surveyor, In-Service Surveyor, Trainee, On Probation', updated_on=CURRENT_TIMESTAMP::text
WHERE training_id IN ('TRN-CURR-CORE-008','TRN-CURR-SMHS9','TRN-CURR-SMMR10','TRN-CURR-SMS11','TRN-CURR-SMLL12','TRN-CURR-SMIT13','TRN-CURR-SMSF14','TRN-CURR-SMSE15','TRN-CURR-SMOP16','TRN-CURR-SMNX17','TRN-CURR-SMDB18','TRN-CURR-SMRE19','TRN-CURR-SMLB20','TRN-CURR-SMH-M21','TRN-CURR-SMTM22');

WITH src(training_id,title,category,source_ref,duration_hours) AS (VALUES
('TRN-CURR-SMAS23','SMAS23 — Theoretical Training on Annual Survey Checklist','In-Service Procedures','PSB-PTQ20-F01 · 8 Hours',8.0),
('TRN-CURR-SMIS24','SMIS24 — Theoretical Training on Intermediate Survey Checklist','In-Service Procedures','PSB-PTQ20-F01 · 8 Hours',8.0),
('TRN-CURR-SMDS25','SMDS25 — Theoretical Training on Docking Survey Checklist','In-Service Procedures','PSB-PTQ20-F01 · 8 Hours',8.0),
('TRN-CURR-IS-SHIP-ALL','All Ships / General Cargo Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-NONSOLAS','Non-SOLAS Ships Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-BULK','Bulk Carriers Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-OILTANKER','Oil Tankers Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-CHEM','Chemical Tankers Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-GAS','Gas Carriers Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-PASSENGER','Passenger Ships Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-HSC','High-Speed Craft Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0),
('TRN-CURR-IS-SHIP-OFFSHORE','Offshore Units Familiarization','In-Service Familiarization','Existing Ships Survey Authorization Sheet',0.0)
)
INSERT INTO public.trainings
(training_id,module_id,title,category,standards,target_roles,target_paths,trainer_id,trainer_name,slides_link,video_link,reference_link,scorm_package_link,lms_course_id,schedule_date,schedule_time,meeting_link,recording_link,passing_marks,validity_months,max_attempts,retest_wait_days,status,created_on,updated_on,delivery_mode,duration_hours,location_or_platform,capacity,enrollment_open,course_version,prerequisite_text,assessment_required,certificate_required)
SELECT training_id,'',title,category,source_ref,'Surveyor, In-Service Surveyor, Trainee, On Probation','In-Service Surveyor','','','','','','','','','','','',70,36,2,0,'Active',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text,'Self-paced',duration_hours,'PSB Qualification Workspace',0,'Yes','1.0','','Yes','No'
FROM src
ON CONFLICT (training_id) DO UPDATE SET title=EXCLUDED.title,category=EXCLUDED.category,standards=EXCLUDED.standards,target_roles=EXCLUDED.target_roles,target_paths=EXCLUDED.target_paths,status='Active',delivery_mode='Self-paced',duration_hours=EXCLUDED.duration_hours,updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.training_assessment_configs
(assessment_config_id,training_id,title,duration_minutes,passing_score,max_attempts,randomize_questions,randomize_answers,show_result_immediately,show_correct_answers,available_from,available_until,active,created_by,created_on,updated_on)
SELECT 'TAC-'||training_id,training_id,title||' Knowledge Assessment',30,70,2,'Yes','Yes','Yes','After Final Attempt','','','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text
FROM public.trainings WHERE category IN ('In-Service Procedures','In-Service Familiarization')
ON CONFLICT (assessment_config_id) DO UPDATE SET title=EXCLUDED.title,duration_minutes=30,passing_score=70,max_attempts=2,active='Yes',updated_on=CURRENT_TIMESTAMP::text;

WITH links(module_training_id,module_id,training_id,sequence_no,mandatory) AS (VALUES
('QMT-IS-TECH-01','QMOD-IS-TECH','TRN-CURR-CORE-008',1,'Yes'),
('QMT-IS-TECH-02','QMOD-IS-TECH','TRN-CURR-SMHS9',2,'Yes'),
('QMT-IS-TECH-03','QMOD-IS-TECH','TRN-CURR-SMMR10',3,'Yes'),
('QMT-IS-TECH-04','QMOD-IS-TECH','TRN-CURR-SMS11',4,'Yes'),
('QMT-IS-TECH-05','QMOD-IS-TECH','TRN-CURR-SMLL12',5,'Yes'),
('QMT-IS-TECH-06','QMOD-IS-TECH','TRN-CURR-SMIT13',6,'Yes'),
('QMT-IS-TECH-07','QMOD-IS-TECH','TRN-CURR-SMSF14',7,'Yes'),
('QMT-IS-TECH-08','QMOD-IS-TECH','TRN-CURR-SMSE15',8,'Yes'),
('QMT-IS-TECH-09','QMOD-IS-TECH','TRN-CURR-SMOP16',9,'Yes'),
('QMT-IS-TECH-10','QMOD-IS-TECH','TRN-CURR-SMNX17',10,'Yes'),
('QMT-IS-TECH-11','QMOD-IS-TECH','TRN-CURR-SMDB18',11,'Yes'),
('QMT-IS-TECH-12','QMOD-IS-TECH','TRN-CURR-SMRE19',12,'Yes'),
('QMT-IS-TECH-13','QMOD-IS-TECH','TRN-CURR-SMLB20',13,'Yes'),
('QMT-IS-TECH-14','QMOD-IS-TECH','TRN-CURR-SMH-M21',14,'Yes'),
('QMT-IS-TECH-15','QMOD-IS-TECH','TRN-CURR-SMTM22',15,'Yes'),
('QMT-IS-PROC-01','QMOD-IS-PROC','TRN-CURR-SMAS23',1,'Yes'),
('QMT-IS-PROC-02','QMOD-IS-PROC','TRN-CURR-SMIS24',2,'Yes'),
('QMT-IS-PROC-03','QMOD-IS-PROC','TRN-CURR-SMDS25',3,'Yes'),
('QMT-IS-SHIP-01','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-ALL',1,'Yes'),
('QMT-IS-SHIP-02','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-NONSOLAS',2,'Yes'),
('QMT-IS-SHIP-03','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-BULK',3,'Yes'),
('QMT-IS-SHIP-04','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-OILTANKER',4,'Yes'),
('QMT-IS-SHIP-05','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-CHEM',5,'Yes'),
('QMT-IS-SHIP-06','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-GAS',6,'Yes'),
('QMT-IS-SHIP-07','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-PASSENGER',7,'Yes'),
('QMT-IS-SHIP-08','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-HSC',8,'Yes'),
('QMT-IS-SHIP-09','QMOD-IS-SHIPTYPE','TRN-CURR-IS-SHIP-OFFSHORE',9,'Yes')
)
INSERT INTO public.qualification_module_training(module_training_id,module_id,training_id,sequence_no,mandatory,active,created_by,created_on)
SELECT module_training_id,module_id,training_id,sequence_no,mandatory,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text FROM links
ON CONFLICT (module_training_id) DO UPDATE SET module_id=EXCLUDED.module_id,training_id=EXCLUDED.training_id,sequence_no=EXCLUDED.sequence_no,mandatory=EXCLUDED.mandatory,active='Yes';

WITH req(practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description) AS (VALUES
('PWR-IS-CLASS-01','QMOD-IS-CLASS','In-Service Survey','Hull and Structure Annual Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-CLASS-02','QMOD-IS-CLASS','In-Service Survey','Hull and Structure Renewal Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-CLASS-03','QMOD-IS-CLASS','In-Service Survey','Bottom / Docking Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-CLASS-04','QMOD-IS-CLASS','In-Service Survey','Machinery and Other Class Surveys','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-CLASS-05','QMOD-IS-CLASS','In-Service Survey','Tailshaft Surveys','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-CLASS-06','QMOD-IS-CLASS','In-Service Survey','Main Boiler Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-CLASS-07','QMOD-IS-CLASS','In-Service Survey','Load Line Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-CLASS-IP','QMOD-IS-CLASS','In-Service Survey','Existing Ship Class / Load Line Final Independent Practical Assessment','Independent Practical',1,'Final independent practical assessment for this scope.'),
('PWR-IS-SOLAS-01','QMOD-IS-SOLAS','In-Service Survey','Safety Construction Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-SOLAS-02','QMOD-IS-SOLAS','In-Service Survey','Safety Equipment Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-SOLAS-03','QMOD-IS-SOLAS','In-Service Survey','Safety Radio Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-SOLAS-04','QMOD-IS-SOLAS','In-Service Survey','Passenger Ship Safety Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-SOLAS-IP','QMOD-IS-SOLAS','In-Service Survey','Existing Ship SOLAS Final Independent Practical Assessment','Independent Practical',1,'Final independent practical assessment for this scope.'),
('PWR-IS-STAT-01','QMOD-IS-MARPOL','In-Service Survey','MARPOL Annex I – Form A','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-02','QMOD-IS-MARPOL','In-Service Survey','MARPOL Annex I – Form B','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-03','QMOD-IS-MARPOL','In-Service Survey','MARPOL Annex II','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-04','QMOD-IS-MARPOL','In-Service Survey','IBC Code – Chemical Tanker Fitness','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-05','QMOD-IS-MARPOL','In-Service Survey','IGC Code – Gas Carrier Fitness','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-06','QMOD-IS-MARPOL','In-Service Survey','Offshore / MODU Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-07','QMOD-IS-MARPOL','In-Service Survey','Anti-Fouling Systems Survey','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-08','QMOD-IS-MARPOL','In-Service Survey','MARPOL Annex IV – Sewage','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-09','QMOD-IS-MARPOL','In-Service Survey','MARPOL Annex VI – Air Pollution','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-10','QMOD-IS-MARPOL','In-Service Survey','International Ballast Water Management','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-11','QMOD-IS-MARPOL','In-Service Survey','Inventory of Hazardous Materials / Recycling of Ships','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-12','QMOD-IS-MARPOL','In-Service Survey','Cargo Gear – ILO 32/152','Guided Practical',1,'Existing Ships Survey Authorization Sheet scope item.'),
('PWR-IS-STAT-IP','QMOD-IS-MARPOL','In-Service Survey','Existing Ship MARPOL / Specialized Statutory Final Independent Practical Assessment','Independent Practical',1,'Final independent practical assessment for this scope.')
)
INSERT INTO public.qualification_practical_requirements(practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,mandatory,active,created_by,created_on,updated_on)
SELECT practical_requirement_id,module_id,activity_domain,activity_title,activity_mode,required_count,description,'Yes','Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text FROM req
ON CONFLICT (practical_requirement_id) DO UPDATE SET module_id=EXCLUDED.module_id,activity_domain=EXCLUDED.activity_domain,activity_title=EXCLUDED.activity_title,activity_mode=EXCLUDED.activity_mode,required_count=EXCLUDED.required_count,description=EXCLUDED.description,mandatory='Yes',active='Yes',updated_on=CURRENT_TIMESTAMP::text;

INSERT INTO public.module_practical_gates(practical_gate_id,module_id,minimum_guided_practical,trainer_satisfaction_required,independent_practical_required,active,created_by,created_on,updated_on)
VALUES
('MPG-IS-CLASS','QMOD-IS-CLASS',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text),
('MPG-IS-SOLAS','QMOD-IS-SOLAS',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text),
('MPG-IS-MARPOL','QMOD-IS-MARPOL',2,'Yes',1,'Yes','excel-curriculum',CURRENT_TIMESTAMP::text,CURRENT_TIMESTAMP::text)
ON CONFLICT (practical_gate_id) DO UPDATE SET module_id=EXCLUDED.module_id,minimum_guided_practical=EXCLUDED.minimum_guided_practical,trainer_satisfaction_required='Yes',independent_practical_required=1,active='Yes',updated_on=CURRENT_TIMESTAMP::text;
