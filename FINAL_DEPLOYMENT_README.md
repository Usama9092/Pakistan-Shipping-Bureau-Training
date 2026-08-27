# Pakistan Shipping Bureau HRD&M Portal — Deployment

This release is configured for Render and a Supabase PostgreSQL database.

## Render deployment

1. Create a new Render Blueprint from this repository/package and use `render.yaml`.
2. Configure every environment variable marked `sync: false` in `render.yaml`.
3. Set `DATABASE_URL` to the Supabase PostgreSQL pooler connection string. Use the SQLAlchemy-compatible `postgresql+psycopg2://` scheme when required by the hosting environment.
4. Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, and `SUPABASE_STORAGE_BUCKET` from the Supabase project.
5. Set `PUBLIC_URL` and `VERIFY_PUBLIC_URL` to the final HTTPS Render URL.
6. Set strong, unique `INITIAL_ADMIN_LOGIN` and `INITIAL_ADMIN_PASSWORD` values before the first startup.

The application runs pending database migrations automatically during startup. Demo seeding is disabled in production.

## Required production checks

After deployment, validate login, role navigation, file upload/download, email delivery, Supabase storage, database persistence across a Render restart, and backup/restore. Do not place credentials in this ZIP or commit them to source control.
