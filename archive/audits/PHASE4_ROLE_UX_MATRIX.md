# Phase 4 — Role-wise UX Consistency Matrix

All roles use the same PSB design system. Role differences are limited to navigation, permissions, data visibility and primary actions.

| Role | Primary focus | Primary modules | Design treatment |
|---|---|---|---|
| Admin | identity, access, governance | Administration + full read access | same layout; Admin role badge and governance cues |
| Trainer | training delivery | Training & Competency | same cards/forms/tables; trainer actions emphasized |
| Tutor/Mentor | development and evidence | People + Training/Competency | same components; mentoring actions emphasized |
| Surveyor | authorized field work | Training/Competency + Authorization | same components; readiness and scope cues |
| Plan Appraiser | plan appraisal | Training/Competency + Authorization | same components; plan review cues |
| QMS Auditor/QMR | quality governance | Technical & Quality + NCR | same components; compliance cues |
| Rule Development Rep | rules/interpretations | Interpretation Portal + Knowledge Library | same components; controlled publication cues |
| Technical Manager/Principal/Chief/Lead | technical governance | Technical Reviews + Authorization | same components; review/approval cues |
| CRB Member | review board | Authorization/CRB | same components; decision cues |
| Job Coordinator | allocation | Operations | same components; eligibility/workload cues |
| Management | oversight | Dashboard + Authorization + Operations | same components; approval/oversight cues |
| Trainee | own development | Training/CPD/Competency | same components; learner progress cues |

## Shared design rules

- Persistent 290px sidebar; no horizontal slide/collapse.
- Visible Sign out.
- Single role-aware page header with PSB branding and page context.
- Consistent buttons, inputs, selects, forms, cards, metrics, tables, tabs and alerts.
- Shared empty state: “No records found for the current filters.”
- Shared loading state: page-level spinner with current page name.
- Shared friendly error state with a reference ID; details remain in server logs.
- Shared status semantics: success / warning / danger / info / neutral.
- Navigation changes by role; visual language does not.


## Final Role Alignment Pass
All configured roles now have explicit navigation profiles; no generic role fallback is used. Action authorization is centralized through the core RBAC service.
