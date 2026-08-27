# PSB Current Phase Architecture

## Scope
Current qualification phase ends at Authorization and Certificate. Operational job allocation, annual vertical audit, KPI/client feedback, and revalidation are intentionally outside this phase.

## Canonical roles
GM, Management, Admin, Department Manager, Trainer, Trainer, Trainee, On Probation, Surveyor, Industrial Surveyor, Plan Appraiser, QMS Auditor, QMR, Rule Development Rep.

`Lead Auditor` is not an account role. A QMS Auditor may be assigned as lead or team member on a specific audit.

`CRB Member` is not an account role. CRB is a case-based board assignment. Management may be assigned to a CRB case; additional permitted system roles can be added to the board-composition policy when finalized.

`Job Coordinator` is removed from the current phase.

## Qualification curriculum
Each controlled technical path is independent:
- NSC Surveyor
- In-Service Surveyor
- Industrial Surveyor
- Plan Appraiser

Each path supports:
Path -> Version -> Ordered Levels -> Modules -> Module Requirements.

Module requirements can be Training, Reading/Procedure, Assessment, Practical Activity, Witness, Evidence, or Competency. Modules may have prerequisites, passing score, evidence requirements, practical observation counts, and witness requirements.

## Assignment
Trainer assigns eligible people (On Probation, Trainee, or technical staff seeking an authorization) to a path/version/starting level. Trainer is optional. Starting above the first level requires recorded justification and supporting evidence reference.

## Probation progression
On Probation -> qualification foundation/probation modules -> Trainer recommendation -> Trainee -> department placement -> continue the same qualification assignment without resetting completed work.

## Department management
Department Manager is a generic account role scoped to the technical department assigned by Admin: Survey NSC, Survey Inservice, or Plan Appraisal. Department Manager does not automatically become an eligible witness; technical witness eligibility remains authorization/scope based.

## CRB
CRB is represented by `crb_case_board_assignments`. Board membership is per authorization case and records system role, board role, voting authority, conflict declaration, attendance, decision, comments, and timestamps.
