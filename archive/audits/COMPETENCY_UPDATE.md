# Competency Module Update

The Competency page has been rebuilt as the authoritative competency-readiness workflow.

## Design rules
- Training, CPD, Development Plans, Witness/Supervised activities remain authoritative in their own modules.
- Competency consumes these records as evidence and owns the competency decision.
- Duplicate competency records for the same employee and scope are blocked.
- Competency level is no longer a free-standing administrative field.
- Evidence gaps are calculated from the configured authorization/competency matrix.
- Review decisions are stored in `competency_reviews` and all material changes are audited.

## UI
- Competency Register with filters and readiness status.
- Assess / Review workflow with evidence-aware decisions.
- Evidence & Gaps view aggregating authoritative evidence.
- History view combining competency reviews and audit events.

## Backend
- Added `competency_reviews` table with backward-compatible creation/migration.
- Added readiness calculation from Training Requirements, Training Records, Witness, Supervised Activities and Development Plans.
- Preserved `competency_matrix` as the authoritative current competency record.
