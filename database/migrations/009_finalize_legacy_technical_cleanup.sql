do $$ begin
    if to_regclass('public.survey_report_reviews') is not null then
        alter table public.survey_report_reviews rename to legacy_survey_report_reviews;
    end if;
    if to_regclass('public.plan_review_quality') is not null then
        alter table public.plan_review_quality rename to legacy_plan_review_quality;
    end if;
end $$;
insert into deprecated_table_registry(table_name,replacement_table,deprecation_status,notes,registered_on) values
('legacy_survey_report_reviews','technical_reviews','archived','Legacy data preserved after unified technical review migration.',CURRENT_TIMESTAMP),
('legacy_plan_review_quality','technical_reviews','archived','Legacy data preserved after unified technical review migration.',CURRENT_TIMESTAMP)
on conflict (table_name) do nothing;
