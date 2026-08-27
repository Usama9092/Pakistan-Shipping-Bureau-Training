-- Management Review action register: child actions, not duplicate review records.
create table if not exists qms_management_review_actions (
    action_id text primary key, review_id text not null, action_text text not null,
    owner_id text, owner_name text, due_date text, status text not null default 'Open',
    progress integer not null default 0, closure_note text, completed_on text,
    created_by text, created_on text, updated_on text
);
create index if not exists qms_mr_actions_review_idx on qms_management_review_actions(review_id);
create index if not exists qms_mr_actions_status_idx on qms_management_review_actions(status, due_date);
