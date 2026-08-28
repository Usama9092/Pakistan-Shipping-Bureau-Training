# PSB HRDM — Phase 1 Architecture Hardening

## Status
Completed and validated on the current master.

## Security
- Argon2id password hashing (`argon2-cffi`) replaces new SHA-256 password storage.
- Existing legacy SHA-256 password hashes are supported only for one successful login and are then upgraded to Argon2id.
- Temporary/admin-reset passwords are never displayed or persisted as plaintext.
- Forced password change is enforced before portal access.
- Session tokens use 32-byte URL-safe randomness, idle timeout and absolute lifetime.
- Fixed demo credentials removed from source/documentation; production uses one-time `INITIAL_ADMIN_*` environment variables.

## Authorization
- Central `can_action(actor, module, action, scope)` decision function added.
- Administration access now requires both the Admin role and the Administration:Manage permission.
- Role baseline remains separate from business approval authority.

## Data / schema
- `training_requirements` and `competency_reviews` are now first-class canonical PostgreSQL schema objects.
- Modern account lifecycle fields are included in the canonical schema.
- Runtime-created business tables now reconcile with the canonical schema.

## RLS
- RLS is enabled for administration, governance and newly introduced workflow tables.
- The application remains server-side for database access using the Supabase service role; the key must never enter browser code.
- Direct client-side Supabase access requires explicit JWT policies before it is enabled.

## Architecture cleanup
- Legacy standalone Files page implementation removed.
- Legacy Management dashboard implementation removed.
- The consolidated navigation remains the only user-facing route for those business functions.

## Validation
- Python compilation passed for `app.py` and `psb_extracted/app.py`.
- AST parsing passed.
- Canonical schema covers all runtime `CREATE TABLE IF NOT EXISTS` names.
- No fixed demo passwords remain in application/source documentation.
- Final ZIP integrity verified after packaging.

## Remaining production prerequisite
The next security phase should migrate internet-facing authentication to Supabase Auth/MFA or an equivalent managed identity provider, then add tested JWT/RLS policies for any direct browser-to-database access.
