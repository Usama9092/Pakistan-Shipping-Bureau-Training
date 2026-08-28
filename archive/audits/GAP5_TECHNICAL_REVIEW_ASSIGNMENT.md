# Gap 5 — Formal Technical Review Assignment

Implemented a formal assignment lifecycle for the unified Technical Reviews workflow.

## Source of truth
- `technical_reviews` remains the authoritative review record.
- `technical_review_assignments` records who is assigned, when, due date, acceptance/release state, and assignment history.

## Role behavior
- Surveyor / Industrial Surveyor / Plan Appraiser / Principal Surveyor / Chief Plan Appraiser use explicit current assignment records for My Technical Reviews.
- Historical `reviewer_id` or `user_id` attribution alone no longer grants the self-service work view.

## Creation behavior
New Survey Report Reviews and Plan Review QA records create an explicit assignment record at creation time, with the acting reviewer as the assigned reviewer by default.

## Security
The assignment table is server-mediated with RLS enabled and direct browser privileges revoked.

## Validation
- Root tests: 80/80
- Embedded application tests: 80/80 after synchronization
- Gap 5 regression: PASS
