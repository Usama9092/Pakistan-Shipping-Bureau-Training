# Development Plans Update

## Purpose
Development Plans is now the authoritative page for planning and monitoring professional development actions.

## Improvements
- Separated development planning from the Field Exposure Matrix. Exposure/witness evidence remains in the later Competency / Practical workflow.
- Added plan title, objective, development type, priority, owner, progress, evidence status, review date, success criteria, source-gap reference and completion date.
- Added register filters and summary metrics.
- Added create and controlled update workflows.
- Uses assigned Tutor/Mentor as the default development owner where available.
- Same/different Assigner, Tutor and Trainer relationships remain supported; changing a plan owner does not change the master Tutor assignment.
- No duplicate training, competency, witness or authorization records are created from this page.
- Updates are audited with before/after values and reason.
- Existing databases are upgraded additively through init_db migrations.
