-- Gap 5: formal technical-review assignment lifecycle.
create table if not exists public.technical_review_assignments (
    assignment_id text primary key,
    review_id text not null,
    assigned_reviewer_id text not null,
    assigned_reviewer_name text,
    assigned_by text,
    assigned_by_name text,
    assigned_on text,
    due_date text,
    accepted_on text,
    released_on text,
    status text not null default 'Assigned',
    reason text,
    created_on text,
    updated_on text,
    foreign key (review_id) references public.technical_reviews(review_id),
    foreign key (assigned_reviewer_id) references public.users(user_id)
);
create index if not exists technical_review_assignments_reviewer_idx
    on public.technical_review_assignments(assigned_reviewer_id, status, due_date);
create index if not exists technical_review_assignments_review_idx
    on public.technical_review_assignments(review_id, status);

-- Backfill one explicit current assignment from the existing authoritative reviewer attribution.
insert into public.technical_review_assignments
(assignment_id, review_id, assigned_reviewer_id, assigned_reviewer_name, assigned_by, assigned_by_name,
 assigned_on, due_date, status, reason, created_on, updated_on)
select
    'TRA-' || tr.review_id,
    tr.review_id,
    tr.assigned_reviewer_id,
    coalesce(tr.assigned_reviewer_name, tr.reviewer_name),
    tr.reviewer_id,
    tr.reviewer_name,
    coalesce(tr.created_on, ''),
    coalesce(tr.due_date, ''),
    case when lower(coalesce(tr.status,'')) in ('completed','approved','rejected') then 'Completed' else 'Assigned' end,
    'Backfilled from existing technical review reviewer attribution',
    coalesce(tr.created_on, ''),
    coalesce(tr.updated_on, tr.created_on, '')
from public.technical_reviews tr
where coalesce(tr.assigned_reviewer_id, tr.reviewer_id, '') <> ''
and not exists (
    select 1 from public.technical_review_assignments a where a.review_id = tr.review_id
);
