# Administration Module Update

This update restructures the Administration area into six distinct, non-duplicating pages:

1. **Users & Roles** — identity, employee/account lifecycle, primary/additional departments, independent Assigner/Tutor/Trainer assignments, availability, and user history.
2. **Departments** — department master data, department head, status and department membership.
3. **Permissions** — role-based access control using Module + Action + Scope, with audited user-level overrides.
4. **System Settings** — general, security, workflow, notification and scheduler configuration.
5. **Audit Trail** — immutable business-level audit events with actor, entity, reason and before/after fields.
6. **Backup & Recovery** — database exports, backup history and controlled recovery requests; no destructive one-click production restore.

## Business rules implemented

- A user has one **Primary Department** and may have multiple **Additional Departments**.
- Assigner, Tutor/Mentor and Trainer are independent assignments and may be the same person or different people.
- Assignment history is recorded with effective dates.
- Competency level is not manually changed from Administration; the Competency workflow remains authoritative.
- Departments do not automatically grant authority. Access is determined by Role + Permission + Scope.
- Admin manages system governance and does not automatically become Technical Authority, CRB, QMS approver, Trainer or Management approver.
- Temporary passwords are hashed and are not stored in plaintext; the generated temporary password is displayed once after creation.
- Audit records are read-only from the UI.
- Recovery is request/approval based rather than an accidental destructive restore button.

## Database additions

The runtime migration and PostgreSQL schema now include:

- `departments`
- `roles`
- `permissions`
- `role_permissions`
- `user_permission_overrides`
- `system_settings`
- `backup_records`
- `recovery_requests`
- `user_assignments`

Existing installations receive additive migrations for new user and audit fields.
