# PSB Qualification Flow Closure

This release closes the current qualification workflow through authorization and certificate.

## Canonical flow
Admin/Trainer assignment → predefined path/version → level/module → theory resources and attendance → server-timed MCQ → guided practical/witness training → explicit Trainer readiness → authorized independent-practical assessment → competency/module completion → automatic level progression → Department Manager authorization recommendation → case-based CRB → final Management/GM authorization decision → certificate.

## Important governance
- Trainer and Tutor are one Trainer role.
- QMS Auditor and Lead Auditor are one QMS Auditor account role; lead is an audit assignment.
- CRB Member is not an account role. CRB membership is case-based.
- Management is mandatory in the current CRB policy. Other permitted roles can be added when PSB finalizes board composition.
- Trainer recommends probation progression; Management/GM/Admin approval performs On Probation → Trainee and department placement without resetting qualification history.

## Validation
- 98/98 automated tests passed.
- Production gate passed.
- 102/102 schema tables have RLS enabled.
- 102/102 schema tables revoke direct anon/authenticated access.
- Migrations continuous 001–041.
- Python compileall passed.

Live Supabase JWT/RLS behavior, Render multi-instance continuity, browser regression, realistic load, and real backup/restore remain deployment/staging execution gates.
