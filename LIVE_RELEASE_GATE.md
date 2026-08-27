# PSB Live Release Gate

The codebase is hardened for deployment, but these checks must pass against the real staging infrastructure before production promotion:

1. Supabase JWT + RLS behavioral test: verify self/assigned/department/CRB/organization boundaries with real Auth users.
2. Render multi-instance session test: login on instance A, refresh on instance B, verify same database-backed session.
3. Public verification test: rate limit, event logging, valid/invalid certificate responses, no confidential fields.
4. Scheduler failure injection: confirm retry/backoff and administrator notification.
5. Backup/restore test: execute a real restore on staging and validate schema + sample records + storage.
6. Browser regression: every role, every page, sidebar, sign-out, forms, loading/error states.
7. Load test: 100/500/1000 concurrent sessions and representative database volumes.

No production release should be marked green until all seven checks are recorded with timestamp, environment, evidence and reviewer.
