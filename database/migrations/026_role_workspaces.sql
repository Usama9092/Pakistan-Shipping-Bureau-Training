-- Role workspace completion: formal probation review records.
create table if not exists public.probation_reviews (
    review_id text primary key,
    user_id text,
    name text,
    probation_start text,
    probation_end text,
    objectives text,
    performance_summary text,
    training_status text,
    competency_status text,
    tutor_assessment text,
    decision text,
    decision_notes text,
    reviewer_id text,
    reviewer_name text,
    review_date text,
    status text,
    created_on text,
    updated_on text,
    foreign key (user_id) references public.users(user_id)
);
create index if not exists probation_reviews_user_idx on public.probation_reviews(user_id, status);
create index if not exists probation_reviews_reviewer_idx on public.probation_reviews(reviewer_id, status);

alter table if exists public.authorization_certificates add column if not exists replacement_of text;
alter table if exists public.authorization_certificates add column if not exists replaced_on text;
