# PSB Architecture Hardening — Phase 1

## Completed
- Argon2id password hashing with one-time legacy SHA-256 migration.
- Forced-password-change enforcement after administrator reset/invite.
- Server-side session expiry with idle timeout and absolute lifetime.
- Centralized `can_action(actor, module, action, scope)` authorization helper.
- Runtime-created `training_requirements` and `competency_reviews` are now first-class PostgreSQL schema objects.
- Modern user/account fields are present in the canonical schema.
- Application exports never include passwords, hashes, reset tokens, API keys or secrets.
- RLS is enabled for administration and governance tables; server-side service-role access remains isolated to the application.
- Legacy duplicate `files_page()` and `management_page()` implementations were removed after navigation consolidation.

## Production prerequisites
1. Keep `SUPABASE_SERVICE_ROLE_KEY` only in server-side environment variables.
2. Prefer Supabase Auth for internet-facing deployments; if local authentication is retained, require Argon2id and MFA at the hosting/identity layer where available.
3. Before enabling any direct browser-to-Supabase access, add explicit JWT-based RLS policies for each table.
4. Run the canonical `database/postgres_schema.sql` against a staging database and test migrations.
5. Validate all business approval actions with the centralized authorization helper plus database/RLS controls.
