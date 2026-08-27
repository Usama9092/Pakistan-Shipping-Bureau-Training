from __future__ import annotations

# Canonical task-oriented navigation. Related qualification work is merged into professional workspaces.
ROLE_NAVIGATION = {
    "GM": [("Capability", ["GM Capability", "CRB Cases", "Authorization Decisions", "Certificates"], "gm"), ("Account", ["GM Notifications"], "gm")],
    "Admin": [("Administration", ["Users & Roles", "Departments", "Permissions", "System Settings", "Audit Trail", "Backup & Recovery"], "admin")],
    "Trainer": [("Qualification", ["Qualification Workspace"], "training")],
    "Department Manager": [("Department", ["Department Qualification", "My Assessments", "Authorization Cases"], "training"), ("Reference", ["Knowledge Library"], "training")],
    "Surveyor": [("My Qualification", ["My Qualification", "My Assessments", "My Certificates"], "mywork"), ("Reference", ["Knowledge Library"], "training")],
    "NSC Surveyor": [("My Qualification", ["My Qualification", "My Assessments", "My Certificates"], "mywork"), ("Reference", ["Knowledge Library"], "training")],
    "In-Service Surveyor": [("My Qualification", ["My Qualification", "My Assessments", "My Certificates"], "mywork"), ("Reference", ["Knowledge Library"], "training")],
    "Industrial Surveyor": [("My Qualification", ["My Qualification", "My Assessments", "My Certificates"], "mywork"), ("Reference", ["Knowledge Library"], "training")],
    "Plan Appraiser": [("My Qualification", ["My Qualification", "My Assessments", "My Certificates"], "mywork"), ("Reference", ["Knowledge Library", "Interpretation Portal"], "quality")],
    "Trainee": [("My Qualification", ["My Qualification", "My Development", "My Certificates"], "mywork"), ("Reference", ["Knowledge Library"], "training")],
    "On Probation": [("My Qualification", ["My Qualification", "My Development", "My Certificates"], "mywork"), ("Reference", ["Knowledge Library"], "training")],
    "Management": [("Executive", ["Executive Dashboard", "People & Capability", "CRB Cases", "Authorization Decisions", "Certificates"], "executive")],
    "QMS Auditor": [("Quality", ["My Audits", "Audit Workspace", "Accreditation Readiness", "Knowledge Library"], "quality")],
    "QMR": [("Quality", ["Management Review Dashboard", "Accreditation Readiness", "Knowledge Library"], "quality")],
    "Rule Development Rep": [("Rules", ["Rule Development", "Interpretation Portal", "Knowledge Library"], "quality")],
}
