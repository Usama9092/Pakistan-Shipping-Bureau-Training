
-- PSB HRDM Supabase Security Template
-- Use with Supabase PostgreSQL. Tables are created automatically by app.
-- Enable RLS manually after mapping Supabase Auth users to your users table.

alter table users enable row level security;
alter table trainings enable row level security;
alter table files enable row level security;
alter table training_records enable row level security;
alter table competency_matrix enable row level security;
alter table authorization_requests enable row level security;
alter table authorization_certificates enable row level security;
alter table job_requests enable row level security;
alter table supervised_logbook enable row level security;
alter table witness_surveys enable row level security;
alter table rule_library enable row level security;
alter table document_versions enable row level security;
alter table capa_register enable row level security;
alter table audit_trail enable row level security;

-- Storage bucket recommended:
-- psb-hrdm-files

-- IMPORTANT:
-- This Streamlit app uses SUPABASE_SERVICE_ROLE_KEY server-side on Render.
-- Never expose this key in browser code or public GitHub.
-- Put it only in Render Environment Variables.
