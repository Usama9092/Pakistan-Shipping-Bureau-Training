# Job Allocation Update

## Purpose
Job Allocation is the operational assignment engine. It only assigns people whose existing department, competency, authorization, restriction, availability, risk and workload checks pass.

## Workflow
1. Create Job
2. Validate requirements
3. Evaluate candidates
4. Assign a primary assignee
5. Start Job
6. Complete Job
7. Reassign or Cancel with reason

## Single-source-of-truth rules
- Competency remains authoritative in Competency.
- Authorization remains authoritative in Authorization.
- Restrictions remain attached to Authorization and are enforced here.
- KPI remains a performance input.
- Job Allocation stores job and assignment history only.

## Controls
- Department match
- Active account
- Availability
- Minimum competency level
- Valid authorization/scope/job type
- Active authorization restrictions block automatic assignment
- Risk-based KPI threshold for High/Critical jobs
- Active workload limit
- No duplicate active assignment for one job
- Audit event for create/assign/start/complete/reassign/cancel

## Database
- job_requests enhanced with department, client, duration and lifecycle fields.
- job_assignments stores immutable assignment history and eligibility snapshots.


## Client Feedback Integration
Client Feedback is a closed-loop operational quality record. Feedback may reference a Job Allocation record, may create/link one enterprise NCR/CAPA record for complaints/technical concerns, and is consumed by KPI, Annual Review and Revalidation. No duplicate performance or corrective-action system is created.
