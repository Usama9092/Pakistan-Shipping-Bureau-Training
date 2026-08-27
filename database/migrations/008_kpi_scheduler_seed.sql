insert into kpi_definitions(kpi_id,name,description,formula,weight,target,period_type,source_modules,owner_role,version,effective_from,active,created_on,updated_on) values
('KPI-TRAINING','Training Compliance','Percentage of required training completed on time','completed_required / required_total * 100',0.15,95,'Monthly','Training,Training Matrix','Trainer','1.0','2026-01-01','Yes',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('KPI-TECH','Technical Review Quality','Quality of technical review decisions','accepted_reviews / reviewed_reviews * 100',0.15,95,'Monthly','Technical Reviews','Technical Manager','1.0','2026-01-01','Yes',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('KPI-JOB','Operational Delivery','Completed jobs against planned jobs','completed_jobs / planned_jobs * 100',0.15,90,'Monthly','Job Allocation','Job Coordinator','1.0','2026-01-01','Yes',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
on conflict (name) do nothing;
