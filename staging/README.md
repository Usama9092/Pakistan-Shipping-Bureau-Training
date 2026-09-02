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

The live gate verifies reachability. Copy `role_test_matrix.template.json` into the encrypted CI secret `PSB_ROLE_MATRIX_JSON` and configure the referenced 15 staging-only account secrets. Never use production users in this matrix.

Run the GitHub Actions **PSB staging assurance** workflow for authenticated role regression and the five-minute 50-user load plan. The restore job is opt-in, requires the protected `staging-restore` environment, refuses an identical source/target, and requires an exact target database allowlist.

The **PSB uptime monitor** workflow probes HTTP health, host configuration, the login shell and the Streamlit WebSocket every 30 minutes. Enable GitHub Actions failure notifications for the repository. Set repository variable `PSB_MONITOR_URL`; no credential is required.

Production passwords must not be stored in GitHub. Rotate application passwords through the portal and Render/Supabase service secrets in their respective dashboards. A user must personally complete each password-change submission.

Required role scenarios include Own, Assigned, Department, Organization-wide, CRB Case, and denied cross-scope access.

