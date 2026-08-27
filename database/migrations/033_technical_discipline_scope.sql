-- Gap 19: explicit technical discipline and assignment scope
alter table public.technical_reviews add column if not exists discipline text;
alter table public.technical_review_assignments add column if not exists discipline text;
create index if not exists technical_reviews_discipline_idx on public.technical_reviews(discipline,status);
create index if not exists technical_review_assignments_discipline_idx on public.technical_review_assignments(discipline,status,assigned_reviewer_id);
