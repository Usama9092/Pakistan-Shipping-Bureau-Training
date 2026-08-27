# Pakistan Shipping Bureau — World-Class HRDM / Classification Competency Platform

This is a Streamlit + Supabase/PostgreSQL + Render-ready system for PSB.

## What is included

- Role-based dashboards
- Admin control center
- Theoretical training matrix
- Trainer course creation
- File uploads for PDF/PPT/DOC/TXT/video/evidence
- MCQ generation from uploaded/extracted content
- Development plans for trainees/probationers
- Assigned mentor/tutor workflow
- Field exposure matrix
- Witness survey assessment
- Supervised survey assessment
- Plan appraisal joint/independent review workflow
- Scope-specific authorization matrix
- Competency levels
- Technical authority structure
- Competency Review Board (CRB)
- Digital approval/signature flow
- QR authorization certificate
- Risk-based job assignment engine
- KPI and utilization tracking
- CPD/seminar/refresher records
- Technical knowledge library
- QMS/CAPA/audit trail
- Revalidation / reauthorization workflow
- Backup/export system
- Supabase file storage support
- SQLite fallback for local testing
- Render deployment files

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

## PostgreSQL / Supabase migration files

- `database/postgres_schema.sql` contains the complete PostgreSQL schema, indexes, and references for all app tables.
- `database/supabase_rls_template.sql` enables row level security on all supported tables after the schema is created.
- `database/supabase_rls_and_storage.sql` provides a Supabase-ready RLS template and storage guidance.

## Environment variables for Render

```text
DATABASE_URL=postgresql://postgres:PASSWORD@HOST:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET=psb-hrdm-files
PUBLIC_URL=https://training.psbureau.org
```

## Default demo logins

```text
Set INITIAL_ADMIN_LOGIN and INITIAL_ADMIN_PASSWORD in the deployment environment for the first administrator.
Demo credentials are disabled by default. For controlled development testing only, set ENABLE_DEMO_SEED=true and DEMO_PASSWORD in the environment.
```

## International classification society workflow

The workflow follows:

```text
Admin assigns role/path/mentor
→ Trainer assigns theoretical training
→ Candidate passes training and assessment
→ Tutor records witness surveys
→ Tutor records supervised survey or plan review
→ Readiness engine checks evidence
→ Authorization request
→ Principal/Technical/QMR/CRB/Management approval
→ QR certificate
→ Risk-based job allocation
→ Annual review, CPD, refresher and reauthorization
```


## PLUS 12 Advanced Modules

1. Technical Authority Framework
2. Survey Report Review System
3. Plan Review Quality Monitoring
4. Competency NCR / Surveyor Performance NCR
5. AI Competency Gap Advisor
6. Annual Competency Review Board
7. Authorization Restriction Matrix
8. Client / Shipowner / Shipyard Feedback
9. Succession Planning / Talent Pipeline
10. Workforce Planning / Resource Forecasting
11. Accreditation Readiness Dashboard
12. Rule Interpretation / Technical Decision Portal

## IMPORTANT: Prevent Data Loss on Render

This version prevents accidental data loss by blocking temporary SQLite/local storage on Render.

Set these Render Environment Variables:

```text
DATABASE_URL=postgresql://postgres:PASSWORD@HOST:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET=psb-hrdm-files
PUBLIC_URL=https://training.psbureau.org
APP_ENV=production
```

Local SQLite is allowed only for local testing. On Render, the app will stop and show a configuration warning if `DATABASE_URL` is not PostgreSQL/Supabase.

Uploaded files also require Supabase Storage on Render, so training files, evidence, certificates and records do not disappear after restart/redeploy.


## Role Alignment / Live Verification
- Explicit navigation profiles are defined for every configured role.
- Page action authorization uses the central RBAC service for upgraded workflows.
- Public certificate verification is available through `?verify=<certificate_id>`.
- Supabase JWT/RLS, Render multi-instance and browser/load tests must be executed in the real deployment environment.


## Final security contract
All schema tables are RLS-enabled and client table privileges are denied by default. The PSB application is server-side and uses controlled credentials. Live Supabase JWT/RLS, Render multi-instance, browser and load checks remain mandatory release-gate evidence and must be executed in staging before production.

## Release documentation

The root of the release contains only the authoritative current release artifacts. Historical audit snapshots and superseded validation reports are stored under `archive/audits/` and are not part of the active release decision.

Authoritative current files:
- `RELEASE_MANIFEST.json`
- `ROLE_EXPERIENCE_FINAL_RELEASE_AUDIT.json`
- `FINAL_RELEASE_EXECUTION_GATE.md`

Current release baseline: **69 schema tables, 277 role routes, 18 roles, migrations 001–029**.


## Qualification Workspace and AI-assisted MCQ publishing
The Trainer now works from one **Qualification Workspace** containing path versions, levels, modules, theoretical training, practical/witness requirements, probation progression, the path matrix, and the controlled Knowledge Library. Uploaded PDF/DOCX/PPTX/XLSX materials and rule/reference text can be used to create MCQ drafts. Draft questions are not visible to learners until the Trainer reviews them and explicitly selects **Publish MCQs to Assigned Learners**.

For an external state-of-the-art model, configure `PSB_AI_MCQ_ENDPOINT`, `PSB_AI_MCQ_API_KEY`, and `PSB_AI_MCQ_MODEL` with an OpenAI-compatible chat-completions provider. If no provider is configured, PSB uses its deterministic controlled-source fallback; the Trainer review/publish gate remains mandatory in either mode.

Final authorization is only presented after a CRB-recommended case. Approval issues a **Digital Certificate of Authorization** valid for 12 months from the final approval date, with QR/public verification and visibility on the holder's qualification/certificate pages.
