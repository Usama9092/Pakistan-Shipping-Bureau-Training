# Backup & Recovery Update

## Scope
The Administration Backup & Recovery page is now a controlled **application-data export and recovery-request interface**.

## Key design decisions
- Exports are explicitly labeled as application-level exports, not managed PostgreSQL/Supabase snapshots.
- Credential and secret fields are excluded from JSON/Excel exports.
- Backup creation creates an auditable `backup_records` event automatically.
- Backup history is filterable by status, format and creator.
- Recovery is request-only; there is no destructive one-click production restore.
- Recovery requests require a restore point, business reason and confirmation.
- Audit events capture backup and recovery actions.
- The page shows database persistence, storage persistence and last recorded application export.
- A restore test is explicitly identified as a governance requirement rather than being falsely represented as complete.

## Production note
Managed database backup, point-in-time recovery and object-storage disaster recovery remain hosting/Supabase responsibilities and should be configured and tested outside the Streamlit UI.
