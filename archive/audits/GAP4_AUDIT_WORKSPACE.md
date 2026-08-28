# Gap 4 — True Audit Workspace

The QMS/Lead Auditor experience now opens a dedicated Audit Workspace instead of redirecting the user into the generic QMS page.

## Workspace

Scope & Plan → Evidence → Findings/NCR → Corrective Actions → Verification & Closure

The workspace composes existing authoritative records:
- `qms_audits`
- `qms_evidence_reviews`
- `competency_ncrs`

No duplicate audit or corrective-action store is created.

## Role scope

- QMS Auditor / Lead Auditor: assigned audits.
- QMR / Management / authorized QMS users: enterprise view where permitted.

## Validation

- Dedicated workspace route registered.
- My Audits opens workspace directly.
- Findings map to enterprise NCR/CAPA.
- Evidence maps to QMS Evidence Review.
- Audit outcome updates remain on `qms_audits`.
