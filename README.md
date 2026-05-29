# PSB HRDM Supabase + Render Complete Streamlit App

This package is ready for:

```text
GitHub → Render → Supabase PostgreSQL + Supabase Storage
```

## Main features

- Supabase/PostgreSQL database through `DATABASE_URL`
- Supabase Storage for PDF, PPT/PPTX, TXT, DOC/DOCX, image, video, Excel and certificate files
- Local fallback storage for testing
- Training file uploads by Trainer/Admin/Tutor
- Certificate storage table
- Rule document version file uploads
- Logbook/evidence file uploads
- Extracted text from TXT/PDF/DOCX/PPTX files
- MCQ generation from extracted content
- Authorization certificate with QR code
- Authorized + available job allocation
- SCORM/LMS records
- Audit backup export
- Render deployment files

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

## Render Environment Variables

Required for Supabase database:

```text
DATABASE_URL=postgresql://postgres:PASSWORD@HOST:5432/postgres
```

Required for Supabase file storage:

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET=psb-hrdm-files
PUBLIC_URL=https://training.psbureau.org
```

## Important security

- Never put `SUPABASE_SERVICE_ROLE_KEY` in GitHub.
- Add it only in Render Environment Variables.
- Use Supabase RLS when you later migrate to Supabase Auth.
- For now, app-side role controls protect pages and actions.

## Default logins

```text
admin / Admin@1234
trainer / Trainer@1234
tutor / Tutor@1234
surveyor / Surveyor@1234
appraiser / Appraiser@1234
qmr / QMR@1234
rule / Rule@1234
coordinator / Coord@1234
management / Mgmt@1234
```
