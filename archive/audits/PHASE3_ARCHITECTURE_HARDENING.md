# Phase 3 — Architecture Hardening

Phase 3 is the multi-instance / security / modularity hardening layer on top of Phase 2.

## Authentication
- Optional Supabase Auth adapter is available with `AUTH_MODE=supabase`.
- Interactive sign-in uses `SUPABASE_ANON_KEY`; the service-role key remains server-side only.
- `users.auth_user_id` maps the external identity to the PSB profile.
- Local authentication remains available using Argon2id for controlled deployments.
- Forced password changes remain enforced after hash migration.

## Session architecture
- Authentication sessions are stored in the database as SHA-256 hashes of random opaque tokens.
- Sessions have idle timeout, absolute expiry and revocation timestamps.
- This removes the previous single-process in-memory session dependency and makes the application safer for multi-instance deployments.
- Raw session tokens are not persisted.

## Data access
- Added `core/repository.py` as a database access boundary.
- SQL identifiers are strictly validated; values remain parameterized through SQLAlchemy.
- Insert/update/delete operations route through the repository boundary.

## Security/RLS
- Added external identity mapping through `auth_user_id`.
- Added explicit self-profile policy example.
- Session table is server-only under the RLS template.
- Service-role operations remain backend-only.

## Modularity
- Added `core/module_registry.py` for authoritative module ownership metadata.
- Added dedicated core services for authorization, authentication, repository access, health and security policy.
- The large `app.py` remains backward-compatible in this phase; page extraction is intentionally deferred until integration tests cover the business modules.

## Validation
- Phase 3 tests cover Supabase Auth integration, session persistence, force-password-change preservation, identifier validation and schema identity mapping.
