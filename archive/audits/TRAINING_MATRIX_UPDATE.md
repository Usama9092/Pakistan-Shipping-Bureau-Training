# Training Matrix Update

## Purpose
The Training Matrix is now the authoritative requirement engine for training applicability.

It defines what a person should complete based on department, role, trainee path, mandatory status, priority, sequence and applicability period.

## Single-source-of-truth rules
- `training_modules` is the catalogue of theoretical modules.
- `training_requirements` is the applicability/rules layer.
- `training_records` is the authoritative learner assignment/completion layer.
- The matrix does not store learner completion or assessment results.
- Matrix-generated assignments are idempotent: an existing learner/module record is never duplicated.

## Requirement rule fields
- department
- role
- trainee_path
- requirement_type
- mandatory
- priority
- prerequisite_module_ids
- sequence_no
- validity_months
- effective_from / effective_to
- active
- notes

## UI
- Matrix Overview
- Requirement Rules (Admin/Trainer)
- Coverage & Gaps
- Department, role, path, status and search filters
- Summary metrics for active requirements, learners, completion and overdue work

## Governance
Changing a requirement rule is audited. Deactivating a requirement preserves history. Completion and assessment remain managed in Training.
