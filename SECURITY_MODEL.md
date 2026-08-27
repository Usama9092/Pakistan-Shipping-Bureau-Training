# PSB Security Model — Gap 2 Baseline

## Production database access model

The application uses a **server-mediated Supabase architecture**. Browser clients do not receive direct table privileges. The production RLS contract therefore has one authoritative rule:

1. Every schema table has RLS enabled.
2. `anon` and `authenticated` receive no direct table privileges.
3. `anon`/`authenticated` policies fail closed with `USING (false)` / `WITH CHECK (false)` where required.
4. The PSB server accesses the database through the controlled repository/service boundary.
5. Application RBAC and record scope (`role → module → action → scope → record`) is the authoritative business authorization layer.
6. Direct browser table access is intentionally not a second competing authorization model.

This removes the previous ambiguity where authenticated SELECT policies coexisted with later server-only policies.

## Scope alignment

Application scope remains explicit:

- Own
- Assigned
- Department
- Multiple Departments
- Organization-wide
- Case-assigned

The RLS layer protects the database boundary; the application policy enforces business scope.

## Staging validation required before production

The release includes behavioral tests for a Supabase environment. These must be executed against the real staging project before production promotion.
