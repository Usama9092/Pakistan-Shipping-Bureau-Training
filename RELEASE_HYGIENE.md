# Release Hygiene — Gap 1 Closure

The current release has a single active audit baseline. Historical/superseded validation snapshots are stored under `archive/audits/` and are excluded from the active release decision.

## Authoritative current baseline

- Roles: **18**
- Role routes: **277**
- Schema tables: **69**
- RLS-enabled tables: **69/69**
- Migrations: **001–029**
- Automated tests: **70/70 PASS**
- Role gap loop: **17/17 PASS**
- Production/static gate: **PASS**

## Active release documents

- `RELEASE_MANIFEST.json`
- `ROLE_EXPERIENCE_FINAL_RELEASE_AUDIT.json`
- `FINAL_RELEASE_EXECUTION_GATE.md`
- `RELEASE_HYGIENE.md`

Historical reports are retained only in `archive/audits/`.
