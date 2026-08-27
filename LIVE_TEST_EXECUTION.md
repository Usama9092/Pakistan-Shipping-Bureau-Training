# Live Execution Gate

Run only against a staging deployment first. Required gates:
1. Supabase Auth + JWT/RLS regression.
2. Render multi-instance session persistence.
3. Browser smoke for login, forced password change, sign-out, fixed navigation, forms, QR.
4. Locust load test at 100/500/1000 virtual users with no error-rate or latency regression.
5. Restore test from backup.
6. Scheduler failure/retry test.
The project cannot honestly mark these as passed without your live deployment credentials and infrastructure.
