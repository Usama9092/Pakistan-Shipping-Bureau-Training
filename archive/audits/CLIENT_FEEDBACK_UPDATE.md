# Client Feedback Update

## Purpose
Closed-loop client / shipowner / shipyard feedback linked to jobs, people, performance, NCR/CAPA, annual review and revalidation.

## Workflow
Record feedback -> Review/Respond -> Action/NCR when required -> Close -> Insights -> downstream KPI/annual review consumption.

## Single source of truth
`client_feedback` is authoritative for client feedback. KPI, Annual Review and Revalidation consume it; NCR/CAPA remains the enterprise corrective-action engine.

## Data controls
- Client, person, job, channel, service area, scope, type, rating, sentiment, severity and confidentiality.
- Response/action owner and due date.
- Optional Job and NCR links.
- Status lifecycle: New, Under Review, Responded, Action Required, Closed, Dismissed.
- Audit events for recording, review, NCR creation/linking and closure.

Frontend/back-end: unified register, review workflow, action/NCR linkage, insights, migration and indexes.
