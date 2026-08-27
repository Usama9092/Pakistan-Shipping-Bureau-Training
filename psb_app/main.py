from psb_app.services.database_service import ensure_accreditation_schema, init_db
from psb_app.common import (
    APP_TITLE,
    LOGO_PATH,
    actor_get,
    require_persistent_backend,
    st,
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

def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "⚓", layout="wide", initial_sidebar_state="expanded")
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = uuid.uuid4().hex
    apply_style()
    require_persistent_backend()
    init_db()
    ensure_accreditation_schema()
    query_params = st.query_params
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
