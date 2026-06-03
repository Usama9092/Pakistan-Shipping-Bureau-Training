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
admin / Admin@1234
trainer / Trainer@1234
tutor / Tutor@1234
technical / Tech@1234
principal / Principal@1234
qmr / QMR@1234
coordinator / Coord@1234
surveyor / Surveyor@1234
appraiser / Appraiser@1234
management / Mgmt@1234
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
