from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any
import pandas as pd

from pathlib import Path
import json


TECH_DISCIPLINE_POLICY_FILE = Path(__file__).resolve().parents[1] / 'config' / 'technical_discipline_policy.json'
try:
    TECH_DISCIPLINE_POLICY = json.loads(TECH_DISCIPLINE_POLICY_FILE.read_text(encoding='utf-8'))
except Exception:
    TECH_DISCIPLINE_POLICY = {'disciplines': [], 'default_allowed': [], 'roles': {}}

def allowed_disciplines(role: str) -> set[str]:
    values = TECH_DISCIPLINE_POLICY.get('roles', {}).get(role)
    if values:
        return set(values)
    return set(TECH_DISCIPLINE_POLICY.get('default_allowed', []))

def discipline_allowed(role: str, discipline: str | None) -> bool:
    d = str(discipline or '').strip()
    if not d or d.casefold() in {'all','all technical'}:
        return True
    allowed = allowed_disciplines(role)
    return d in allowed or 'All Technical' in allowed

from core.role_classes import ORG_ROLES, SELF_ROLES, ASSIGNED_ROLES, CASE_ROLES, DEPARTMENT_ROLES
_POLICY_FILE = Path(__file__).resolve().parents[1] / "config" / "role_scope_policy.json"
POLICY_LOAD_ERROR = False
try:
    ROLE_MODULE_SCOPE_DEFAULTS = json.loads(_POLICY_FILE.read_text(encoding="utf-8"))
except Exception:
    POLICY_LOAD_ERROR = True
    ROLE_MODULE_SCOPE_DEFAULTS = {}
ROLE_ALLOWED_SCOPES = {
    **{r: {"Organization-wide", "Department", "Multiple Departments", "Assigned", "Own"} for r in ORG_ROLES},
    **{r: {"Own", "Assigned"} for r in SELF_ROLES},
    **{r: {"Assigned", "Own"} for r in ASSIGNED_ROLES},
    **{r: {"Assigned", "Department"} for r in CASE_ROLES},
    **{r: {"Department", "Assigned", "Own"} for r in DEPARTMENT_ROLES},
}

USER_ID_COLUMNS = ("user_id", "employee_id", "subject_user_id", "assigned_user_id", "owner_id", "owner_user_id", "crb_member_id", "assigned_crb_member_id", "person_id", "trainee_id")
ASSIGNMENT_COLUMNS = ("tutor_id", "mentor_id", "trainer_id", "assigner_id", "assigned_by", "assigned_user_id", "owner_id")
DEPARTMENT_COLUMNS = ("primary_department", "department", "owner_department", "lead_department")

ORG_SCOPE_PERMISSION_ALLOWLIST = {
    "Trainer": {("Knowledge Library","View")},
    "Surveyor": {("Knowledge Library","View")},
    "NSC Surveyor": {("Knowledge Library","View")},
    "In-Service Surveyor": {("Knowledge Library","View")},
    "Plan Appraiser": {("Knowledge Library","View"),("Interpretation Portal","View")},
    "Industrial Surveyor": {("Knowledge Library","View"),("Interpretation Portal","View")},
    "Rule Development Rep": {("Interpretation Portal","View"),("Interpretation Portal","Approve"),("Knowledge Library","View"),("Accreditation Readiness","View")},
    "QMS Auditor": {("Accreditation Readiness","View"),("Knowledge Library","View")},
    "Trainee": {("Knowledge Library","View")},
    "On Probation": {("Knowledge Library","View")},
}

def scope_permission_allowed(role: str, module: str, action: str, scope: str) -> bool:
    if scope != "Organization-wide":
        return True
    if role in ORG_ROLES:
        return True
    return (module, action) in ORG_SCOPE_PERMISSION_ALLOWLIST.get(role, set())


def _actor_departments(actor: dict, users: pd.DataFrame) -> set[str]:
    uid = str(actor.get("user_id", ""))
    if users is None or users.empty or "user_id" not in users.columns:
        return set()
    rows = users[users["user_id"].astype(str) == uid]
    if rows.empty:
        return set()
    vals: set[str] = set()
    for _, r in rows.iterrows():
        for col in DEPARTMENT_COLUMNS:
            if col in r:
                vals.update(x.strip() for x in re.split(r"[,;|]+", str(r.get(col) or "")) if x.strip())
    # normalized user_departments is handled by callers where needed
    return vals


def allowed_user_ids(actor: dict, users: pd.DataFrame, user_departments: pd.DataFrame | None = None) -> set[str]:
    uid = str(actor.get("user_id", ""))
    role = str(actor.get("role", ""))
    if not uid or users is None or users.empty or "user_id" not in users.columns:
        return {uid} if uid else set()
    if role in ORG_ROLES:
        return set(users["user_id"].astype(str))
    if role in SELF_ROLES:
        return {uid}
    ids = {uid}
    depts = _actor_departments(actor, users)
    if user_departments is not None and not user_departments.empty and "user_id" in user_departments.columns:
        own = user_departments[user_departments["user_id"].astype(str) == uid]
        if "department" in own.columns:
            depts |= set(own["department"].dropna().astype(str).str.strip())
    if role in ASSIGNED_ROLES:
        # Supervisor scope is relationship-based only. Department membership does
        # not grant visibility of every learner.
        for col in ("tutor_id", "mentor_id", "trainer_id", "assigner_id"):
            if col in users.columns:
                ids.update(users.loc[users[col].astype(str) == uid, "user_id"].astype(str))
        return ids
    if role in CASE_ROLES:
        # CRB members see cases explicitly assigned to them; no department fallback.
        for col in ("crb_member_id", "assigned_crb_member_id", "assigned_user_id", "owner_id"):
            if col in users.columns:
                ids.update(users.loc[users[col].astype(str) == uid, "user_id"].astype(str))
        return ids
    # Department/case roles: department first, explicit assignment second.
    if depts:
        vals = users.get("primary_department", pd.Series(dtype=str)).fillna("").astype(str) + ";" + users.get("department", pd.Series(dtype=str)).fillna("").astype(str)
        mask = vals.apply(lambda s: bool(depts & {x.strip() for x in re.split(r"[,;|]+", s) if x.strip()}))
        ids.update(users.loc[mask, "user_id"].astype(str))
    for col in ASSIGNMENT_COLUMNS:
        if col in users.columns:
            ids.update(users.loc[users[col].astype(str) == uid, "user_id"].astype(str))
    return ids


def scope_allows(actor: dict, scope: str, row: dict | None = None, users: pd.DataFrame | None = None, user_departments: pd.DataFrame | None = None, module: str | None = None, action: str | None = None) -> bool:
    """Fail-closed record-scope decision used by all repository reads/writes.

    The actor must first be allowed to use the requested scope for their role.
    Record ownership/assignment/department membership is then evaluated from the
    normalized user and assignment fields.  Rows without a subject user are
    treated as module-level records and rely on the page/action permission gate.
    """
    actor = actor or {}
    role = str(actor.get("role", "")).strip()
    uid = str(actor.get("user_id", "")).strip()
    if not role or not uid:
        return False
    allowed = ROLE_ALLOWED_SCOPES.get(role, {"Own"})
    if scope not in allowed:
        return False
    if not scope_permission_allowed(role, module or "", action or "View", scope):
        return False
    if scope == "Organization-wide":
        return role in ORG_ROLES
    if row is None:
        return True

    record = dict(row)
    subject = record_user_id(record)
    # Module-level records (e.g. knowledge/rule definitions) do not carry a user id.
    # They remain protected by can_action/page permission and are not fabricated as
    # employee-scoped records here.
    if not subject and not any(str(record.get(c) or '').strip() for c in ASSIGNMENT_COLUMNS + DEPARTMENT_COLUMNS):
        return True

    if scope == "Own":
        return bool(subject and subject == uid)

    if scope == "Assigned":
        # Direct assignee/owner/witness relationships on the row.
        for col in set(ASSIGNMENT_COLUMNS) | {"witness_id", "proposed_witness_id", "assessor_id", "reviewer_id", "assigned_crb_member_id", "crb_member_id"}:
            if str(record.get(col) or '').strip() == uid:
                return True
        if users is not None and not users.empty:
            return bool(subject and subject in allowed_user_ids(actor, users, user_departments))
        return False

    if scope in {"Department", "Multiple Departments"}:
        if users is None or users.empty:
            return False
        actor_depts = _actor_departments(actor, users)
        if user_departments is not None and not user_departments.empty and "user_id" in user_departments.columns and "department" in user_departments.columns:
            own = user_departments[user_departments["user_id"].astype(str) == uid]
            actor_depts |= {str(x).strip() for x in own["department"].dropna().tolist() if str(x).strip()}
        if not actor_depts:
            return False
        row_depts = {str(record.get(c) or '').strip() for c in DEPARTMENT_COLUMNS if str(record.get(c) or '').strip()}
        if subject and not row_depts and "user_id" in users.columns:
            hit = users[users["user_id"].astype(str) == subject]
            if not hit.empty:
                rr = hit.iloc[0].to_dict()
                row_depts |= {str(rr.get(c) or '').strip() for c in DEPARTMENT_COLUMNS if str(rr.get(c) or '').strip()}
            if user_departments is not None and not user_departments.empty and "user_id" in user_departments.columns and "department" in user_departments.columns:
                sr = user_departments[user_departments["user_id"].astype(str) == subject]
                row_depts |= {str(x).strip() for x in sr["department"].dropna().tolist() if str(x).strip()}
        return bool(actor_depts & row_depts)
    return False

def filter_frame(frame: pd.DataFrame, actor: dict, users: pd.DataFrame, user_departments: pd.DataFrame | None = None, module: str | None = None, action: str = "View") -> pd.DataFrame:
    """Return only records visible to *actor* using the canonical scope engine.

    The function intentionally returns a copy and fails closed on malformed input.
    """
    if frame is None or frame.empty:
        return frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    role = str((actor or {}).get("role", ""))
    if not role or not str((actor or {}).get("user_id", "")):
        return frame.iloc[0:0].copy()
    inferred_module = module or ""
    scope = scope_for_actor_module(actor, inferred_module) if inferred_module else (
        "Organization-wide" if role in ORG_ROLES else "Assigned" if role in ASSIGNED_ROLES else "Department" if role in DEPARTMENT_ROLES else "Own"
    )
    # Tables with no user/assignment/department identity are module-level definitions.
    identity_cols = set(USER_ID_COLUMNS) | set(ASSIGNMENT_COLUMNS) | set(DEPARTMENT_COLUMNS) | {"witness_id","assessor_id","reviewer_id"}
    if not (identity_cols & set(frame.columns)):
        return frame.copy()
    mask = frame.apply(lambda r: scope_allows(actor, scope, r.to_dict(), users, user_departments, module=inferred_module, action=action), axis=1)
    return frame.loc[mask].copy()


TABLE_SCOPE_MODULES = {
    'users':'Users & Roles','user_departments':'Departments','development_plans':'Development Plans',
    'succession_plans':'Succession Planning','workforce_forecasts':'Workforce Planning',
    'training_requirements':'Training Matrix','trainings':'Training','training_records':'Training','question_bank':'Training',
    'qualification_path_versions':'Training','qualification_path_levels':'Training',
    'qualification_modules':'Training','qualification_level_modules':'Training',
    'qualification_module_requirements':'Training','qualification_module_training':'Training',
    'qualification_assignments':'Training','qualification_assignment_state':'Training',
    'qualification_module_progress':'Training','training_assessment_configs':'Training',
    'training_live_sessions':'Training','training_resources':'Training',
    'training_session_attendance':'Training','training_mcq_drafts':'Training','user_assignments':'Users & Roles',
    'qualification_practical_requirements':'Training','guided_practical_training':'Practical / Witness',
    'independent_practical_assessments':'Practical / Witness','independent_practical_records':'Practical / Witness',
    'module_practical_gates':'Practical / Witness','module_trainer_readiness':'Practical / Witness',
    'probation_progression_approvals':'Training','probation_transitions':'Training',
    'crb_case_board_assignments':'CRB','case_correspondence':'CRB',
    'cpd_records':'CPD','competency_matrix':'Competency','competency_reviews':'Competency',
    'witness_surveys':'Practical / Witness','supervised_activities':'Practical / Witness',
    'practical_requirement_templates':'Practical / Witness','practical_activities':'Practical / Witness',
    'practical_assessments':'Practical / Witness','practical_evidence_links':'Practical / Witness',
    'gap_advisor_actions':'Gap Advisor','competency_ncrs':'NCR / Corrective Action',
    'knowledge_library':'Knowledge Library','knowledge_versions':'Knowledge Library',
    'authorization_requests':'Authorization','authorization_certificates':'Authorization','authorization_certificate_history':'Authorization',
    'authorization_restrictions':'Restrictions','crb_reviews':'CRB',
    'technical_reviews':'Technical Reviews','qms_audits':'QMS','qms_compliance_items':'QMS',
    'qms_management_reviews':'QMS','qms_evidence_reviews':'QMS',
    'accreditation_assessments':'Accreditation Readiness','accreditation_evidence':'Accreditation Readiness',
    'technical_interpretations':'Interpretation Portal','rule_change_requests':'Rule Development',
    'job_requests':'Job Allocation','job_assignments':'Job Allocation','client_feedback':'Client Feedback',
    'kpi_snapshots':'Performance & KPI','kpi_definitions':'Performance & KPI',
    'notifications':'Notifications','files':'Documents & Storage','gm_watchlist':'Dashboard',
}

def scope_for_actor_module(actor: dict, module: str) -> str:
    role = str(actor.get('role',''))
    defaults = ROLE_MODULE_SCOPE_DEFAULTS.get(role, {})
    scopes = defaults.get(module)
    if scopes:
        ordered = ('Organization-wide','Department','Multiple Departments','Assigned','Own')
        for candidate in ordered:
            if candidate in scopes:
                return candidate
    if role in ORG_ROLES:
        return 'Organization-wide'
    if role in ASSIGNED_ROLES:
        return 'Assigned'
    if role in DEPARTMENT_ROLES:
        return 'Department'
    return 'Own'

def record_user_id(row: dict | None) -> str:
    if not row:
        return ''
    for col in USER_ID_COLUMNS:
        value = str(row.get(col) or '').strip()
        if value:
            return value
    return ''

def record_scope_allowed(actor: dict, module: str, action: str, row: dict | None, users: pd.DataFrame, user_departments: pd.DataFrame | None = None) -> bool:
    role = str(actor.get('role',''))
    scope = scope_for_actor_module(actor, module)
    if module == 'Technical Reviews' and row is not None and not discipline_allowed(role, row.get('discipline')):
        return False
    if module == 'Practical / Witness' and row is not None:
        uid = str(actor.get('user_id',''))
        subject = str(row.get('user_id') or row.get('trainee_id') or '').strip()
        witness = str(row.get('witness_id') or row.get('proposed_witness_id') or '').strip()
        if witness and witness == uid and subject != uid:
            return True
        if subject and subject == uid:
            return True

    # Modules without a user-record scope use their explicit policy/role grant.
    if module in {'Departments','Users & Roles','Administration','System Settings','Audit Trail','Backup & Recovery','Permissions'}:
        return role in {'Admin','GM'}
    return scope_allows(actor, scope, row, users, user_departments, module=module, action=action)


TABLE_MUTATION_MODULES = {
    **TABLE_SCOPE_MODULES,
    'departments':'Departments','roles':'Permissions','permissions':'Permissions','role_permissions':'Permissions',
    'user_permission_overrides':'Permissions','system_settings':'System Settings','backup_records':'Backup & Recovery',
    'recovery_requests':'Backup & Recovery','restore_tests':'Backup & Recovery',
}
