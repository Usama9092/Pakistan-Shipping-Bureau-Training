# Gaps 14–17 Final Closure

## 14 — Audit-event integration
Critical mutation modules now have executable source/integration regression checks covering the audit event contract. The local suite verifies required audit actions and source hooks. End-to-end database persistence is covered by the staging execution harness.

## 15 — Supabase JWT/RLS
`tests/live_supabase_security.py` is an executable staging gate. In the current server-mediated architecture it verifies that authenticated browser clients cannot directly read protected tables. It requires a real staging Supabase project and low-privilege test credentials.

## 16 — Render multi-instance
`tests/render_multinstance_smoke.py` verifies the database-backed session remains usable across two deployed instance URLs. It requires real staging endpoints/session material.

## 17 — Browser/load/backup restore
The release contains:
- `tests/browser_role_regression.py` for role login/navigation regression with Playwright;
- `locustfile.py` for realistic load testing;
- `tests/backup_restore_rehearsal.py` for safe local backup/restore round-trip validation;
- staging release-gate wiring and documentation.

### Final truth
Local/static closure is PASS. Real staging execution for Supabase JWT/RLS, Render multi-instance, browser, load and production-backup restore is environment-dependent and is intentionally not represented as passed until run against the actual staging environment.
