# PSB Staging Release Gate

This release contains deterministic local checks and a live staging gate.

## Offline preflight

Run:

```bash
python scripts/staging_release_gate.py
pytest -q
python tests/architecture_gap_guard.py
python scripts/production_gate.py
```

## Live staging

Set:

- `STAGING_APP_URL`
- `STAGING_VERIFY_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Then run:

```bash
python scripts/staging_release_gate.py --live
```

The live gate verifies reachability. The actual role/RLS behavioral matrix must be executed against the staging Supabase project using `database/rls_behavioral_tests.sql` with dedicated test identities.

Required role scenarios include Own, Assigned, Department, Organization-wide, CRB Case, and denied cross-scope access.
