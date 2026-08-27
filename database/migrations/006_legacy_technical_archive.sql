create table if not exists deprecated_table_registry (table_name text primary key, replacement_table text, deprecation_status text, notes text, registered_on text);
insert into deprecated_table_registry(table_name,replacement_table,deprecation_status,notes,registered_on) values
('survey_report_reviews','technical_reviews','deprecated','Retained for historical data migration only; no application writes.','' || CURRENT_TIMESTAMP),
('plan_review_quality','technical_reviews','deprecated','Retained for historical data migration only; no application writes.','' || CURRENT_TIMESTAMP) on conflict (table_name) do nothing;
