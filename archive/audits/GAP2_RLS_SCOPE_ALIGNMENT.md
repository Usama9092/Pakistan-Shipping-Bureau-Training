# Gap 2 — RLS / Application Scope Alignment

## Status

**CLOSED at source/static architecture level.**

The production deployment uses a server-mediated Supabase model. Direct browser access to application tables is denied. Business scope is enforced by the PSB application authorization layer.

### Authoritative layers

1. **Database boundary:** RLS enabled on every schema table.
2. **Client boundary:** `anon` and `authenticated` have no table privileges.
3. **Application boundary:** `role → module → action → scope → record` is enforced by the PSB authorization/scope services.
4. **Repository boundary:** application data access is server-side.

The previous ambiguous configuration where `authenticated` SELECT policies coexisted with a later server-only contract has been removed.

## Verified

- 69/69 schema tables RLS enabled.
- 69/69 tables revoke direct client privileges.
- 0 production authenticated SELECT policies remain.
- CRB remains case-assignment scoped in application policy.
- Trainer/Tutor remain assignment scoped.
- Own-role views remain own scoped.

## Staging requirement

This closes the code/configuration gap. It does **not** claim a live Supabase JWT test was executed. Run the provided staging behavioral test against the real Supabase project before production promotion.
