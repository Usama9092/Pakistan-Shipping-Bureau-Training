# Technical Reviews Update

## Scope
Unified Technical & Quality review workspace covering Survey Report Review and Plan Review QA.

## Design
- One common `technical_reviews` register and lifecycle.
- Discipline-specific criteria remain separated in the same record.
- Legacy `survey_report_reviews` and `plan_review_quality` records are retained for backward compatibility/history.
- Technical Review results may raise the existing enterprise NCR/CAPA engine; no competing NCR system is created.
- Technical Review is a review/quality workflow, not an authorization workflow. Formal authorization remains in Authorization.

## Frontend
- Executive review metrics.
- Unified register with search and filters.
- Dedicated Survey Report Review form.
- Dedicated Plan Review QA form.
- Review detail view.
- Clear source-of-truth messaging and links to NCR/CAPA.

## Backend
- `technical_reviews` table with discipline-specific fields.
- Indexed by review type, person/scope, status, source record and creation date.
- Audit events for review creation.
- Existing enterprise NCR table reused for adverse outcomes.

## Validation
- Python compilation must pass.
- Both root and `psb_extracted` copies must stay synchronized.
