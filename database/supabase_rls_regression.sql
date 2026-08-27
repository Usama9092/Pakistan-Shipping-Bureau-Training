-- Non-destructive regression queries; execute in Supabase SQL editor with JWT context.
-- Replace the JWT-derived identity mechanism with your final production mapping before enabling client-side DB access.
-- Server-side service-role application paths should not rely on these browser policies.

select tablename, rowsecurity from pg_tables where schemaname='public' and rowsecurity=false order by tablename;
select count(*) as policies from pg_policies where schemaname='public';
select id, auth_user_id, email, role from public.users where auth_user_id = auth.uid();
