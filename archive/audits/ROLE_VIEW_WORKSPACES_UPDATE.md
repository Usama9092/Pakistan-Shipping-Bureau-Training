# Role View Workspaces Update

Added role-specific single-source-of-truth workspaces:
- Certificate Center / My Certificates
- My Technical Reviews
- My Audits
- CRB Case Workspace
- Management Review Dashboard
- Formal Probation Review

All reuse existing source records except `probation_reviews`, which is the authoritative record for formal probation decisions.
No duplicate Job, Feedback, KPI, Technical Review, CRB, Authorization, or Certificate databases were created.

Role guardrails:
- self-service users see own/assigned records only
- CRB members see explicitly assigned CRB cases
- Trainer/Tutor workflows remain assigned-person scoped
- Management/QMR use governance dashboards
- probationers can view but cannot decide their own probation review
