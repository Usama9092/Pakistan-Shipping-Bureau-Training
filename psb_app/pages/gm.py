from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from psb_app.common import (
    actor_get,
    audit,
    db_all,
    db_count,
    db_update,
    db_insert,
    db_where,
    table_exists,
    uid,
)

GM_ROLE = "GM"


def _gm_only(actor: dict) -> bool:
    if actor_get(actor, "role", "") != GM_ROLE:
        st.error("This executive workspace is reserved for the GM role.")
        return False
    return True


def _go(page: str, *, target_user_id: str = "") -> None:
    if target_user_id:
        st.session_state["profile_target_user_id"] = target_user_id
    st.session_state["psb_current_page"] = page
    st.rerun()


def _safe_all(table_name: str) -> pd.DataFrame:
    if not table_exists(table_name):
        return pd.DataFrame()
    try:
        return db_all(table_name)
    except Exception:
        return pd.DataFrame()


def _safe_count(table_name: str, where: str | None = None) -> int:
    if not table_exists(table_name):
        return 0
    try:
        return int(db_count(table_name, where))
    except Exception:
        return 0


def _status_count(df: pd.DataFrame, values: list[str], column: str = "status") -> int:
    if df.empty or column not in df.columns:
        return 0
    wanted = {v.lower() for v in values}
    return int(df[column].fillna("").astype(str).str.lower().isin(wanted).sum())


def _open_count(df: pd.DataFrame, column: str = "status") -> int:
    if df.empty or column not in df.columns:
        return 0
    closed = {"closed", "resolved", "completed", "complete", "cancelled", "canceled", "rejected"}
    return int((~df[column].fillna("").astype(str).str.lower().isin(closed)).sum())


def _days_to(value) -> int | None:
    try:
        return (datetime.strptime(str(value)[:10], "%Y-%m-%d").date() - date.today()).days
    except Exception:
        return None


def _header(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def _metric_row(items: list[tuple[str, object]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)


def _dataframe(df: pd.DataFrame, cols: list[str] | None = None, *, max_rows: int = 100) -> None:
    if df is None or df.empty:
        st.info("No records are available for this view.")
        return
    shown = df.copy()
    if cols:
        shown = shown[[c for c in cols if c in shown.columns]]
    st.dataframe(shown.head(max_rows), use_container_width=True, hide_index=True)


def _nav_cards(cards: list[tuple[str, str, str]]) -> None:
    """Render compact drill-down cards as three-column rows."""
    for i in range(0, len(cards), 3):
        row = cards[i:i + 3]
        cols = st.columns(3)
        for col, (title, detail, page) in zip(cols, row):
            with col:
                st.markdown(f"**{title}**")
                st.caption(detail)
                if st.button(f"Open {title}", key=f"gm_open_{page}_{i}_{title}", use_container_width=True):
                    _go(page)


def _decision_items() -> pd.DataFrame:
    rows: list[dict] = []
    ncr = _safe_all("competency_ncrs")
    if not ncr.empty:
        status = ncr.get("status", pd.Series(index=ncr.index, dtype=str)).fillna("").astype(str).str.lower()
        severity = ncr.get("severity", pd.Series(index=ncr.index, dtype=str)).fillna("").astype(str).str.lower()
        due = ncr.get("due_date", pd.Series(index=ncr.index, dtype=str)).fillna("").astype(str)
        for _, r in ncr[(~status.isin(["closed", "resolved"])) & severity.isin(["critical", "high"])].head(8).iterrows():
            rows.append({
                "Priority": "Critical" if str(r.get("severity", "")).lower() == "critical" else "High",
                "Area": "Quality",
                "Matter": f"NCR {r.get('ncr_id', r.get('id', ''))}",
                "Owner": r.get("owner_name", r.get("corrective_action_owner_name", "QMR")),
                "Due": r.get("due_date", ""),
                "Route": "NCR / Corrective Action",
            })
    auth = _safe_all("authorization_requests")
    if not auth.empty and "expiry_date" in auth.columns:
        for _, r in auth.iterrows():
            days = _days_to(r.get("expiry_date", ""))
            if days is not None and 0 <= days <= 30:
                rows.append({
                    "Priority": "High" if days <= 14 else "Medium",
                    "Area": "Authorization",
                    "Matter": f"{r.get('name', '')} / {r.get('scope', '')}",
                    "Owner": "Department Manager",
                    "Due": r.get("expiry_date", ""),
                    "Route": "Authorization",
                })
    actions = _safe_all("qms_management_review_actions")
    if not actions.empty:
        status = actions.get("status", pd.Series(index=actions.index, dtype=str)).fillna("").astype(str).str.lower()
        for _, r in actions[~status.isin(["closed", "completed", "complete"])].iterrows():
            days = _days_to(r.get("due_date", ""))
            if days is not None and days < 0:
                rows.append({
                    "Priority": "High",
                    "Area": "Management Review",
                    "Matter": str(r.get("action", r.get("action_text", "Overdue action"))),
                    "Owner": r.get("responsible_owner_name", r.get("owner_name", "")),
                    "Due": r.get("due_date", ""),
                    "Route": "Management Review Dashboard",
                })
    jobs = _safe_all("job_requests")
    if not jobs.empty:
        status = jobs.get("status", pd.Series(index=jobs.index, dtype=str)).fillna("").astype(str).str.lower()
        risk = jobs.get("risk_level", pd.Series(index=jobs.index, dtype=str)).fillna("").astype(str).str.lower()
        for _, r in jobs[(status.isin(["open", "assigned", "in progress"])) & risk.isin(["high", "critical"])].head(6).iterrows():
            rows.append({
                "Priority": "High",
                "Area": "Operations",
                "Matter": f"{r.get('job_id', '')} / {r.get('job_type', '')}",
                "Owner": r.get("assigned_user_name", "Unassigned"),
                "Due": r.get("planned_date", ""),
                "Route": "Job Allocation",
            })
    return pd.DataFrame(rows)


def _global_search(q: str) -> pd.DataFrame:
    q = (q or "").strip().lower()
    if not q:
        return pd.DataFrame()
    results: list[dict] = []
    specs = [
        ("Employee", "users", ["name", "employee_id", "email", "user_id"], "Employee Profile", "user_id"),
        ("Authorization", "authorization_requests", ["authorization_id", "name", "scope", "job_type"], "Authorization", "authorization_id"),
        ("Certificate", "authorization_certificates", ["certificate_id", "name", "scope", "job_type"], "Certificate Center", "certificate_id"),
        ("NCR", "competency_ncrs", ["ncr_id", "name", "requirement", "deficiency"], "NCR / Corrective Action", "ncr_id"),
        ("Audit", "qms_audits", ["audit_id", "audit_type", "standard", "department"], "Audit Workspace", "audit_id"),
        ("Job", "job_requests", ["job_id", "job_title", "job_type", "vessel_name", "client_name"], "Job Allocation", "job_id"),
    ]
    for kind, table_name, fields, route, id_field in specs:
        df = _safe_all(table_name)
        if df.empty:
            continue
        mask = df.apply(lambda r: q in " ".join(str(r.get(f, "")) for f in fields).lower(), axis=1)
        for _, r in df[mask].head(8).iterrows():
            label = " • ".join([str(r.get(f, "")) for f in fields[:3] if str(r.get(f, "")).strip()])
            results.append({"Type": kind, "Result": label, "Reference": r.get(id_field, ""), "Route": route, "User ID": r.get("user_id", "")})
    return pd.DataFrame(results)


def _watchlist(actor: dict) -> None:
    st.markdown("### My Watchlist")
    if not table_exists("gm_watchlist"):
        st.info("Watchlist storage is not available yet.")
        return
    uidv = actor_get(actor, "user_id", "")
    rows = db_where("gm_watchlist", "gm_user_id = :uid", (("uid", uidv),))
    if not rows.empty and "status" in rows.columns:
        rows = rows[rows["status"].fillna("").astype(str) != "Removed"].copy()
    if rows.empty:
        st.caption("Pin an executive matter below to keep it on your personal watchlist.")
    else:
        _dataframe(rows, ["record_type", "record_ref", "title", "risk_level", "status", "due_date", "added_on"], max_rows=30)
        options = [f"{r.get('record_type', '')} — {r.get('record_ref', '')}" for _, r in rows.iterrows()]
        selected = st.selectbox("Watchlist item", options, key="gm_watchlist_selected") if options else ""
        if selected and st.button("Remove from Watchlist", key="gm_watch_remove"):
            ref = selected.split(" — ", 1)[-1]
            target = rows[rows["record_ref"].astype(str) == ref]
            if not target.empty:
                db_update("gm_watchlist", "watch_id", str(target.iloc[0]["watch_id"]), {"status": "Removed"})
                audit("GM Watchlist Removed", ref, actor=actor, entity_type="GM Watchlist", entity_id=ref)
                st.rerun()


def gm_executive_command_center_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Executive Command Center", "Manage by exception, risk, decision and accountability — not by operational browsing.")

    c1, c2, c3 = st.columns([2.2, 1, 1])
    q = c1.text_input("Global search", placeholder="Employee, authorization, certificate, NCR, audit, job…", key="gm_global_search")
    c2.selectbox("Department", ["All"] + sorted(_safe_all("users").get("primary_department", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()), key="gm_exec_department")
    c3.selectbox("Period", ["Current", "30 days", "90 days", "12 months"], key="gm_exec_period")
    search_results = _global_search(q)
    if q.strip():
        st.markdown("#### Search Results")
        if search_results.empty:
            st.info("No matching records found.")
        else:
            for i, r in search_results.head(12).iterrows():
                cols = st.columns([1, 5, 1])
                cols[0].markdown(f"**{r['Type']}**")
                cols[1].write(r["Result"])
                if cols[2].button("Open", key=f"gm_search_open_{i}"):
                    if r["Type"] == "Employee" and str(r.get("User ID", "")):
                        _go("Employee Profile", target_user_id=str(r["User ID"]))
                    _go(str(r["Route"]))

    users = _safe_all("users")
    training = _safe_all("training_records")
    competency = _safe_all("competency_matrix")
    auth = _safe_all("authorization_requests")
    ncr = _safe_all("competency_ncrs")
    jobs = _safe_all("job_requests")
    feedback = _safe_all("client_feedback")
    kpi = _safe_all("kpi_snapshots")

    active_users = len(users[~users.get("status", pd.Series(index=users.index, dtype=str)).fillna("").astype(str).str.lower().isin(["inactive", "disabled", "deactivated"])]) if not users.empty else 0
    training_overdue = _status_count(training, ["Overdue"])
    competency_ready = _status_count(competency, ["Competent", "Authorized", "Ready"])
    auth_active = _status_count(auth, ["Management Approved", "Approved", "Valid", "Active"])
    open_ncr = _open_count(ncr)
    active_jobs = _status_count(jobs, ["Open", "Assigned", "In Progress"])
    low_feedback = 0
    if not feedback.empty and "rating" in feedback.columns:
        low_feedback = int((pd.to_numeric(feedback["rating"], errors="coerce") <= 2).sum())
    overall_kpi = "—"
    if not kpi.empty and "overall_score" in kpi.columns:
        scores = pd.to_numeric(kpi["overall_score"], errors="coerce").dropna()
        if not scores.empty:
            overall_kpi = f"{scores.mean():.0f}%"

    _metric_row([
        ("Active Workforce", active_users),
        ("Active Authorizations", auth_active),
        ("Training Overdue", training_overdue),
        ("Competency Ready", competency_ready),
        ("Open NCR", open_ncr),
        ("Active Jobs", active_jobs),
        ("Low Client Ratings", low_feedback),
        ("Overall KPI", overall_kpi),
    ])

    st.markdown("### Requires GM Attention")
    decisions = _decision_items()
    if decisions.empty:
        st.success("No critical executive exceptions are currently detected.")
    else:
        priority_order = {"Critical": 0, "High": 1, "Medium": 2}
        decisions["_p"] = decisions["Priority"].map(priority_order).fillna(9)
        decisions = decisions.sort_values(["_p", "Due"]).drop(columns=["_p"])
        for i, r in decisions.head(10).iterrows():
            cols = st.columns([1, 1.3, 4, 1.7, 1.3, 1])
            cols[0].markdown("🔴 **Critical**" if r["Priority"] == "Critical" else "🟠 **High**" if r["Priority"] == "High" else "🟡 **Medium**")
            cols[1].write(r["Area"])
            cols[2].write(r["Matter"])
            cols[3].write(r["Owner"] or "—")
            cols[4].write(r["Due"] or "—")
            if cols[5].button("Open", key=f"gm_decision_{i}"):
                _go(str(r["Route"]))

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("### Executive Risk Pulse")
        risk_rows = pd.DataFrame([
            {"Domain": "People", "Signal": "High" if training_overdue >= 5 else "Medium" if training_overdue else "Low", "Driver": f"{training_overdue} overdue training"},
            {"Domain": "Governance", "Signal": "High" if auth_active < max(active_users // 2, 1) else "Low", "Driver": f"{auth_active} active authorizations"},
            {"Domain": "Quality", "Signal": "High" if open_ncr >= 5 else "Medium" if open_ncr else "Low", "Driver": f"{open_ncr} open NCR"},
            {"Domain": "Operations", "Signal": "Medium" if active_jobs >= 8 else "Low", "Driver": f"{active_jobs} active jobs"},
            {"Domain": "Client", "Signal": "High" if low_feedback >= 3 else "Medium" if low_feedback else "Low", "Driver": f"{low_feedback} low ratings"},
        ])
        _dataframe(risk_rows)
    with r2:
        st.markdown("### Decision Inbox")
        if decisions.empty:
            st.info("No executive decision items are open.")
        else:
            _dataframe(decisions, ["Priority", "Area", "Matter", "Owner", "Due"], max_rows=8)

    _watchlist(actor)
    if not decisions.empty and table_exists("gm_watchlist"):
        st.markdown("#### Pin an executive matter")
        labels = [f"{r['Area']} — {r['Matter']}" for _, r in decisions.head(20).iterrows()]
        selected = st.selectbox("Matter", labels, key="gm_watch_add_select")
        if st.button("Add to Watchlist", key="gm_watch_add"):
            idx = labels.index(selected)
            r = decisions.iloc[idx]
            ref = str(r["Matter"])
            existing = db_where("gm_watchlist", "gm_user_id = :uid and record_ref = :ref", (("uid", actor_get(actor, "user_id", "")), ("ref", ref)))
            if existing.empty:
                db_insert("gm_watchlist", {
                    "watch_id": uid("WATCH"), "gm_user_id": actor_get(actor, "user_id", ""),
                    "record_type": r["Area"], "record_ref": ref, "title": r["Matter"],
                    "risk_level": r["Priority"], "status": "Open", "due_date": r["Due"],
                    "route": r["Route"], "added_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                audit("GM Watchlist Added", ref, actor=actor, entity_type="GM Watchlist", entity_id=ref)
                st.success("Added to watchlist.")
                st.rerun()
            else:
                st.info("This matter is already on your watchlist.")

    st.markdown("### Executive Drill-down")
    _nav_cards([
        ("People", "Workforce, succession, employee 360° and development risk.", "GM People"),
        ("Capability", "Training, competency, witness, CPD and capability gaps.", "GM Capability"),
        ("Governance", "Authorization, CRB, technical reviews, restrictions and certificates.", "GM Governance"),
        ("Quality", "Audits, NCR/CAPA, accreditation and management review.", "GM Quality"),
        ("Operations", "Jobs, coverage, client feedback and performance.", "GM Operations"),
        ("Administration", "Users, departments, permissions, settings, audit and recovery.", "GM Administration"),
    ])


def gm_people_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("People", "Strategic workforce, employee readiness, succession and development oversight.")
    users = _safe_all("users")
    plans = _safe_all("development_plans")
    succession = _safe_all("succession_plans")
    workforce = _safe_all("workforce_forecasts")
    tabs = st.tabs(["Overview", "Employees", "Workforce", "Succession", "Development"])
    with tabs[0]:
        active = len(users[~users.get("status", pd.Series(index=users.index, dtype=str)).fillna("").astype(str).str.lower().isin(["inactive", "disabled", "deactivated"])]) if not users.empty else 0
        trainees = _status_count(users, ["Trainee"], column="role")
        probation = _status_count(users, ["On Probation"], column="role")
        _metric_row([("Employees", len(users)), ("Active", active), ("Trainees", trainees), ("On Probation", probation), ("Open Development", _open_count(plans))])
        if not users.empty and "primary_department" in users.columns:
            summary = users.groupby("primary_department", dropna=False).size().reset_index(name="Employees").sort_values("Employees", ascending=False)
            st.markdown("#### Department Coverage")
            _dataframe(summary)
        _nav_cards([
            ("Employee Directory", "Open organization-wide employee 360° records.", "Employee Profile"),
            ("Workforce Planning", "Demand, authorized coverage and resource gaps.", "Workforce Planning"),
            ("Succession Planning", "Critical roles, successors and readiness.", "Succession Planning"),
        ])
    with tabs[1]:
        if users.empty:
            st.info("No employees available.")
        else:
            search = st.text_input("Search employees", placeholder="Name, employee ID, email", key="gm_people_search")
            shown = users.copy()
            if search.strip():
                q = search.lower().strip()
                shown = shown[shown.apply(lambda r: q in " ".join(str(r.get(k, "")) for k in ["name", "employee_id", "email", "role", "department"]).lower(), axis=1)]
            _dataframe(shown, ["employee_id", "name", "role", "primary_department", "department", "competency_level", "availability", "status"], max_rows=100)
            options = [f"{r.get('name','')} — {r.get('employee_id', r.get('user_id',''))} — {r.get('user_id','')}" for _, r in shown.head(100).iterrows()]
            if options:
                selected = st.selectbox("Open Employee 360°", options, key="gm_people_employee")
                if st.button("Open Employee 360°", key="gm_people_open_profile", type="primary"):
                    _go("Employee Profile", target_user_id=selected.rsplit(" — ", 1)[-1])
    with tabs[2]:
        _metric_row([("Forecast Records", len(workforce)), ("High Risk", _status_count(workforce, ["High", "Critical"], column="risk_status"))])
        _dataframe(workforce, ["forecast_period", "department", "role", "required_headcount", "available_headcount", "authorized_headcount", "gap", "risk_status", "mitigation_plan"])
        if st.button("Open Workforce Planning", key="gm_people_workforce"):
            _go("Workforce Planning")
    with tabs[3]:
        _metric_row([("Succession Records", len(succession)), ("Not Ready", _status_count(succession, ["Not Ready"], column="readiness_level"))])
        _dataframe(succession, ["successor_for", "name", "current_role_name", "target_role", "readiness_level", "expected_ready_date", "status"])
        if st.button("Open Succession Planning", key="gm_people_succession"):
            _go("Succession Planning")
    with tabs[4]:
        _metric_row([("Development Actions", len(plans)), ("Open", _open_count(plans))])
        _dataframe(plans, ["name", "plan_title", "objective", "priority", "owner_name", "target_date", "progress_percent", "status"])
        if st.button("Open Development Plans", key="gm_people_development"):
            _go("Development Plans")


def gm_capability_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Capability", "")
    training = _safe_all("training_records")
    competency = _safe_all("competency_matrix")
    witness = _safe_all("witness_surveys")
    cpd = _safe_all("cpd_records")
    gaps = _safe_all("gap_advisor_actions")
    tabs = st.tabs(["Training", "Competency", "Practical / Witness", "CPD", "Capability Gaps"])
    with tabs[0]:
        if not training.empty and "status" in training.columns:
            _dataframe(training["status"].astype(str).value_counts().rename_axis("Status").reset_index(name="Records"))
        if st.button("Open Training", key="gm_cap_training"):
            _go("Training")
    with tabs[1]:
        _dataframe(competency, ["name", "area", "scope", "competency_level", "status", "expiry_date"])
        if st.button("Open Competency", key="gm_cap_comp"):
            _go("Competency")
    with tabs[2]:
        _dataframe(witness, ["name", "job_type", "scope", "witness_date", "outcome", "verification_status"])
        if st.button("Open Practical / Witness", key="gm_cap_witness"):
            _go("Practical / Witness")
    with tabs[3]:
        _dataframe(cpd, ["name", "activity", "category", "hours", "date", "status"])
        if st.button("Open CPD", key="gm_cap_cpd"):
            _go("CPD")
    with tabs[4]:
        _dataframe(gaps, ["name", "gap_category", "gap_title", "priority", "owner_name", "due_date", "status"])
        if st.button("Open Gap Advisor", key="gm_cap_gap"):
            _go("Gap Advisor")


def gm_governance_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Governance", "Authorization and technical governance oversight. GM visibility does not imply technical approval authority.")
    auth = _safe_all("authorization_requests")
    reviews = _safe_all("technical_reviews")
    restrictions = _safe_all("authorization_restrictions")
    certs = _safe_all("authorization_certificates")
    tabs = st.tabs(["Overview", "Authorization", "CRB", "Technical Reviews", "Restrictions", "Certificates", "Revalidation"])
    with tabs[0]:
        _metric_row([
            ("Authorization Pipeline", len(auth)),
            ("Approved / Valid", _status_count(auth, ["Management Approved", "Approved", "Valid", "Active"])),
            ("Technical Reviews Open", _open_count(reviews)),
            ("Restrictions", _open_count(restrictions)),
            ("Certificates", len(certs)),
        ])
        _nav_cards([
            ("Authorization", "Pipeline, evidence and authorization cases.", "Authorization"),
            ("CRB", "Case readiness and board decisions.", "CRB"),
            ("Certificate Center", "Active, expired, revoked, replaced and history.", "Certificate Center"),
        ])
    with tabs[1]:
        _dataframe(auth, ["authorization_id", "name", "job_type", "scope", "status", "current_stage", "expiry_date"])
        if st.button("Open Authorization Workspace", key="gm_gov_auth"):
            _go("Authorization")
    with tabs[2]:
        crb = _safe_all("crb_reviews")
        _dataframe(crb, ["crb_id", "authorization_id", "name", "scope", "final_decision", "review_date", "remarks"])
        if st.button("Open CRB", key="gm_gov_crb"):
            _go("CRB")
    with tabs[3]:
        _dataframe(reviews, ["review_id", "review_type", "name", "discipline", "status", "assigned_reviewer_name", "due_date"])
        if st.button("Open Technical Reviews", key="gm_gov_review"):
            _go("Technical Reviews")
    with tabs[4]:
        _dataframe(restrictions, ["restriction_id", "name", "scope", "restriction_type", "restriction_detail", "effective_date", "expiry_date", "status"])
        if st.button("Open Restrictions", key="gm_gov_restrict"):
            _go("Restrictions")
    with tabs[5]:
        _dataframe(certs, ["certificate_id", "name", "scope", "job_type", "issue_date", "expiry_date", "status"])
        if st.button("Open Certificate Center", key="gm_gov_cert"):
            _go("Certificate Center")
    with tabs[6]:
        reval = _safe_all("revalidation_requests")
        _dataframe(reval, ["revalidation_id", "name", "scope", "final_status", "due_date", "updated_on"])
        if st.button("Open Revalidation", key="gm_gov_revalidation"):
            _go("Revalidation")


def gm_quality_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Quality", "Quality health, audits, NCR/CAPA, accreditation and management-review accountability.")
    audits = _safe_all("qms_audits")
    ncr = _safe_all("competency_ncrs")
    accred = _safe_all("accreditation_evidence")
    reviews = _safe_all("qms_management_reviews")
    actions = _safe_all("qms_management_review_actions")
    tabs = st.tabs(["Overview", "Audits", "NCR / CAPA", "Accreditation", "Management Review", "Interpretations", "Knowledge"])
    with tabs[0]:
        _metric_row([("Open Audits", _open_count(audits)), ("Open NCR", _open_count(ncr)), ("Critical NCR", _status_count(ncr, ["Critical"], column="severity")), ("Accreditation Evidence", len(accred)), ("Management Actions Open", _open_count(actions))])
        _nav_cards([
            ("Audit Workspace", "Audit programme, evidence, findings, CAPA and closure.", "Audit Workspace"),
            ("NCR / CAPA", "Requirement, deficiency, corrective action and verification.", "NCR / Corrective Action"),
            ("Management Review", "Inputs, decisions, actions and closure.", "Management Review Dashboard"),
        ])
    with tabs[1]:
        _dataframe(audits, ["audit_id", "audit_type", "standard", "department", "lead_auditor_name", "status", "overall_result", "due_date"])
        if st.button("Open Audit Workspace", key="gm_quality_audit"):
            _go("Audit Workspace")
    with tabs[2]:
        _dataframe(ncr, ["ncr_id", "source", "requirement", "deficiency", "severity", "owner_name", "due_date", "verification_status", "status"])
        if st.button("Open NCR / CAPA", key="gm_quality_ncr"):
            _go("NCR / Corrective Action")
    with tabs[3]:
        _dataframe(accred, ["standard", "clause", "requirement", "status", "owner", "last_reviewed"])
        if st.button("Open Accreditation Readiness", key="gm_quality_accred"):
            _go("Accreditation Readiness")
    with tabs[4]:
        _metric_row([("Reviews", len(reviews)), ("Open Actions", _open_count(actions))])
        _dataframe(actions, ["review_id", "action", "responsible_owner_name", "due_date", "progress_percent", "status", "closure_note"])
        if st.button("Open Management Review", key="gm_quality_mr"):
            _go("Management Review Dashboard")
    with tabs[5]:
        if st.button("Open Interpretation Portal", key="gm_quality_interp"):
            _go("Interpretation Portal")
    with tabs[6]:
        if st.button("Open Knowledge Library", key="gm_quality_knowledge"):
            _go("Knowledge Library")


def gm_operations_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Operations & Performance", "Operational coverage, service delivery, client sentiment and performance outcomes.")
    jobs = _safe_all("job_requests")
    feedback = _safe_all("client_feedback")
    kpi = _safe_all("kpi_snapshots")
    tabs = st.tabs(["Overview", "Jobs", "Resource Coverage", "Client Feedback", "Performance"])
    with tabs[0]:
        _metric_row([("Active Jobs", _status_count(jobs, ["Open", "Assigned", "In Progress"])), ("Unassigned", int(jobs.get("assigned_user_id", pd.Series(index=jobs.index, dtype=str)).fillna("").eq("").sum()) if not jobs.empty else 0), ("Feedback Records", len(feedback)), ("KPI Snapshots", len(kpi))])
        _nav_cards([
            ("Job Allocation", "Eligibility, assignment, coverage and conflicts.", "Job Allocation"),
            ("Client Feedback", "Sentiment, complaints and service trends.", "Client Feedback"),
            ("Performance", "Organization → department → employee performance.", "Performance & KPI"),
        ])
    with tabs[1]:
        _dataframe(jobs, ["job_id", "job_title", "job_type", "required_department", "assigned_user_name", "planned_date", "priority", "risk_level", "status"])
        if st.button("Open Job Allocation", key="gm_ops_jobs"):
            _go("Job Allocation")
    with tabs[2]:
        if not jobs.empty and "required_department" in jobs.columns:
            summary = jobs.groupby(["required_department", "status"], dropna=False).size().reset_index(name="Jobs")
            _dataframe(summary)
        else:
            st.info("No department-level operational coverage data is available.")
    with tabs[3]:
        if not feedback.empty and "rating" in feedback.columns:
            ratings = pd.to_numeric(feedback["rating"], errors="coerce").dropna()
            st.metric("Average Rating", f"{ratings.mean():.1f}/5" if not ratings.empty else "—")
        _dataframe(feedback, ["feedback_id", "client_name", "project_or_vessel", "name", "rating", "feedback_type", "comments", "received_on"])
        if st.button("Open Client Feedback", key="gm_ops_feedback"):
            _go("Client Feedback")
    with tabs[4]:
        _dataframe(kpi, ["name", "period_start", "period_end", "overall_score", "status", "calculation_version"])
        if st.button("Open Performance & KPI", key="gm_ops_kpi"):
            _go("Performance & KPI")


def gm_administration_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Administration", "Identity, organization, permissions, settings, immutable audit and recovery governance.")
    users = _safe_all("users")
    depts = _safe_all("departments")
    perms = _safe_all("permissions")
    audits = _safe_all("audit_trail")
    _metric_row([("Users", len(users)), ("Departments", len(depts)), ("Permission Definitions", len(perms)), ("Audit Events", len(audits))])
    st.info("GM administration authority covers system governance. Technical competency, CRB and QMS approvals remain owned by their authorized business roles.")
    _nav_cards([
        ("Users & Roles", "Identity, departments, roles, capabilities and access review.", "Users & Roles"),
        ("Departments", "Department structure, heads, deputies and membership.", "Departments"),
        ("Permissions", "Role → module → action → scope authority.", "Permissions"),
        ("System Settings", "Security, sessions, notifications and workflow settings.", "System Settings"),
        ("Audit Trail", "Immutable who/what/when/before/after governance history.", "Audit Trail"),
        ("Backup & Recovery", "Backup status, recovery requests and restore tests.", "Backup & Recovery"),
    ])


def gm_reports_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Reports & Analytics", "One report center over authoritative source records — no duplicate reporting database.")
    categories = [
        ("Workforce", "Workforce Planning"), ("Training", "Training Dashboard"), ("Competency", "Competency"),
        ("Authorization", "Authorization"), ("Technical", "Technical Reviews"), ("Quality", "QMS"),
        ("Operations", "Job Allocation"), ("Client", "Client Feedback"), ("KPI", "Performance & KPI"), ("Audit", "Audit Trail"),
    ]
    st.markdown("### Report Categories")
    _nav_cards([(name, "Open live source data and apply the module's filters/export.", page) for name, page in categories])
    st.markdown("### Executive Snapshot")
    snapshot = pd.DataFrame([
        {"Area": "People", "Records": _safe_count("users")},
        {"Area": "Training", "Records": _safe_count("training_records")},
        {"Area": "Competency", "Records": _safe_count("competency_matrix")},
        {"Area": "Authorization", "Records": _safe_count("authorization_requests")},
        {"Area": "Quality", "Records": _safe_count("competency_ncrs")},
        {"Area": "Operations", "Records": _safe_count("job_requests")},
        {"Area": "Client", "Records": _safe_count("client_feedback")},
    ])
    _dataframe(snapshot)


def gm_notifications_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("Notifications", "")
    uidv = actor_get(actor, "user_id", "")
    notes = db_where("notifications", "user_id = :uid", (("uid", uidv),)) if table_exists("notifications") else pd.DataFrame()
    if notes.empty:
        st.info("No notifications are assigned to the GM account.")
        return
    if "type" in notes.columns:
        _dataframe(notes["type"].astype(str).value_counts().rename_axis("Category").reset_index(name="Notifications"))
    _dataframe(notes.sort_values("created_on", ascending=False) if "created_on" in notes.columns else notes, ["created_on", "type", "subject", "message", "status"], max_rows=100)


def gm_profile_page(actor: dict) -> None:
    if not _gm_only(actor):
        return
    _header("My Profile", "GM self-service identity, roles, departments, security and sessions.")
    uidv = actor_get(actor, "user_id", "")
    user = db_where("users", "user_id = :uid", (("uid", uidv),))
    if user.empty:
        st.warning("Your user profile could not be loaded.")
        return
    r = user.iloc[0]
    _metric_row([("Role", r.get("role", "GM")), ("Department", r.get("primary_department", r.get("department", ""))), ("Account", r.get("account_status", r.get("status", ""))), ("Availability", r.get("availability", ""))])
    tabs = st.tabs(["Profile", "Departments", "Roles & Access", "Security", "Sessions"])
    with tabs[0]:
        st.write(f"**Name:** {r.get('name','')}")
        st.write(f"**Employee ID:** {r.get('employee_id','')}")
        st.write(f"**Email:** {r.get('email','')}")
        st.write(f"**Current Location:** {r.get('current_location','')}")
    with tabs[1]:
        depts = db_where("user_departments", "user_id = :uid", (("uid", uidv),)) if table_exists("user_departments") else pd.DataFrame()
        _dataframe(depts, ["department", "is_primary", "status", "effective_from", "effective_to"])
    with tabs[2]:
        st.info("GM has executive organization-wide visibility and administration authority. Technical approval rights remain explicit and separate.")
        if st.button("Open Effective Permissions", key="gm_profile_permissions"):
            _go("Permissions")
    with tabs[3]:
        st.caption("Credential values are never displayed. Use the account/security administration controls for password and policy changes.")
    with tabs[4]:
        sessions = db_where("auth_sessions", "user_id = :uid", (("uid", uidv),)) if table_exists("auth_sessions") else pd.DataFrame()
        _dataframe(sessions, ["created_on", "last_seen_on", "expires_on", "status", "client_fingerprint"])
