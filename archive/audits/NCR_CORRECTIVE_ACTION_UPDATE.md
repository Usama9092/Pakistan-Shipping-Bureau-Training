# NCR / Corrective Action — Enterprise Update

## Purpose

The NCR / Corrective Action module is now a single enterprise workflow used by Competency, Training, Practical/Witness, QMS, Technical Review, Survey Report Review, Plan Review QA, Client Feedback and Audit processes.

## Ownership model

- Source modules own the underlying finding or event.
- NCR / Corrective Action owns investigation, containment, corrective action, verification and closure.
- Gap Advisor may reference an NCR but does not create a competing NCR workflow.
- Development Plans may be linked to NCR actions but remain the authoritative development workflow.

## Lifecycle

Draft → Open → Containment → Corrective Action → Verification → Closed

Alternative terminal states are Rejected and Cancelled.

## Required controls

- Finding/non-conformance
- Reason for raising
- Source module
- Optional source record ID
- Severity + likelihood → calculated risk score/priority
- Containment
- Root cause
- Corrective action
- Responsible owner
- Due date
- Verification evidence
- Effectiveness result
- Closure notes
- Audit trail for important changes

## Anti-duplication rules

- An open NCR cannot be created again for the same person, source record and category when a source record ID is available.
- Existing Training, Competency, Witness, QMS, Technical Review, Client Feedback and Development Plan records are referenced rather than copied.
- User Profile History remains a filtered view of the central audit trail.

## Production note

Existing `competency_ncrs` records remain compatible. The application performs additive migrations for the new fields and preserves legacy records.
