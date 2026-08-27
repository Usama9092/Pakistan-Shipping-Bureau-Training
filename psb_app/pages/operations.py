from psb_app.common import (
    COMPETENCY_LEVELS,
    DEPARTMENTS,
    JOB_TYPES,
    SCOPES,
    actor_get,
    audit,
    can_action,
    clean,
    date,
    datetime,
    days_until,
    db_all,
    db_insert,
    db_update,
    db_where,
    json,
    kpi_definitions_frame,
    now,
    pd,
    re,
    restrict_user_frame,
    split_list,
    timedelta,
    today,
    uid,
)

def _job_can_manage(actor: dict) -> bool:
    return can_action(actor, 'Job Allocation', 'Assign', 'Organization-wide') or can_action(actor, 'Job Allocation', 'Create', 'Organization-wide') or can_action(actor, 'Job Allocation', 'Edit', 'Organization-wide')

def _job_can_view_self(actor: dict) -> bool:
    return can_action(actor, 'Job Allocation', 'View', 'Own')

def _job_status_class(status: str) -> str:
    s = clean(status).lower()
    if s in {'completed', 'assigned', 'in progress'}:
        return 'status-good'
    if s in {'open', 'reassign', 'draft'}:
        return 'status-warn'
    if s in {'cancelled', 'rejected'}:
        return 'status-bad'
    return 'status-neutral'

def _job_candidate_matrix(job: pd.Series) -> pd.DataFrame:
    users = db_all('users')
    auths = db_all('authorization_requests')
    kpis = db_all('kpi_records')
    restrictions = db_all('authorization_restrictions')
    jobs = db_all('job_requests')
    if users.empty:
        return pd.DataFrame()
    rows = []
    required_dept = clean(job.get('required_department', ''))
    required_scope = clean(job.get('required_scope', ''))
    required_type = clean(job.get('job_type', ''))
    min_level = clean(job.get('minimum_level', 'Level 1'))
    risk = clean(job.get('risk_level', 'Normal'))
    for _, u in users.iterrows():
        reasons = []
        passed = []
        uidv = clean(u.get('user_id'))
        uname = clean(u.get('name'))
        account = clean(u.get('account_status', u.get('status', 'Active')))
        availability = clean(u.get('availability', 'Available'))
        if account not in {'Active', 'active', ''}:
            reasons.append(f'Account {account}')
        else:
            passed.append('active account')
        if availability != 'Available':
            reasons.append(f'Availability: {availability}')
        else:
            passed.append('available')
        dept_text = clean(u.get('primary_department', '')) + ',' + clean(u.get('departments', ''))
        if required_dept and required_dept not in split_list(dept_text):
            reasons.append(f'Not assigned to {required_dept}')
        elif required_dept:
            passed.append(f'department {required_dept}')
        if level_rank(u.get('competency_level', '')) < level_rank(min_level):
            reasons.append(f'Competency below {min_level}')
        else:
            passed.append(f"competency {clean(u.get('competency_level', ''))}")
        user_auths = auths[auths['user_id'].astype(str) == uidv] if not auths.empty and 'user_id' in auths.columns else pd.DataFrame()
        approved = user_auths[user_auths['status'].astype(str).isin(['Management Approved', 'Approved', 'Active']) & (user_auths['scope'].astype(str) == required_scope)] if not user_auths.empty and 'scope' in user_auths.columns else pd.DataFrame()
        if required_type and (not approved.empty) and ('job_type' in approved.columns):
            typed = approved[approved['job_type'].astype(str) == required_type]
            if not typed.empty:
                approved = typed
        if approved.empty:
            reasons.append('No valid authorization for required scope/job type')
            auth_id = ''
        else:
            approved = approved.sort_values('expiry_date', ascending=False).iloc[0]
            auth_id = clean(approved.get('authorization_id', ''))
            if days_until(approved.get('expiry_date', '')) < 0:
                reasons.append('Authorization expired')
                auth_id = ''
            else:
                passed.append(f'authorization {auth_id}')
        active_restr = restrictions[(restrictions['authorization_id'].astype(str) == auth_id) & (restrictions['status'].astype(str) == 'Active')] if auth_id and (not restrictions.empty) else pd.DataFrame()
        if not active_restr.empty:
            reasons.append(f'{len(active_restr)} active authorization restriction(s)')
        user_kpis = kpis[kpis['user_id'].astype(str) == uidv] if not kpis.empty and 'user_id' in kpis.columns else pd.DataFrame()
        kpi_score = float(user_kpis.sort_values('created_on').iloc[-1].get('kpi_score', 80) or 80) if not user_kpis.empty else 80.0
        if risk in {'High', 'Critical'} and kpi_score < 75:
            reasons.append(f'KPI {kpi_score:.0f}% below risk threshold')
        elif risk in {'High', 'Critical'}:
            passed.append(f'KPI {kpi_score:.0f}%')
        open_assigned = jobs[(jobs['assigned_user_id'].astype(str) == uidv) & jobs['status'].astype(str).isin(['Assigned', 'In Progress'])] if not jobs.empty and 'assigned_user_id' in jobs.columns else pd.DataFrame()
        capacity = int(open_assigned.shape[0])
        if capacity >= 3:
            reasons.append(f'Already carrying {capacity} active jobs')
        else:
            passed.append(f'active jobs {capacity}')
        eligible = not reasons
        rows.append({'user_id': uidv, 'name': uname, 'role': clean(u.get('role')), 'department': clean(u.get('primary_department', '')), 'competency_level': clean(u.get('competency_level')), 'authorization_id': auth_id, 'kpi_score': kpi_score, 'active_jobs': capacity, 'eligible': eligible, 'reasons': '; '.join(reasons), 'passed_checks': '; '.join(passed)})
    return pd.DataFrame(rows)

def _job_assignment_snapshot(candidate: pd.Series, job: pd.Series) -> str:
    return json.dumps({'job_id': clean(job.get('job_id')), 'user_id': clean(candidate.get('user_id')), 'authorization_id': clean(candidate.get('authorization_id')), 'competency_level': clean(candidate.get('competency_level')), 'kpi_score': float(candidate.get('kpi_score', 0) or 0), 'active_jobs': int(candidate.get('active_jobs', 0) or 0), 'required_scope': clean(job.get('required_scope')), 'minimum_level': clean(job.get('minimum_level')), 'required_department': clean(job.get('required_department')), 'risk_level': clean(job.get('risk_level'))})

def job_allocation_page(actor):
    st.header('Job Allocation')
    st.caption('Controlled assignment using department, competency, authorization, restrictions, availability, risk and workload. Allocation never bypasses authorization.')
    manage = _job_can_manage(actor)
    self_view = (not manage) and _job_can_view_self(actor)
    if not manage and not self_view:
        st.error('Job allocation access is not permitted for this account.')
        return
    jobs = db_all('job_requests')
    if self_view and not jobs.empty and 'assigned_user_id' in jobs.columns:
        jobs = jobs[jobs['assigned_user_id'].astype(str) == actor_get(actor, 'user_id')].copy()
    if self_view:
        st.info('My Jobs view — only assignments belonging to your account are shown. Operational assignment controls are hidden.')
    assignments = db_all('job_assignments')
    today_s = today()
    metrics([('Open Jobs', int(jobs['status'].astype(str).isin(['Open', 'Reassign']).sum()) if not jobs.empty else 0), ('Assigned', int((jobs['status'].astype(str) == 'Assigned').sum()) if not jobs.empty else 0), ('In Progress', int((jobs['status'].astype(str) == 'In Progress').sum()) if not jobs.empty else 0), ('Due Today', int((jobs['planned_date'].astype(str) == today_s).sum()) if not jobs.empty else 0), ('Overdue', int(((jobs['planned_date'].astype(str) < today_s) & ~jobs['status'].astype(str).isin(['Completed', 'Cancelled'])).sum()) if not jobs.empty else 0)])
    tabs = st.tabs(['My Jobs' if self_view else 'Job Register', 'Create Job', 'Assignment Workbench', 'History'] if manage else ['My Jobs', 'History'])
    with tabs[0]:
        if jobs.empty:
            st.info('No jobs have been created yet.')
        else:
            c1, c2, c3, c4 = st.columns(4)
            status = c1.selectbox('Status', ['All'] + sorted(jobs['status'].astype(str).unique().tolist()), key='job_status_filter')
            deptvals = sorted([x for x in jobs.get('required_department', pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x]) if 'required_department' in jobs.columns else []
            dept = c2.selectbox('Department', ['All'] + deptvals, key='job_dept_filter')
            risk = c3.selectbox('Risk', ['All'] + sorted(jobs['risk_level'].astype(str).unique().tolist()), key='job_risk_filter')
            search = c4.text_input('Search', key='job_search')
            view = jobs.copy()
            if status != 'All':
                view = view[view['status'].astype(str) == status]
            if dept != 'All' and 'required_department' in view.columns:
                view = view[view['required_department'].astype(str) == dept]
            if risk != 'All':
                view = view[view['risk_level'].astype(str) == risk]
            if search:
                view = view[view.apply(lambda r: search.lower() in ' '.join((str(v) for v in r.values)).lower(), axis=1)]
            cols = [c for c in ['job_id', 'job_title', 'job_type', 'required_department', 'required_scope', 'vessel_name', 'planned_date', 'priority', 'risk_level', 'status', 'assigned_user_name'] if c in view.columns]
            table(view.sort_values('planned_date')[[c for c in cols if c in view.columns]])
        if self_view:
            with tabs[1]:
                history = db_all('job_assignments')
                if not history.empty and 'user_id' in history.columns:
                    history = history[history['user_id'].astype(str) == actor_get(actor, 'user_id')].copy()
                table(history, max_rows=100) if not history.empty else st.info('No assignment history is available for your account.')
            return
    with tabs[1]:
        st.subheader('Create Job')
        with st.form('create_job_professional'):
            c1, c2 = st.columns(2)
            title = c1.text_input('Job Title *')
            job_type = c2.selectbox('Job Type', JOB_TYPES)
            c1, c2 = st.columns(2)
            scope = c1.selectbox('Required Scope', SCOPES)
            department = c2.selectbox('Required Department', DEPARTMENTS)
            c1, c2, c3 = st.columns(3)
            vessel = c1.text_input('Vessel / Project')
            imo = c2.text_input('IMO / Reference')
            client = c3.text_input('Client')
            c1, c2, c3, c4 = st.columns(4)
            planned = c1.date_input('Planned Date', value=date.today())
            duration = c2.number_input('Estimated Days', min_value=1, max_value=365, value=1)
            priority = c3.selectbox('Priority', ['Low', 'Normal', 'High', 'Urgent'])
            risk = c4.selectbox('Risk Level', ['Low', 'Medium', 'High', 'Critical'])
            min_level = st.selectbox('Minimum Competency Level', COMPETENCY_LEVELS, index=min(3, len(COMPETENCY_LEVELS) - 1))
            location = st.text_input('Location')
            reference = st.text_input('Client / Project Reference')
            notes = st.text_area('Job Notes / Special Requirements')
            submit = st.form_submit_button('Create Job', type='primary', use_container_width=True)
        if submit:
            if not title.strip():
                st.error('Job title is required.')
            elif planned < date.today() and priority != 'Urgent':
                st.error('Planned date cannot be in the past unless the job is Urgent.')
            else:
                job_id = uid('JOB')
                db_insert('job_requests', {'job_id': job_id, 'job_title': title.strip(), 'job_type': job_type, 'required_scope': scope, 'vessel_name': vessel, 'imo_number': imo, 'location': location, 'planned_date': str(planned), 'priority': priority, 'risk_level': risk, 'minimum_level': min_level, 'required_department': department, 'estimated_days': int(duration), 'client_name': client, 'client_reference': reference, 'notes': notes, 'status': 'Open', 'created_by': actor_get(actor, 'name'), 'assigned_user_id': '', 'assigned_user_name': '', 'assignment_reason': '', 'created_on': now(), 'updated_on': now()})
                audit('Job Created', f'Created {job_id} — {title}', actor=actor, entity_type='job_requests', entity_id=job_id, reason='New operational job')
                st.success(f'Job {job_id} created and is ready for controlled allocation.')
                st.rerun()
    with tabs[2]:
        open_jobs = jobs[jobs['status'].astype(str).isin(['Open', 'Reassign'])] if not jobs.empty else pd.DataFrame()
        if open_jobs.empty:
            st.info('No open jobs require allocation.')
        else:
            labels = open_jobs.apply(lambda r: f"{r.get('job_title', '')} — {r.get('job_id', '')}", axis=1)
            sel = st.selectbox('Job', labels, key='allocation_job_select')
            jid = sel.rsplit(' — ', 1)[-1]
            job = jobs[jobs['job_id'].astype(str) == jid].iloc[0]
            st.subheader(f"{job['job_title']}  ·  {jid}")
            info = st.columns(5)
            info[0].metric('Scope', job.get('required_scope', ''))
            info[1].metric('Level', job.get('minimum_level', ''))
            info[2].metric('Risk', job.get('risk_level', ''))
            info[3].metric('Priority', job.get('priority', ''))
            info[4].metric('Date', job.get('planned_date', ''))
            matrix = _job_candidate_matrix(job)
            if matrix.empty:
                st.warning('No active users are available for evaluation.')
            else:
                eligible = matrix[matrix['eligible'] == True].copy()
                blocked = matrix[matrix['eligible'] == False].copy()
                st.subheader(f'Eligible Candidates ({len(eligible)})')
                if eligible.empty:
                    st.error('No candidate satisfies all allocation controls.')
                else:
                    table(eligible[['name', 'role', 'department', 'competency_level', 'authorization_id', 'kpi_score', 'active_jobs', 'passed_checks']])
                    choice = st.selectbox('Assign To', eligible.apply(lambda r: f"{r['name']} — {r['user_id']}", axis=1), key='assign_candidate')
                    uidv = choice.rsplit(' — ', 1)[-1]
                    cand = eligible[eligible['user_id'].astype(str) == uidv].iloc[0]
                    reason = st.text_area('Assignment Reason', value=f"Eligible: department, competency, valid authorization, no active restrictions, available and workload within limit. Authorization {cand['authorization_id']}.", key='assignment_reason')
                    confirm = st.checkbox('I confirm the candidate meets the job requirements and no active authorization restriction is being bypassed.', key='assignment_confirm')
                    if st.button('Assign Job', type='primary', disabled=not confirm, key='assign_job_btn'):
                        existing = assignments[(assignments['job_id'].astype(str) == jid) & assignments['status'].astype(str).isin(['Assigned', 'Accepted', 'In Progress'])] if not assignments.empty else pd.DataFrame()
                        if not existing.empty:
                            st.error('This job already has an active assignment. Reassign it through the reassignment workflow.')
                        else:
                            snap = _job_assignment_snapshot(cand, job)
                            aid = uid('JA')
                            db_insert('job_assignments', {'assignment_id': aid, 'job_id': jid, 'user_id': uidv, 'user_name': cand['name'], 'assignment_type': 'Primary', 'assigned_by': actor_get(actor, 'name'), 'assigned_on': now(), 'accepted_on': '', 'released_on': '', 'status': 'Assigned', 'reason': reason, 'eligibility_snapshot': snap, 'created_on': now()})
                            db_update('job_requests', 'job_id', jid, {'status': 'Assigned', 'assigned_user_id': uidv, 'assigned_user_name': cand['name'], 'assignment_reason': reason, 'updated_on': now()})
                            audit('Job Assigned', f"{jid} assigned to {cand['name']}", actor=actor, entity_type='job_requests', entity_id=jid, reason=reason, after_value=snap)
                            st.success('Job assigned successfully.')
                            st.rerun()
                with st.expander(f'Excluded Candidates ({len(blocked)})'):
                    if blocked.empty:
                        st.success('No excluded candidates.')
                    else:
                        table(blocked[['name', 'role', 'department', 'competency_level', 'reasons']])
    with tabs[3]:
        if assignments.empty:
            st.info('No assignment history recorded.')
        else:
            table(assignments.sort_values('created_on', ascending=False).head(200))
    st.divider()
    st.subheader('Job Lifecycle')
    active_jobs = jobs[jobs['status'].astype(str).isin(['Assigned', 'In Progress', 'Reassign'])] if not jobs.empty else pd.DataFrame()
    if not active_jobs.empty:
        sel2 = st.selectbox('Job', active_jobs.apply(lambda r: f"{r.get('job_title', '')} — {r.get('job_id', '')}", axis=1), key='job_lifecycle_select')
        jid2 = sel2.rsplit(' — ', 1)[-1]
        job2 = jobs[jobs['job_id'].astype(str) == jid2].iloc[0]
        st.write(f"**Status:** {job2.get('status', '')}  |  **Assigned:** {job2.get('assigned_user_name', '')}")
        c1, c2, c3 = st.columns(3)
        if job2.get('status') == 'Assigned' and c1.button('Start Job', key='start_job_btn'):
            db_update('job_requests', 'job_id', jid2, {'status': 'In Progress', 'updated_on': now()})
            ass = assignments[(assignments['job_id'].astype(str) == jid2) & (assignments['status'].astype(str) == 'Assigned')] if not assignments.empty else pd.DataFrame()
            if not ass.empty:
                db_update('job_assignments', 'assignment_id', ass.iloc[0]['assignment_id'], {'status': 'In Progress', 'accepted_on': now()})
            audit('Job Started', f'{jid2} started', actor=actor, entity_type='job_requests', entity_id=jid2)
            st.rerun()
        if job2.get('status') in {'Assigned', 'In Progress'} and c2.button('Complete Job', key='complete_job_btn'):
            db_update('job_requests', 'job_id', jid2, {'status': 'Completed', 'completed_on': now(), 'updated_on': now()})
            ass = assignments[(assignments['job_id'].astype(str) == jid2) & assignments['status'].astype(str).isin(['Assigned', 'In Progress'])] if not assignments.empty else pd.DataFrame()
            if not ass.empty:
                db_update('job_assignments', 'assignment_id', ass.iloc[0]['assignment_id'], {'status': 'Completed', 'released_on': now()})
                db_update('users', 'user_id', ass.iloc[0]['user_id'], {'availability': 'Available'})
            audit('Job Completed', f'{jid2} completed', actor=actor, entity_type='job_requests', entity_id=jid2)
            st.rerun()
        if c3.button('Cancel / Reassign', key='cancel_reassign_btn'):
            st.session_state['show_job_cancel_form'] = jid2
        if st.session_state.get('show_job_cancel_form') == jid2:
            with st.expander('Cancellation / Reassignment', expanded=True):
                mode = st.radio('Action', ['Reassign', 'Cancel'], horizontal=True, key='job_end_mode')
                reason = st.text_area('Reason *', key='cancel_reason')
                if st.button('Confirm', key='confirm_job_end'):
                    if not reason.strip():
                        st.error('Reason is required.')
                    else:
                        ass = assignments[(assignments['job_id'].astype(str) == jid2) & assignments['status'].astype(str).isin(['Assigned', 'In Progress'])] if not assignments.empty else pd.DataFrame()
                        if not ass.empty:
                            db_update('job_assignments', 'assignment_id', ass.iloc[0]['assignment_id'], {'status': 'Released', 'released_on': now(), 'reason': reason})
                            db_update('users', 'user_id', ass.iloc[0]['user_id'], {'availability': 'Available'})
                        newst = 'Reassign' if mode == 'Reassign' else 'Cancelled'
                        patch = {'status': newst, 'updated_on': now(), 'cancellation_reason': reason}
                        if newst == 'Cancelled':
                            patch['cancelled_on'] = now()
                        db_update('job_requests', 'job_id', jid2, patch)
                        audit('Job Reassigned' if newst == 'Reassign' else 'Job Cancelled', f'{jid2}: {reason}', actor=actor, entity_type='job_requests', entity_id=jid2, reason=reason)
                        st.session_state.pop('show_job_cancel_form', None)
                        st.rerun()

def level_rank(level: str) -> int:
    m = re.search('Level\\s+(\\d+)', clean(level))
    return int(m.group(1)) if m else 0

def eligible_job_candidates(job: pd.Series) -> pd.DataFrame:
    matrix = _job_candidate_matrix(job)
    return matrix[matrix['eligible'] == True].copy() if not matrix.empty else pd.DataFrame()

def _kpi_score_bucket(score: float) -> str:
    if score >= 90:
        return 'Excellent'
    if score >= 80:
        return 'Strong'
    if score >= 70:
        return 'Acceptable'
    if score >= 60:
        return 'Needs Attention'
    return 'Critical'

def _safe_pct(value, default=0.0):
    try:
        return max(0.0, min(100.0, float(value)))
    except Exception:
        return float(default)

def _calculate_performance_snapshot(user_row, period: str):
    """Calculate KPI from authoritative modules; do not ask users to re-enter source metrics."""
    uidv = str(user_row.get('user_id', ''))
    name = str(user_row.get('name', ''))
    trainings = db_where('training_records', 'user_id = :user_id', (('user_id', uidv),))
    reqs = db_all('training_requirements')
    comp = db_where('competency_matrix', 'user_id = :user_id', (('user_id', uidv),))
    auth = db_where('authorization_requests', 'user_id = :user_id', (('user_id', uidv),))
    jobs = db_where('job_assignments', 'user_id = :user_id', (('user_id', uidv),))
    feedback = db_where('client_feedback', 'subject_user_id = :user_id', (('user_id', uidv),))
    ncr = db_where('competency_ncrs', 'user_id = :user_id', (('user_id', uidv),))
    tech = db_where('technical_reviews', 'user_id = :user_id', (('user_id', uidv),))
    audits = db_where('qms_audits', 'lead_auditor_id = :user_id', (('user_id', uidv),))
    training_score = 100.0
    if not trainings.empty:
        s = trainings.get('status', pd.Series(dtype=str)).astype(str).str.lower()
        done = s.isin(['completed', 'passed', 'complete']).sum()
        training_score = _safe_pct(done / max(len(s), 1) * 100)
    elif not reqs.empty:
        training_score = 0.0
    competency_score = 0.0
    if not comp.empty:
        c = comp.iloc[-1]
        status = str(c.get('status', '')).lower()
        if status in {'authorized', 'competent', 'ready', 'approved'}:
            competency_score = 100.0
        else:
            try:
                competency_score = _safe_pct(float(c.get('current_level', 0) or 0) / max(float(c.get('required_level', 1) or 1), 1) * 100)
            except Exception:
                competency_score = 50.0
    authorization_score = 0.0
    if not auth.empty:
        approved = auth.get('status', pd.Series(dtype=str)).astype(str).str.lower().isin(['approved', 'authorized', 'active'])
        authorization_score = 100.0 if bool(approved.any()) else 0.0
        if authorization_score and 'expiry_date' in auth.columns:
            try:
                expiry = pd.to_datetime(auth['expiry_date'], errors='coerce', utc=True).max()
                if pd.notna(expiry):
                    days = (expiry - pd.Timestamp.utcnow()).days
                    if days < 0:
                        authorization_score = 0.0
                    elif days < 30:
                        authorization_score = 70.0
                    elif days < 90:
                        authorization_score = 85.0
            except Exception:
                pass
    technical_review_score = 100.0 if tech.empty else 0.0
    if not tech.empty:
        decisions = tech.get('decision', tech.get('status', pd.Series(dtype=str))).astype(str).str.lower()
        technical_review_score = 100.0 * float(decisions.isin(['approved', 'pass', 'passed', 'satisfactory', 'accepted', 'closed']).mean())
    quality_score = 100.0 if audits.empty else 0.0
    if not audits.empty:
        st = audits.get('status', pd.Series(dtype=str)).astype(str).str.lower()
        quality_score = 100.0 * float(st.isin(['closed', 'completed', 'satisfactory', 'passed']).mean())
    delivery_score = 0.0
    if not jobs.empty:
        js = jobs.get('status', pd.Series(dtype=str)).astype(str).str.lower()
        completed = js.isin(['completed', 'closed', 'released']).sum()
        delivery_score = _safe_pct(completed / max(len(js), 1) * 100)
    client_feedback_score = 0.0
    if not feedback.empty and 'rating' in feedback.columns:
        vals = pd.to_numeric(feedback['rating'], errors='coerce').dropna()
        if not vals.empty:
            avg = float(vals.mean())
            client_feedback_score = _safe_pct(avg / 5 * 100 if avg <= 5 else avg)
    else:
        client_feedback_score = 0.0
    ncr_score = 100.0
    if not ncr.empty:
        st = ncr.get('status', pd.Series(dtype=str)).astype(str).str.lower()
        open_count = int((~st.isin(['closed', 'resolved', 'verified', 'cancelled'])).sum())
        crit = ncr.get('severity', pd.Series(dtype=str)).astype(str).str.lower().isin(['critical', 'high']).sum()
        ncr_score = _safe_pct(100 - open_count * 10 - int(crit) * 15)
    utilization_score = 0.0
    if not jobs.empty:
        js = jobs.get('status', pd.Series(dtype=str)).astype(str).str.lower()
        meaningful = js.isin(['completed', 'in progress', 'assigned', 'accepted']).sum()
        utilization_score = _safe_pct(meaningful / max(len(js), 1) * 100)
    weights = {'training': 0.15, 'competency': 0.2, 'authorization': 0.15, 'technical': 0.1, 'quality': 0.1, 'delivery': 0.1, 'feedback': 0.1, 'ncr': 0.05, 'utilization': 0.05}
    overall = round(training_score * weights['training'] + competency_score * weights['competency'] + authorization_score * weights['authorization'] + technical_review_score * weights['technical'] + quality_score * weights['quality'] + delivery_score * weights['delivery'] + client_feedback_score * weights['feedback'] + ncr_score * weights['ncr'] + utilization_score * weights['utilization'], 2)
    status = _kpi_score_bucket(overall)
    sources = {'training_records': len(trainings), 'competency_records': len(comp), 'authorization_records': len(auth), 'job_assignments': len(jobs), 'client_feedback': len(feedback), 'ncr_records': len(ncr), 'technical_reviews': len(tech), 'qms_audits': len(audits)}
    return {'snapshot_id': uid('KPI'), 'user_id': uidv, 'name': name, 'period': period, 'training_score': round(training_score, 2), 'competency_score': round(competency_score, 2), 'authorization_score': round(authorization_score, 2), 'technical_review_score': round(technical_review_score, 2), 'quality_score': round(quality_score, 2), 'delivery_score': round(delivery_score, 2), 'client_feedback_score': round(client_feedback_score, 2), 'ncr_score': round(ncr_score, 2), 'utilization_score': round(utilization_score, 2), 'overall_score': overall, 'status': status, 'calculation_version': 'v1-authoritative-derived', 'source_counts': json.dumps(sources), 'calculated_on': now(), 'calculated_by': 'system', 'notes': 'Derived from authoritative operational records.'}

def kpi_definitions_panel(actor):
    defs=kpi_definitions_frame()
    if defs.empty:
        st.info("No governed KPI definitions are configured yet.")
        return
    st.subheader("Governed KPI Definitions")
    st.dataframe(defs[[c for c in ["name","formula","weight","target","period_type","version","effective_from","active"] if c in defs.columns]], use_container_width=True, hide_index=True)
    if can_action(actor,"Performance & KPI","Manage","Organization-wide"):
        st.caption("KPI definitions are versioned governance records; change history is preserved by the audit trail.")

def kpi_page(actor):
    """Read-only performance analytics from authoritative modules. No manual KPI re-entry."""
    st.header('Performance & KPI')
    st.caption('KPI is calculated from Training, Competency, Authorization, Technical Reviews, QMS, Jobs, Client Feedback and NCR/CAPA. It is not a second data-entry system.')
    with st.expander("KPI Definitions & Targets", expanded=False):
        kpi_definitions_panel(actor)
    users = db_all('users')
    role = actor_get(actor, 'role')
    elevated = can_action(actor, 'Performance & KPI', 'View', 'Organization-wide')
    if users.empty:
        st.info('No users available.')
        return
    user_df = users.copy()
    if not elevated:
        user_df = user_df[user_df['user_id'].astype(str) == actor_get(actor, 'user_id')]
    p1, p2, p3 = st.columns([2, 2, 2])
    with p1:
        period = st.text_input('Period', datetime.now().strftime('%Y-%m'))
    with p2:
        dept = st.selectbox('Department', ['All'] + sorted(user_df.get('primary_department', pd.Series(dtype=str)).fillna('').astype(str).replace('', 'Unassigned').unique().tolist()))
    with p3:
        status_filter = st.selectbox('Performance', ['All', 'Excellent', 'Strong', 'Acceptable', 'Needs Attention', 'Critical'])
    scoped = user_df if dept == 'All' else user_df[user_df.get('primary_department', pd.Series(dtype=str)).astype(str).fillna('').eq(dept)]
    snapshots = []
    for _, u in scoped.iterrows():
        snapshots.append(_calculate_performance_snapshot(u, period))
    snap = pd.DataFrame(snapshots)
    if snap.empty:
        st.info('No performance records available for the selected filters.')
        return
    if status_filter != 'All':
        snap = snap[snap['status'] == status_filter]
    avg = float(snap['overall_score'].mean())
    crit = int((snap['status'] == 'Critical').sum())
    attention = int(snap['status'].isin(['Needs Attention', 'Critical']).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('People Assessed', len(snap))
    c2.metric('Average KPI', f'{avg:.1f}%')
    c3.metric('Needs Attention', attention)
    c4.metric('Critical', crit)
    st.subheader('Performance Overview')
    show_cols = ['name', 'period', 'overall_score', 'status', 'training_score', 'competency_score', 'authorization_score', 'quality_score', 'delivery_score', 'client_feedback_score', 'ncr_score']
    table(snap[show_cols], max_rows=100)
    if not snap.empty:
        st.subheader('Performance Distribution')
        counts = snap['status'].value_counts().rename_axis('status').to_frame('people')
        st.bar_chart(counts)
        selected_name = st.selectbox('View employee performance', snap['name'].astype(str).tolist())
        row = snap[snap['name'].astype(str) == selected_name].iloc[0]
        st.subheader(f'{selected_name} — Evidence-Based Scorecard')
        metric_cols = [('Training', 'training_score'), ('Competency', 'competency_score'), ('Authorization', 'authorization_score'), ('Technical Review', 'technical_review_score'), ('QMS', 'quality_score'), ('Delivery', 'delivery_score'), ('Client Feedback', 'client_feedback_score'), ('NCR/CAPA', 'ncr_score'), ('Utilization', 'utilization_score')]
        cols = st.columns(3)
        for i, (label, col) in enumerate(metric_cols):
            cols[i % 3].metric(label, f'{float(row[col]):.0f}%')
        st.info('This scorecard is derived from live source records. Changing a Training, Competency, Authorization, Job, Feedback or NCR record changes the KPI view automatically.')
    if elevated and (not snap.empty):
        with st.expander('Governance Snapshot', expanded=False):
            st.caption('Save the calculated scorecard as a point-in-time governance snapshot. Source metrics cannot be manually edited here.')
            chosen = st.selectbox('Employee', snap['name'].astype(str).tolist(), key='kpi_snapshot_employee')
            if st.button('Save Calculated Snapshot', key='save_calculated_kpi'):
                row = snap[snap['name'].astype(str) == chosen].iloc[0].to_dict()
                payload = {k: row.get(k) for k in ['snapshot_id', 'user_id', 'name', 'period', 'training_score', 'competency_score', 'authorization_score', 'technical_review_score', 'quality_score', 'delivery_score', 'client_feedback_score', 'ncr_score', 'utilization_score', 'overall_score', 'status', 'calculation_version', 'source_counts', 'calculated_on']}
                payload['calculated_by'] = actor_get(actor, 'name')
                payload['notes'] = 'Governance snapshot of system-calculated KPI; source data remains authoritative.'
                db_insert('kpi_snapshots', payload)
                audit_event(actor, 'KPI Snapshot', 'Created', payload['snapshot_id'], payload['notes'])
                st.success('Calculated KPI snapshot saved.')
                st.rerun()

def _client_feedback_can_manage(actor: dict) -> bool:
    return can_action(actor, 'Client Feedback', 'Create', 'Organization-wide') or can_action(actor, 'Client Feedback', 'Edit', 'Department') or can_action(actor, 'Client Feedback', 'Manage', 'Organization-wide')

def _client_feedback_can_view_self(actor: dict) -> bool:
    return can_action(actor, 'Client Feedback', 'View', 'Own')

def _client_feedback_status_open(status: str) -> bool:
    return clean(status) not in {'Closed', 'Dismissed'}

def client_feedback_page(actor):
    """Closed-loop client feedback workflow.

    Feedback remains the authoritative client-feedback record. Performance/KPI,
    Annual Review and NCR/CAPA consume the feedback rather than duplicating it.
    """
    st.header('Client Feedback')
    st.caption('Closed-loop client, shipowner and shipyard feedback linked to jobs, people, performance, NCR/CAPA and annual review.')
    manage = _client_feedback_can_manage(actor)
    self_view = (not manage) and _client_feedback_can_view_self(actor)
    if not manage and not self_view:
        st.info('Client Feedback access is not permitted for this account.')
        return
    feedback = restrict_user_frame(db_all('client_feedback'), actor)
    if self_view:
        feedback = feedback[feedback.get('user_id', pd.Series(dtype=str)).astype(str).eq(actor_get(actor, 'user_id'))] if not feedback.empty else feedback
        st.info('My Feedback view — only feedback linked to your account is shown. Create/edit controls are hidden.')
    if feedback.empty:
        feedback = pd.DataFrame(columns=['feedback_id', 'user_id', 'name', 'client_name', 'project_or_vessel', 'job_id', 'rating', 'feedback_type', 'comments', 'status', 'received_on'])
    for col in ['feedback_channel', 'contact_person', 'source_reference', 'service_area', 'scope', 'severity', 'sentiment', 'confidentiality', 'response_due', 'owner_id', 'owner_name', 'response_text', 'action_required', 'linked_ncr_id', 'linked_job_id', 'submitted_by', 'submitted_by_name', 'created_on', 'updated_on', 'resolved_on', 'resolution_notes']:
        if col not in feedback.columns:
            feedback[col] = ''
    feedback['rating_num'] = pd.to_numeric(feedback.get('rating', 0), errors='coerce').fillna(0)
    feedback['status'] = feedback['status'].replace('', 'New').fillna('New')
    open_fb = feedback[feedback['status'].apply(_client_feedback_status_open)]
    action_fb = feedback[feedback['action_required'].astype(str).str.casefold().eq('yes')]
    complaint_fb = feedback[feedback['feedback_type'].astype(str).isin(['Complaint', 'Technical Concern'])]
    avg_rating = round(float(feedback['rating_num'].mean()), 2) if not feedback.empty else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Total Feedback', len(feedback))
    c2.metric('Open / Under Review', len(open_fb))
    c3.metric('Complaints / Concerns', len(complaint_fb))
    c4.metric('Actions Required', len(action_fb))
    c5.metric('Average Rating', f'{avg_rating:.1f}/5')
    tabs = st.tabs(['Feedback Register', 'New Feedback', 'Review & Response', 'Insights'])
    with tabs[0]:
        a, b, c, d, e = st.columns(5)
        search = a.text_input('Search', key='fb_search')
        status = b.selectbox('Status', ['All', 'New', 'Under Review', 'Responded', 'Action Required', 'Closed', 'Dismissed'], key='fb_status')
        ftype = c.selectbox('Type', ['All', 'Positive', 'Neutral', 'Complaint', 'Technical Concern'], key='fb_type')
        dept = d.selectbox('Service Area', ['All', 'Survey NSC', 'Survey Inservice', 'Plan Appraisal', 'QMS', 'Rule Development', 'Training', 'Administration'], key='fb_dept')
        rating = e.selectbox('Rating', ['All', '1', '2', '3', '4', '5'], key='fb_rating')
        view = feedback.copy()
        if search:
            blob = view.fillna('').astype(str).agg(' | '.join, axis=1).str.casefold()
            view = view[blob.str.contains(search.casefold(), regex=False)]
        if status != 'All':
            view = view[view['status'].astype(str) == status]
        if ftype != 'All':
            view = view[view['feedback_type'].astype(str) == ftype]
        if dept != 'All':
            view = view[view['service_area'].astype(str) == dept]
        if rating != 'All':
            view = view[view['rating_num'] == int(rating)]
        cols = [c for c in ['feedback_id', 'name', 'client_name', 'service_area', 'feedback_type', 'rating', 'status', 'action_required', 'linked_ncr_id', 'received_on'] if c in view.columns]
        table(view[cols].sort_values('received_on', ascending=False) if not view.empty else view, max_rows=250)
        if not view.empty:
            st.download_button('Export Filtered Feedback', view.to_csv(index=False).encode('utf-8'), 'psb_client_feedback.csv', 'text/csv')
        st.info('Feedback owns the client-feedback record. KPI, Annual Review and Revalidation consume this data; they do not recreate feedback entries.')
    if self_view:
        with tabs[3]:
            st.subheader('My Feedback Insights')
            st.metric('Total Feedback', len(feedback))
            st.metric('Average Rating', f'{avg_rating:.1f}/5')
            st.caption('This self-service view is read-only. Organization-wide feedback response and closure actions require an authorized Operations/Quality role.')
        return
    with tabs[1]:
        users = db_all('users')
        jobs = db_all('job_requests')
        user_labels = _user_label_series(users) if not users.empty else []
        job_labels = []
        if not jobs.empty and 'job_id' in jobs.columns:
            job_labels = [f"{r.get('job_id', '')} — {r.get('job_title', '')}" for _, r in jobs.iterrows()]
        with st.form('new_client_feedback'):
            a, b = st.columns(2)
            person_label = a.selectbox('PSB Person / Responsible Subject', [''] + user_labels)
            job_label = b.selectbox('Related Job (optional)', [''] + job_labels)
            c, d = st.columns(2)
            client = c.text_input('Client / Shipowner / Shipyard *')
            contact = d.text_input('Client Contact (optional)')
            e, f = st.columns(2)
            project = e.text_input('Project / Vessel')
            source_ref = f.text_input('Client Reference / Source')
            g, h = st.columns(2)
            channel = g.selectbox('Feedback Channel', ['Email', 'Meeting', 'Survey Form', 'Letter', 'Phone', 'Portal', 'Other'])
            service_area = h.selectbox('Service Area', ['Survey NSC', 'Survey Inservice', 'Plan Appraisal', 'QMS', 'Rule Development', 'Training', 'Administration'])
            i, j = st.columns(2)
            scope = i.selectbox('Scope', ['Not Scope-Specific'] + SCOPES)
            ftype = j.selectbox('Feedback Type', ['Positive', 'Neutral', 'Complaint', 'Technical Concern'])
            k, l, m = st.columns(3)
            rating = k.slider('Rating', 1, 5, 4)
            severity = l.selectbox('Severity', ['Low', 'Medium', 'High', 'Critical'])
            sentiment = m.selectbox('Sentiment', ['Positive', 'Neutral', 'Negative'])
            comments = st.text_area('Feedback / Client Comment *', height=130)
            confidential = st.checkbox('Confidential feedback', value=False)
            owner_label = st.selectbox('Response / Action Owner', [''] + user_labels)
            due = st.date_input('Response / Action Due Date', value=date.today() + timedelta(days=7))
            action_required = st.selectbox('Action Required?', ['No', 'Yes'])
            reason = st.text_area('Reason / context *')
            submit = st.form_submit_button('Record Feedback', type='primary')
        if submit:
            _, uidv = _parse_user_label(person_label)
            _, owner_id = _parse_user_label(owner_label)
            owner_name = owner_label.split(' — ')[0] if owner_label else ''
            job_id = job_label.split(' — ')[0] if job_label else ''
            if not client.strip() or not comments.strip() or (not reason.strip()):
                st.error('Client, feedback comments and reason/context are mandatory.')
            else:
                status = 'Action Required' if action_required == 'Yes' else 'Under Review' if ftype in ['Complaint', 'Technical Concern'] else 'New'
                fid = uid('FB')
                row = {'feedback_id': fid, 'user_id': uidv or '', 'name': person_label.split(' — ')[0] if person_label else '', 'client_name': client.strip(), 'contact_person': contact.strip(), 'project_or_vessel': project.strip(), 'job_id': job_id, 'linked_job_id': job_id, 'rating': rating, 'feedback_type': ftype, 'comments': comments.strip(), 'impact_on_kpi': 'Requires Review' if ftype in ['Complaint', 'Technical Concern'] else 'Positive' if rating >= 4 else 'No Impact', 'feedback_channel': channel, 'source_reference': source_ref.strip(), 'service_area': service_area, 'scope': '' if scope == 'Not Scope-Specific' else scope, 'severity': severity, 'sentiment': sentiment, 'confidentiality': 'Confidential' if confidential else 'Internal', 'response_due': str(due), 'owner_id': owner_id or '', 'owner_name': owner_name, 'response_text': '', 'action_required': action_required, 'linked_ncr_id': '', 'submitted_by': actor_get(actor, 'user_id'), 'submitted_by_name': actor_get(actor, 'name'), 'status': status, 'received_on': today(), 'created_on': now(), 'updated_on': now(), 'resolved_on': '', 'resolution_notes': ''}
                db_insert('client_feedback', row)
                audit('Client Feedback Recorded', f'{fid} · {ftype} · {client.strip()}', actor=actor, entity_type='client_feedback', entity_id=fid, reason=reason.strip(), after_value=json.dumps({k: row.get(k) for k in ['feedback_type', 'rating', 'severity', 'status', 'action_required', 'linked_job_id']}, default=str))
                st.success(f'Feedback {fid} recorded.')
                st.rerun()
    with tabs[2]:
        candidates = feedback[feedback['status'].apply(_client_feedback_status_open)]
        if candidates.empty:
            st.success('No open feedback items require review.')
        else:
            labels = (candidates['feedback_id'].astype(str) + ' — ' + candidates['client_name'].astype(str) + ' — ' + candidates['feedback_type'].astype(str)).tolist()
            selected = st.selectbox('Feedback item', labels, key='fb_review_select')
            fid = selected.split(' — ')[0]
            row = candidates[candidates['feedback_id'].astype(str) == fid].iloc[0]
            st.markdown(f"### {fid} · {row.get('feedback_type', 'Feedback')}")
            st.write(f"**Client:** {row.get('client_name', '')}  ·  **Person:** {row.get('name', '')}  ·  **Rating:** {row.get('rating', '')}/5")
            st.write(f"**Feedback:** {row.get('comments', '')}")
            linked_ncr = clean(row.get('linked_ncr_id', ''))
            with st.form('fb_review_form'):
                a, b = st.columns(2)
                new_status = a.selectbox('Status', ['New', 'Under Review', 'Responded', 'Action Required', 'Closed', 'Dismissed'], index=['New', 'Under Review', 'Responded', 'Action Required', 'Closed', 'Dismissed'].index(str(row.get('status', 'New'))) if str(row.get('status', 'New')) in ['New', 'Under Review', 'Responded', 'Action Required', 'Closed', 'Dismissed'] else 0)
                action = b.selectbox('Action Required', ['No', 'Yes'], index=1 if str(row.get('action_required', 'No')) == 'Yes' else 0)
                response = st.text_area('Response / Management Action', str(row.get('response_text', '')), height=120)
                resolution = st.text_area('Resolution Notes', str(row.get('resolution_notes', '')), height=90)
                create_ncr = st.checkbox('Create / link NCR-CAPA for this feedback', value=bool(linked_ncr or str(row.get('feedback_type')) in ['Complaint', 'Technical Concern']))
                reason = st.text_area('Reason for review/update *')
                save = st.form_submit_button('Save Review', type='primary')
            if save:
                if not reason.strip():
                    st.error('Reason is required.')
                else:
                    before = json.dumps({k: row.get(k, '') for k in ['status', 'action_required', 'response_text', 'resolution_notes', 'linked_ncr_id']}, default=str)
                    ncr_id = linked_ncr
                    if create_ncr and (not ncr_id) and (str(row.get('feedback_type')) in ['Complaint', 'Technical Concern']):
                        ncrs = db_all('competency_ncrs')
                        duplicate = False
                        if not ncrs.empty:
                            duplicate = any((_ncr_is_open(str(r.get('status', ''))) and str(r.get('source_record_id', '')) == fid for _, r in ncrs.iterrows()))
                        if duplicate:
                            match = ncrs[ncrs['source_record_id'].astype(str) == fid]
                            if not match.empty:
                                ncr_id = str(match.iloc[0]['ncr_id'])
                        else:
                            ncr_id = uid('NCR')
                            db_insert('competency_ncrs', {'ncr_id': ncr_id, 'user_id': clean(row.get('user_id', '')), 'name': clean(row.get('name', '')), 'source': 'Client Feedback', 'source_record_id': fid, 'scope': clean(row.get('scope', '')), 'category': 'Client Feedback', 'ncr_type': clean(row.get('feedback_type', '')), 'description': clean(row.get('comments', '')), 'severity': clean(row.get('severity', 'Medium')) or 'Medium', 'likelihood': 3, 'risk_score': 6, 'priority': 'Medium', 'status': 'Open', 'corrective_action': 'Investigate and respond to client feedback', 'owner_id': clean(row.get('owner_id', '')), 'owner_name': clean(row.get('owner_name', '')), 'impact_on_authorization': 'Monitor / Review if recurrent', 'raised_by': actor_get(actor, 'name'), 'raised_on': now(), 'closed_on': '', 'closed_by': '', 'verification_status': 'Pending', 'effectiveness_check': 'Pending', 'updated_on': now()})
                            audit('NCR Raised from Client Feedback', f'{fid} → {ncr_id}', actor=actor, entity_type='NCR', entity_id=ncr_id, reason=reason.strip(), after_value=fid)
                    new_status = 'Closed' if new_status == 'Closed' and resolution.strip() else new_status
                    db_update('client_feedback', 'feedback_id', fid, {'status': new_status, 'action_required': action, 'response_text': response.strip(), 'resolution_notes': resolution.strip(), 'linked_ncr_id': ncr_id, 'resolved_on': today() if new_status == 'Closed' else '', 'updated_on': now()})
                    audit('Client Feedback Reviewed', fid, actor=actor, entity_type='client_feedback', entity_id=fid, reason=reason.strip(), before_value=before, after_value=json.dumps({'status': new_status, 'action_required': action, 'linked_ncr_id': ncr_id}, default=str))
                    st.success('Feedback review saved.')
                    st.rerun()
    with tabs[3]:
        a, b, c = st.columns(3)
        period = a.selectbox('Period', ['All', 'Last 30 Days', 'Last 90 Days', 'This Year'], key='fb_period')
        subject = feedback.copy()
        if period != 'All':
            days = 30 if period == 'Last 30 Days' else 90 if period == 'Last 90 Days' else 365
            cutoff = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
            subject = subject[subject['received_on'].astype(str) >= cutoff]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Average Rating', f"{(float(subject['rating_num'].mean()) if not subject.empty else 0):.2f}/5")
        c2.metric('Positive %', f"{(float((subject['sentiment'].astype(str) == 'Positive').mean()) * 100 if not subject.empty else 0):.0f}%")
        c3.metric('Complaints', int(subject['feedback_type'].isin(['Complaint', 'Technical Concern']).sum()) if not subject.empty else 0)
        c4.metric('Resolved', int(subject['status'].astype(str).eq('Closed').sum()) if not subject.empty else 0)
        if not subject.empty:
            by_type = subject.groupby('feedback_type', dropna=False).size().reset_index(name='count')
            st.subheader('Feedback Mix')
            st.bar_chart(by_type.set_index('feedback_type'))
            by_area = subject.groupby('service_area', dropna=False)['rating_num'].mean().sort_values(ascending=False).round(2)
            st.subheader('Average Rating by Service Area')
            st.bar_chart(by_area)
        st.caption('Insights are derived from feedback records. KPI and annual-review workflows consume these outcomes rather than requiring manual duplicate entries.')
