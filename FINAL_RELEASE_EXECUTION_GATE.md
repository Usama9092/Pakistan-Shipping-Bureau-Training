# Final Release Execution Gate

## Local gate
- `pytest` must pass without PYTHONPATH overrides.
- Role/view audit must pass for all 18 roles.
- Migration/schema/RLS static gates must pass.

## Staging-only gates
These cannot be honestly executed in this build environment and must be run against the real infrastructure:
1. Supabase JWT + RLS behavioral test.
2. Render multi-instance session continuity test.
3. Browser regression across the 18-role matrix.
4. Realistic load test.
5. Backup/restore test against staging Supabase and storage.

A release is production-approved only when all five staging gates are recorded as PASS.
