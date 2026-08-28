# Phase 4 — UX Consistency & Production Hardening

## UX consistency
- Global PSB design tokens for colors, spacing, radius, typography and shadows.
- Consistent role/page kicker in the global header.
- Standardized buttons, inputs, forms, tabs, dataframes, expanders, metrics and alerts.
- Consistent status badges and empty-state presentation.
- Fixed 290px sidebar with no collapse/slide/horizontal overflow and persistent Sign out.
- Role-aware navigation and role description in the header without changing the visual design language.
- Standard page execution wrapper for predictable loading/error handling and request IDs.

## Phase 4 production hardening
- Centralized page execution timing and structured exception logging.
- Production configuration diagnostics.
- Clear separation of system administration from business approvals.
- Preserves the Phase 1-3 authentication, RBAC, schema-contract, repository, RLS and performance hardening.
- Preserves single-source-of-truth workflows.

## Remaining environment-dependent verification
- Live Supabase JWT/RLS integration against the target project.
- Real Render multi-instance load test and browser regression test.
