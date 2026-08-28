# Permissions Module Update

## Purpose
The Permissions module is the central RBAC control center. It separates system administration from operational business approvals.

## Features
- Role Profiles: description/status and role-level summaries.
- Permission Matrix: Module + Action + Scope with explicit role grants.
- Standard actions: View, Create, Edit, Submit, Assign, Review, Approve, Reject, Close, Export, Manage.
- Standard scopes: Own, Assigned, Department, Multiple Departments, Organization-wide.
- User Overrides: exceptional, time-bound permission changes requiring a reason and audit trail.
- Effective Access: shows the final access result for a user from role baseline plus user overrides.

## Governance rules
- Admin manages access but does not automatically receive operational approval authority.
- User-specific overrides are exceptions and should be rare.
- Permission changes and overrides are audited.
- Effective access is the view that should be used by future module-level authorization checks.
