# Gap 3 — Legacy Runtime Decomposition

## Goal
Reduce the remaining concentration in `psb_app/legacy_runtime.py` without changing business behavior.

## Changes
The following responsibilities were extracted into explicit service modules:

- `psb_app/services/auth_service.py`
- `psb_app/services/policy_service.py`
- `psb_app/services/training_service.py`
- `psb_app/services/certificate_service.py`
- `psb_app/services/governance_service.py`
- `psb_app/services/admin_service.py`
- `psb_app/services/ui_helpers.py`

`psb_app/common.py` remains the compatibility facade for existing page imports. `legacy_runtime.py` now retains the shared runtime/database/migration compatibility layer and imports the extracted services at the boundary.

## Result
`legacy_runtime.py` reduced from approximately 1,098 lines to 751 lines.

## Validation
- Full test suite: 72/72 PASS
- Main application compile: PASS
- Embedded application compile: PASS
- Production/static gate: PASS
- RLS policy check: PASS
- Migration check: PASS
- Architecture gap guard: PASS

## Remaining compatibility boundary
The service modules intentionally consume `legacy_runtime` context for backward compatibility. This allows staged extraction without changing the business workflow or database contract in one release. Future refactors can continue moving database/config primitives into dedicated core services.
