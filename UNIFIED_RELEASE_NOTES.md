# Pakistan Shipping Bureau — Unified Master Release

This release converges the GM Executive and Professional Practical/Witness sibling builds into one canonical application tree.

## Canonical integration
- One active application tree; redundant `psb_extracted/` application copy removed.
- GM Executive workspace retained with dedicated executive navigation and organization-wide governance scope.
- Practical/Witness retained as one reusable engine for Surveyor and Plan Appraiser pathways rather than separate duplicate systems.
- Practical evidence links existing source documents rather than duplicating uploads.
- Verified practical evidence feeds competency readiness and authorization workflow.
- Sign out remains at the end of the fixed sidebar navigation.

## Database and upgrade convergence
The two input branches both used migration version 035 for different features. The unified release keeps Practical/Witness as canonical 035 and adds migration 036 as an idempotent convergence bridge containing both feature schemas. The migration runner recognizes only the two known legacy 035 checksums so an installation originating from either sibling branch can converge without accepting arbitrary checksum drift.

## Security and validation
- Central RBAC/record authorization boundary retained.
- 77 canonical schema tables have RLS enabled and direct anon/authenticated table privileges revoked in the production policy.
- Practical/Witness witness eligibility, assigned/own scope, declarations, evidence linking, and controlled outcomes are covered by automated tests.
- GM does not receive implicit technical Review/Approve authority merely from executive status.
- Automated suite: 109 tests passed.
- Static master, gap, role-page, Phase 4 UX/security, and RLS policy checks pass.

## Deployment-stage gates
The following require a real staged environment and are intentionally not self-certified by source inspection: Supabase JWT/RLS behavioral execution, Render multi-instance continuity, browser role regression, realistic load testing, and real backup/restore execution.

## Qualification Curriculum / Role Model Update — Migration 038
- Added versioned qualification curricula: Path -> Level -> Module -> Requirement.
- Four controlled technical paths remain independent: NSC Surveyor, In-Service Surveyor, Industrial Surveyor, Plan Appraiser.
- Trainer can add levels/modules and assign eligible people to a path/version/starting level; Trainer is optional.
- Higher-level starting assignments require justification/evidence reference.
- Added controlled On Probation -> Trainee progression with technical department placement while preserving the same qualification assignment.
- Removed account roles Lead Auditor, CRB Member, and Job Coordinator.
- QMS Auditor is the single audit account role; lead/member responsibility is assigned per audit.
- CRB remains as a case-based board through crb_case_board_assignments; Management can participate when assigned, with additional eligible board roles to be configured when governance composition is finalized.
- Added RLS/client-revoke coverage for all curriculum/CRB tables.

## Qualification Curriculum Delivery — Migration 040
- Qualification modules now support multiple theoretical trainings.
- Each theoretical training supports multiple uploaded materials (PDF/DOCX/XLSX/PPTX and other allowed controlled files), multiple video/rule/reference links, and multiple live/Zoom/classroom sessions.
- Trainer can generate MCQ assessments from source material inside Qualification Paths and configure pass mark, maximum attempts, randomization flags, and a server-controlled timer.
- Learner assessment attempts use server-side start/expiry records and auto-fail on expiry.
- Each module has a configurable guided Practical/Witness Training minimum (default 2), learner report, Trainer review/declaration, and Trainer satisfaction gate.
- Independent Practical remains locked until mandatory theory is passed, the guided-practical minimum is met, and Trainer satisfaction is recorded.
- Multiple theoretical trainings, guided practical activities and independent practical requirements are supported per module/path.

## State-of-the-art PSB brand/UI upgrade
- Applied supplied PSB crest and crest-derived navy/green palette.
- Replaced sidebar section selectboxes with direct task navigation and explicit active-page state.
- Added accessible focus/reduced-motion contracts, responsive mobile drawer behavior, sticky sign-out and refined enterprise surfaces.
- Updated login/product language to Qualification & Digital Authorization Portal.
- Added branded Streamlit theme and refreshed digital certificate presentation.
- Expanded automated suite to 119 passing tests.
