# Authorization & Governance — Master Update

## Unified lifecycle
The application now treats authorization as one controlled record and lifecycle:

1. Evidence readiness from Training / Practical / Competency
2. Authorization request
3. Principal review
4. Technical Authority review
5. QMS review
6. CRB decision
7. Management approval
8. Certificate issuance
9. Active restrictions / expiry
10. Annual review
11. Revalidation / suspension / withdrawal

## Single source of truth
Training, CPD, Development Plans, Practical/Witness, Competency and NCR remain authoritative in their own modules. Authorization references those records; it does not recreate them.

## Controls
- Duplicate open authorization requests are prevented for the same person/scope/job type.
- Status transitions are audited.
- Technical Authority and QMS control only their own review gate.
- CRB controls the board decision.
- Management controls final authorization.
- Certificates are issued only after Management Approved.
- Restrictions are attached to authorizations and active restrictions block automatic job assignment until controlled review.
- Revalidation uses live evidence and can revalidate, restrict, suspend or withdraw.
- Certificate public status is revoked when authorization is suspended/withdrawn.
