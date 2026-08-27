# Live Environment Test Plan

## Supabase JWT/RLS
1. Configure SUPABASE_URL and SUPABASE_ANON_KEY in the target environment.
2. Create two users with different roles.
3. Verify authentication maps `auth.users.id` to `users.auth_user_id`.
4. Run `database/supabase_rls_regression.sql`.
5. Confirm each role can read/write only the intended records.

## Render multi-instance
1. Run at least two web instances.
2. Login on instance A.
3. Navigate/reload through instance B using the same browser session.
4. Confirm `auth_sessions` keeps the session valid.
5. Revoke the session and confirm access fails on both instances.

## Browser regression
Exercise each role's menu, forms, confirmation dialogs, empty/loading/error states, sign-out, and QR verification.

## Load test
Exercise dashboards and high-volume tables with 1k, 10k and 100k-row synthetic datasets; capture p50/p95/p99 page times.
