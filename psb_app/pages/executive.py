from psb_app.common import (
    actor_get,
    db_all,
    db_count,
    pd,
    st,
    table_exists,
)


def _safe_count(table_name: str, where: str | None = None) -> int:
    if not table_exists(table_name):
        return 0
    try:
        return int(db_count(table_name, where))
    except Exception:
        return 0


def _risk_band(label: str, value: int, thresholds=(0, 1, 5)) -> str:
    low, medium, high = thresholds
    if value >= high:
        return f"🔴 {label}: {value}"
    if value >= medium:
        return f"🟠 {label}: {value}"
    return f"🟢 {label}: {value}"


def _top_risk_records(ncr: pd.DataFrame, jobs: pd.DataFrame, auth: pd.DataFrame, feedback: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if ncr is not None and not ncr.empty:
        sev_col = ncr.get('severity', pd.Series(index=ncr.index, dtype=str)).astype(str)
        open_mask = ~ncr.get('status', pd.Series(index=ncr.index, dtype=str)).astype(str).isin(['Closed', 'Resolved'])
        severe = ncr[open_mask & sev_col.str.lower().isin(['critical', 'high'])]
        rows.extend([
            {'Priority': 'High', 'Domain': 'Quality', 'Item': f"NCR {r.get('ncr_id', '')}", 'Status': r.get('status', ''), 'Owner': r.get('owner_name', r.get('owner', '')), 'Due': r.get('due_date', '')}
            for _, r in severe.head(8).iterrows()
        ])
    if auth is not None and not auth.empty:
        status = auth.get('status', pd.Series(index=auth.index, dtype=str)).astype(str)
        exp = auth.get('expiry_date', pd.Series(index=auth.index, dtype=str)).astype(str)
        mask = status.str.contains('Approved|Valid|Management', case=False, na=False) & exp.ne('')
        rows.extend([
            {'Priority': 'Medium', 'Domain': 'Authorization', 'Item': f"{r.get('name', '')} / {r.get('job_type', '')}", 'Status': r.get('status', ''), 'Owner': r.get('name', ''), 'Due': r.get('expiry_date', '')}
            for _, r in auth[mask].head(8).iterrows()
        ])
    if jobs is not None and not jobs.empty:
        status = jobs.get('status', pd.Series(index=jobs.index, dtype=str)).astype(str)
        risk = jobs.get('risk_level', pd.Series(index=jobs.index, dtype=str)).astype(str).str.lower()
        mask = status.isin(['Open', 'Assigned', 'In Progress']) & risk.isin(['high', 'critical'])
        rows.extend([
            {'Priority': 'High', 'Domain': 'Operations', 'Item': f"{r.get('job_id', '')} / {r.get('job_type', '')}", 'Status': r.get('status', ''), 'Owner': r.get('assigned_user_name', r.get('assigned_user_id', '')), 'Due': r.get('planned_date', '')}
            for _, r in jobs[mask].head(8).iterrows()
        ])
    if feedback is not None and not feedback.empty:
        rating = pd.to_numeric(feedback.get('rating', pd.Series(index=feedback.index, dtype=float)), errors='coerce')
        mask = rating.le(2)
        rows.extend([
            {'Priority': 'Medium', 'Domain': 'Client', 'Item': f"{r.get('feedback_id', '')} / {r.get('client_name', '')}", 'Status': r.get('status', ''), 'Owner': r.get('owner_name', r.get('user_id', '')), 'Due': r.get('response_due_date', r.get('received_on', ''))}
            for _, r in feedback[mask].head(8).iterrows()
        ])
    return pd.DataFrame(rows)


def management_executive_dashboard_page(actor):
    """Executive management workspace composed from authoritative operational records."""
    if actor_get(actor, 'role', '') != 'Management':
        st.error('Executive Dashboard is reserved for the Management role.')
        return

    st.markdown("## Executive Dashboard")
    st.caption('Enterprise decision view: workforce, qualification, authorization, quality, operations, client feedback and performance risk.')

    workforce = _safe_count('users', "status not in ('Inactive','Disabled')")
    active_training = _safe_count('training_records', "status in ('Assigned','In Progress','Pending','Due')")
    open_ncr = _safe_count('competency_ncrs', "status not in ('Closed','Resolved')")
    open_jobs = _safe_count('job_requests', "status in ('Open','Assigned','In Progress')")
    feedback_count = _safe_count('client_feedback')
    expiring_auth = _safe_count('authorization_requests', "status in ('Management Approved','Valid','Approved')")

    metrics([
        ('Active Workforce', workforce),
        ('Training Attention', active_training),
        ('Open Critical/Quality Actions', open_ncr),
        ('Open Jobs', open_jobs),
        ('Authorization Pipeline', expiring_auth),
        ('Client Feedback', feedback_count),
    ])

    st.markdown('### Executive Risk Pulse')
    pulse_cols = st.columns(4)
    pulse = [
        ('Workforce', workforce, (0, 1, 2), 'capacity and headcount'),
        ('Quality', open_ncr, (0, 1, 5), 'open NCR/CAPA'),
        ('Operations', open_jobs, (0, 3, 8), 'open / active jobs'),
        ('Training', active_training, (0, 5, 15), 'records requiring attention'),
    ]
    for col, (label, value, thresholds, help_text) in zip(pulse_cols, pulse):
        with col:
            st.metric(label, value, help=help_text)
            st.caption(_risk_band('Risk signal', value, thresholds))

    ncr = db_all('competency_ncrs') if table_exists('competency_ncrs') else pd.DataFrame()
    jobs = db_all('job_requests') if table_exists('job_requests') else pd.DataFrame()
    auth = db_all('authorization_requests') if table_exists('authorization_requests') else pd.DataFrame()
    feedback = db_all('client_feedback') if table_exists('client_feedback') else pd.DataFrame()
    kpi = db_all('kpi_snapshots') if table_exists('kpi_snapshots') else pd.DataFrame()
    reviews = db_all('qms_management_reviews') if table_exists('qms_management_reviews') else pd.DataFrame()

    st.markdown('### Decision Board')
    risk_df = _top_risk_records(ncr, jobs, auth, feedback)
    if risk_df.empty:
        st.success('No high-priority decision items detected from current source records.')
    else:
        table(risk_df.sort_values(['Priority', 'Domain']))

    left, right = st.columns(2)
    with left:
        st.subheader('Workforce & Qualification Risk')
        if table_exists('competency_matrix'):
            comp = db_all('competency_matrix')
            if not comp.empty and 'status' in comp.columns:
                comp_status = comp['status'].astype(str).value_counts().rename_axis('status').reset_index(name='count')
                table(comp_status)
            else:
                st.info('No competency status distribution is available.')
        else:
            st.info('Competency source is unavailable.')

    with right:
        st.subheader('Operational Coverage')
        if not jobs.empty and 'status' in jobs.columns:
            table(jobs['status'].astype(str).value_counts().rename_axis('status').reset_index(name='count'))
        else:
            st.info('No operational job records are available.')

    st.markdown('### Quality & Client Signal')
    q1, q2 = st.columns(2)
    with q1:
        if not ncr.empty and 'severity' in ncr.columns:
            table(ncr['severity'].astype(str).value_counts().rename_axis('severity').reset_index(name='count'))
        else:
            st.info('No NCR severity distribution is available.')
    with q2:
        if not feedback.empty and 'rating' in feedback.columns:
            ratings = pd.to_numeric(feedback['rating'], errors='coerce').dropna()
            if not ratings.empty:
                st.metric('Average Client Rating', f'{ratings.mean():.1f}/5')
                low = int((ratings <= 2).sum())
                st.caption(_risk_band('Low-rating feedback', low, (0, 1, 3)))
            else:
                st.info('No usable client ratings are available.')
        else:
            st.info('No client feedback rating data is available.')

    st.markdown('### Performance & Governance')
    if not kpi.empty:
        cols = [c for c in ['user_id','overall_score','status','period_start','period_end'] if c in kpi.columns]
        shown = kpi.copy()
        if 'period_end' in shown.columns:
            shown = shown.sort_values('period_end', ascending=False)
        table(shown.head(20)[cols], max_rows=20)
    else:
        st.info('No KPI snapshots are available.')

    if not reviews.empty:
        st.subheader('Management Review Actions')
        open_reviews = reviews.copy()
        if 'status' in open_reviews.columns:
            open_reviews = open_reviews[~open_reviews['status'].astype(str).str.lower().isin(['closed','complete','completed'])]
        cols = [c for c in ['review_id','review_period','status','responsible_owner_name','due_date','actions'] if c in open_reviews.columns]
        if cols:
            table(open_reviews[cols], max_rows=20)
    else:
        st.info('No management review records are available.')
