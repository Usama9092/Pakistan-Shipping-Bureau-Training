# Phase 4 — Production & UX Hardening

Phase 4 combines a shared role-wise design system with production hardening.

## UX consistency
- Shared design tokens and component styling in `core/design_system.py` and `apply_style()`.
- Role-aware page context in the global header.
- Persistent static sidebar and visible Sign out.
- Shared visual treatment for tables, forms, metrics, buttons, tabs, alerts, expanders and empty states.
- Global page loading state and friendly page-level error boundary with reference IDs.
- Same design language for all roles; permissions/navigation are role-specific.

## Production hardening
- Streamlit XSRF protection enabled.
- Production-bounded dependency file `requirements-prod.txt`.
- Render configuration exposes the required Supabase Auth/Session environment variables.
- RLS posture covers all canonical schema tables, including the server-only `auth_sessions` table.
- Static architecture checks and legacy duplicate checks included.
- Phase 1-3 authentication, RBAC, schema contract, repository and session hardening preserved.

## Environment-dependent verification
- Run live Supabase JWT/RLS regression tests against the target project.
- Run real Render multi-instance/browser/load tests before production launch.
