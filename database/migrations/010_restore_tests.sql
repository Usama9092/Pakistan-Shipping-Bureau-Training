create table if not exists restore_tests (
    test_id text primary key,
    restore_point text,
    tested_on text,
    tested_by text,
    status text,
    duration_minutes integer,
    findings text,
    corrective_action text,
    created_on text
);
create index if not exists restore_tests_date_idx on restore_tests(tested_on, status);
