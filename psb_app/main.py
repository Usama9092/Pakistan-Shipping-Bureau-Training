import hashlib
import secrets

from psb_app.services.database_service import ensure_accreditation_schema, init_db
from psb_app.common import (
    APP_TITLE,
    LOGO_PATH,
    actor_get,
    db_update,
    exec_sql,
    now,
    phash,
    query_sql,
    require_persistent_backend,
    st,
    temp_password,
    uuid,
)
from psb_app.pages.auth_ui import (
    apply_style,
    dashboard_page,
    header,
    require_login,
    sidebar,
)
from psb_app.pages.admin import (
    audit_trail_page,
    backup_recovery_page,
    departments_page,
    permissions_page,
    system_settings_page,
    users_roles_page,
)
from psb_app.pages.people import (
    development_plan_page,
    employee_profile_page,
    succession_planning_page,
    workforce_planning_page,
)
from psb_app.pages.training import (
    cpd_page,
    knowledge_page,
    training_dashboard_page,
    training_matrix_page,
    training_page,
)
from psb_app.pages.competency import (
    competency_gap_advisor_page,
    competency_ncr_page,
    competency_page,
)
from psb_app.pages.practical_witness import (
    practical_page,
    my_witness_assessments_page,
    practical_governance_page,
)
from psb_app.pages.authorization import (
    annual_competency_board_page,
    authorization_page,
    authorization_restrictions_page,
    crb_page,
    revalidation_page,
    technical_authority_page,
)
from psb_app.pages.quality import (
    accreditation_readiness_page,
    interpretation_portal_page,
    qms_page,
    technical_reviews_page,
)
from psb_app.pages.operations import (
    client_feedback_page,
    job_allocation_page,
    kpi_page,
)
from psb_app.pages.public_verify import (
    public_qr_verify_page,
    qr_verify_page,
)
from psb_app.pages.role_workspaces import (
    assigned_learners_page,
    assigned_trainees_page,
    audit_workspace_page,
    certificates_page,
    crb_case_workspace_page,
    management_review_dashboard_page,
    my_audits_page,
    my_authorization_page,
    my_performance_page,
    my_technical_reviews_page,
    probation_progress_page,
    probation_review_page,
)
from psb_app.pages.executive import management_executive_dashboard_page
from psb_app.pages.gm import (
    gm_administration_page,
    gm_capability_page,
    gm_executive_command_center_page,
    gm_governance_page,
    gm_notifications_page,
    gm_operations_page,
    gm_people_page,
    gm_profile_page,
    gm_quality_page,
    gm_reports_page,
)
from psb_app.pages.qualification import (
    my_qualification_page, my_development_page, trainer_paths_training_page,
    department_qualification_page, people_capability_page, authorization_decisions_page,
    authorization_cases_page, my_authorization_cases_page, crb_cases_page,
)
from core.view_context import set_context
from core.production import page_execution as _page_execution
from core.system_write import system_write


_RECOVERY_CODE_SHA256 = "4116b42ce440807695da5ca6f9333f72254e4ec40bfa20448301f284fe2d11c6"
_SCOPED_RECOVERY_TARGETS = {
    "USR-ADMIN": "admin",
    "USR-13F94456": "umairadeem",
    "USR-D7C7A414": "usmanzafar",
}


def _scoped_recovery_page() -> None:
    """Short-lived owner recovery page for exactly three locked accounts."""
    st.markdown("## PSB Account Recovery")
    st.caption("This temporary recovery tool is restricted to Admin, Umair Adeem and Usman Zafar only.")

    existing = st.session_state.get("psb_scoped_recovery_passwords")
    if existing:
        st.success("Temporary passwords were generated successfully. Copy them now; each user must change the password immediately after login.")
        st.table([{"Login ID": login_id, "Temporary Password": password} for login_id, password in existing.items()])
        return

    with st.form("psb_scoped_account_recovery"):
        recovery_code = st.text_input("Recovery code", type="password")
        submitted = st.form_submit_button("Generate temporary passwords for the three approved accounts")

    if not submitted:
        return

    supplied_hash = hashlib.sha256(str(recovery_code or "").encode("utf-8")).hexdigest()
    if not secrets.compare_digest(supplied_hash, _RECOVERY_CODE_SHA256):
        st.error("Invalid recovery code.")
        return

    generated = {}
    for user_id, login_key in _SCOPED_RECOVERY_TARGETS.items():
        rows = query_sql(
            "select user_id, login_id, status from users "
            "where user_id = :uid and lower(login_id) = :login_key",
            {"uid": user_id, "login_key": login_key},
        )
        if rows.empty or str(rows.iloc[0].get("status", "")) != "Active":
            st.error(f"Recovery stopped because the approved account {login_key} was not found as Active.")
            return

    for user_id, login_key in _SCOPED_RECOVERY_TARGETS.items():
        new_password = temp_password()
        with system_write("owner-authorized short-lived account recovery"):
            db_update(
                "users",
                "user_id",
                user_id,
                {"password_hash": phash(new_password), "force_password_change": "Yes"},
            )
        exec_sql(
            "delete from login_security_state where lower(login_key) = :login_key",
            {"login_key": login_key},
        )
        exec_sql(
            "update auth_sessions set revoked_on = coalesce(revoked_on, :ts) "
            "where user_id = :uid and revoked_on is null",
            {"ts": now(), "uid": user_id},
        )
        generated[login_key] = new_password

    st.session_state["psb_scoped_recovery_passwords"] = generated
    st.success("Recovery completed for exactly three approved accounts.")
    st.table([{"Login ID": login_id, "Temporary Password": password} for login_id, password in generated.items()])


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "⚓", layout="wide", initial_sidebar_state="expanded")
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = uuid.uuid4().hex
    apply_style()
    require_persistent_backend()
    init_db()
    ensure_accreditation_schema()
    query_params = st.query_params
    if str(query_params.get("account_recovery", "") or "").strip() == "1":
        _scoped_recovery_page()
        return
    public_cert = str(query_params.get("verify", "") or "").strip()
    if public_cert:
        public_qr_verify_page(public_cert)
        return
    actor = require_login()
    st.session_state["psb_actor"] = actor
    page = sidebar(actor)
    view_context = set_context(actor, page)
    st.session_state['view_context'] = view_context
    header(actor, page, view_context)
    route = {
        "Executive Command Center": gm_executive_command_center_page, "GM People": gm_people_page, "GM Capability": gm_capability_page,
        "GM Governance": gm_governance_page, "GM Quality": gm_quality_page, "GM Operations": gm_operations_page,
        "GM Administration": gm_administration_page, "GM Reports & Analytics": gm_reports_page, "GM Notifications": gm_notifications_page, "GM My Profile": gm_profile_page,
        "Dashboard": dashboard_page, "Employee Profile": employee_profile_page, "People / Employee Profile": employee_profile_page,
        "My Qualification": my_qualification_page, "My Development": my_development_page, "My Learners": assigned_learners_page, "My Trainees": assigned_trainees_page,
        "Qualification Paths": trainer_paths_training_page, "Qualification Workspace": trainer_paths_training_page, "Department Qualification": department_qualification_page, "People & Capability": people_capability_page,
        "CRB Cases": crb_cases_page, "Authorization Decisions": authorization_decisions_page, "Authorization Cases": authorization_cases_page, "My Authorization Cases": my_authorization_cases_page, "My Assessments": my_witness_assessments_page, "Certificates": certificates_page,
        "Assigned Learners": assigned_learners_page, "Assigned Trainees": assigned_trainees_page, "Development Plans": development_plan_page, "Succession Planning": succession_planning_page, "Workforce Planning": workforce_planning_page,
        "Training Dashboard": training_dashboard_page, "Training Matrix": training_matrix_page, "Training": training_page, "CPD": cpd_page,
        "Competency": competency_page, "Practical / Witness": practical_page, "My Witness Assessments": my_witness_assessments_page, "Practical Governance": practical_governance_page, "Gap Advisor": competency_gap_advisor_page, "NCR / Corrective Action": competency_ncr_page, "Knowledge Library": knowledge_page,
        "Authorization": authorization_page, "My CRB Cases": crb_page, "CRB": crb_page, "Technical Authority": technical_authority_page, "Restrictions": authorization_restrictions_page, "Annual Review": annual_competency_board_page, "Revalidation": revalidation_page,
        "Rule Development": interpretation_portal_page, "Technical Reviews": technical_reviews_page, "QMS": qms_page, "Accreditation Readiness": accreditation_readiness_page, "Interpretation Portal": interpretation_portal_page,
        "My Jobs": job_allocation_page, "My Client Feedback": client_feedback_page, "My Performance": my_performance_page, "Job Allocation": job_allocation_page, "Client Feedback": client_feedback_page, "Performance & KPI": kpi_page,
        "Users & Roles": users_roles_page, "Departments": departments_page, "Permissions": permissions_page, "System Settings": system_settings_page, "Audit Trail": audit_trail_page, "Backup & Recovery": backup_recovery_page, "QR Verify": qr_verify_page,
        "Certificate Center": certificates_page, "Certificates": certificates_page, "My Certificates": certificates_page, "My Authorization": my_authorization_page, "My Technical Reviews": my_technical_reviews_page, "My Audits": my_audits_page, "Audit Workspace": audit_workspace_page, "CRB Case Workspace": crb_case_workspace_page, "Management Review Dashboard": management_review_dashboard_page, "Executive Dashboard": management_executive_dashboard_page, "Probation Review": probation_review_page, "Probation Progress": probation_progress_page,
    }
    fn = route.get(page)
    if fn is None:
        st.markdown("<div class='psb-empty'>This page is not available for your current role.</div>", unsafe_allow_html=True)
        return
    try:
        with _page_execution(page, actor_get(actor, "role", "")):
            with st.spinner(f"Loading {page}…"):
                fn(actor)
    except Exception:
        request_id = uuid.uuid4().hex[:12]
        import logging
        logging.getLogger("psb.production").exception("unhandled_page_error request_id=%s page=%s", request_id, page)
        st.error(f"We could not load this page. Reference: {request_id}")
        st.info("Your data has not been intentionally changed. Please retry; if the problem continues, provide the reference to an administrator.")

if __name__ == "__main__":
    main()