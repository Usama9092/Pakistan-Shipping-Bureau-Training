-- Pakistan Shipping Bureau HRDM Supabase RLS Template
-- App creates tables automatically. Use this template after linking Supabase Auth.
-- Enable row level security on all application tables before adding policies.

alter table users enable row level security;
alter table training_modules enable row level security;
alter table trainings enable row level security;
alter table files enable row level security;
alter table training_records enable row level security;
alter table question_bank enable row level security;
alter table assessment_history enable row level security;
alter table competency_matrix enable row level security;
alter table authorization_matrix enable row level security;
alter table development_plans enable row level security;
alter table field_exposure_matrix enable row level security;
alter table witness_surveys enable row level security;
alter table supervised_activities enable row level security;
alter table authorization_requests enable row level security;
alter table authorization_certificates enable row level security;
alter table crb_reviews enable row level security;
alter table annual_reviews enable row level security;
alter table revalidation_requests enable row level security;
alter table job_requests enable row level security;
alter table kpi_records enable row level security;
alter table cpd_records enable row level security;
alter table knowledge_library enable row level security;
alter table knowledge_acknowledgements enable row level security;
alter table rule_library enable row level security;
alter table document_versions enable row level security;
alter table capa_register enable row level security;
alter table notifications enable row level security;
alter table audit_trail enable row level security;
alter table technical_authorities enable row level security;
alter table survey_report_reviews enable row level security;
alter table plan_review_quality enable row level security;
alter table competency_ncrs enable row level security;
alter table authorization_restrictions enable row level security;
alter table client_feedback enable row level security;
alter table succession_plans enable row level security;
alter table workforce_forecasts enable row level security;
alter table accreditation_evidence enable row level security;
alter table technical_interpretations enable row level security;

-- Important:
-- Keep SUPABASE_SERVICE_ROLE_KEY only in Render environment variables.
-- Do not commit service role keys to GitHub.
