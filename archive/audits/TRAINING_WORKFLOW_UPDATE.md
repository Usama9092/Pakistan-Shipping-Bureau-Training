# Training Workflow Update

## Scope
This update upgrades **Training** as the authoritative course-delivery workflow.

### Business boundaries
- **Training Matrix** defines what training is required.
- **Training** defines course delivery and actual learner records.
- **Development Plans** consume identified development needs; they do not duplicate training records.
- **Competency** consumes passed training/assessment status for readiness decisions.

## Improvements
- Course catalogue with search/filter and operational status.
- Professional course creation workflow.
- Course workspace with Overview, Materials, Assessment, Assignments, and Attendance & Certificates.
- Course metadata: delivery mode, duration, location/platform, capacity, enrollment state, version, prerequisites.
- Training material and file attachment remains linked to the course record; there is no standalone Files workflow.
- Assessment configuration and MCQ generation remain attached to the course.
- Unique learner assignment enforcement (no duplicate user/course records).
- Attendance tracking with audit event.
- Certificate issuance is a separate post-pass governance action.
- Course archive replaces destructive delete and preserves historical learner records.
- Learner/trainee view remains read-only for course configuration.

## Completion rule
Certificate issuance is **not** a prerequisite for training completion. Completion is based on attendance/recording evidence plus the configured assessment requirement.

## Backend compatibility
The update uses additive migrations for existing databases. New training fields include course metadata and learner assignment/certificate audit fields.
