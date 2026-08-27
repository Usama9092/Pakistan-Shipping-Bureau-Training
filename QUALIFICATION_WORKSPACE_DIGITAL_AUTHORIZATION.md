# PSB Qualification Workspace & Digital Authorization — Current Master

## Trainer
Trainer now has one top-level **Qualification Workspace**. It contains assigned learners, path library/version/levels/modules, theoretical training, controlled training materials, video/rules/references, live/Zoom sessions and attendance, Trainer-reviewed MCQ draft generation/publishing, path-specific Practical/Witness requirements, final Trainer readiness, independent practical assignment, probation progression, path matrix and the Knowledge Library.

Generated questions are draft-only until the Trainer reviews and explicitly publishes them. When an OpenAI-compatible AI provider is configured with `PSB_AI_MCQ_ENDPOINT`, `PSB_AI_MCQ_API_KEY` and `PSB_AI_MCQ_MODEL`, PSB can use that provider to create source-grounded MCQ drafts. Without it, PSB uses a deterministic controlled-source generator.

## Path-specific practical work
Modules may define multiple required Survey, Industrial Survey or Plan Appraisal activities with modes **Witness / Observe**, **Work Together / Joint**, **Guided Practical**, or **Independent Practical**, with configurable required counts. These specific requirements participate in module completion.

## Authorization
Department Manager recommendation creates the authorization case and constitutes CRB according to `config/crb_policy.json`. Final Authorization Decisions show only cases with status **CRB Recommended**. The decision workspace displays qualification evidence, Department recommendation, CRB discussion/decision, and final action. Approval immediately issues a **Digital Certificate of Authorization** valid for exactly 12 months from the final approval date. The certificate includes QR/public verification, is attached to the holder's My Qualification / My Certificates views, and is auditable.

## Admin
Admin creates identity, employee details, role, department, Trainer responsibility, login ID and temporary password. Role determines access. Qualification Path remains Trainer-controlled. Authorized technical status is never an Admin toggle; it is derived from an approved authorization case plus a valid Digital Certificate of Authorization.
