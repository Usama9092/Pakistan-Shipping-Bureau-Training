# Startup Import Hotfix 044

This code-only hotfix resolves the Windows startup failure:

`ImportError: cannot import name 'actor_get' from partially initialized module 'psb_app.legacy_runtime'`

## Root cause

`legacy_runtime.py` eagerly imported extracted service modules while those same
services imported foundational helpers from `legacy_runtime.py`. This formed an
import cycle during application startup.

A second hidden startup issue was also found: `practical_witness.py` imported the
bounded `table()` renderer through `psb_app.common`, but the renderer lived only
inside `pages/auth_ui.py`.

## Fix

- Extracted service functions are now lazy compatibility exports from
  `legacy_runtime.py`.
- Page modules no longer provide shared runtime symbols back to `main.py`.
- The bounded dataframe renderer is now shared by `psb_app.common`.
- Added regression contracts that reject eager service imports and shared-symbol
  imports from page modules.
- Added `scripts/import_smoke_test.py` for a real post-install import check.

## Validation

- 122/122 automated tests pass.
- Production gate passes.
- Import graph passes with dependency stubs in the build environment.
- On a workstation with `requirements.txt` installed, run:
  `python scripts/import_smoke_test.py`
