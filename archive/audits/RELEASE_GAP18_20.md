# PSB Master — Gaps 18–20

This release closes the next three audited gaps on top of Gap 17:

18. Certificate history / lineage and user-facing certificate history.
19. Explicit technical-discipline scope for technical reviews and assignments.
20. Single-source role classification for access-policy role groups.

Source/local validation: PASS.
Root tests: 87/87.
Embedded tests: 87/87.
Migrations: 001–034.
RLS posture: every schema table has enable/revoke coverage in the authoritative production RLS script.

Live Supabase/Render/browser/load/backup execution remains staging-dependent.
