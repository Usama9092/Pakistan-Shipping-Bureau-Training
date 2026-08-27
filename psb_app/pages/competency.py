from psb_app.common import (
    COMPETENCY_LEVELS,
    JOB_TYPES,
    SCOPES,
    actor_get,
    allowed_user_ids,
    audit,
    can_action,
    date,
    datetime,
    db_all,
    db_insert,
    db_update,
    db_where,
    get_matrix_for_scope,
    json,
    now,
    pd,
    re,
    readiness,
    restrict_user_frame,
    st,
    table_exists,
    timedelta,
    today,
    uid,
)

def competency_page(actor):
    """Authoritative competency assessment and readiness workflow.

    Competency owns the readiness decision. Training/CPD/Development/Witness remain
    authoritative in their own modules and are read here as evidence only.
    """
    st.header('Competency')
    st.caption('Assess capability, review evidence, identify gaps and make a controlled competency decision. Training, CPD, development and witness records remain authoritative in their own modules.')
    # Schema is owned by database migrations; no page-level DDL.
    role = actor_get(actor, 'role')
    privileged = can_action(actor, 'Competency', 'Review', 'Department') or can_action(actor, 'Competency', 'Review', 'Organization-wide') or can_action(actor, 'Competency', 'Edit', 'Assigned')
    users = db_all('users')
    comp = restrict_user_frame(db_all('competency_matrix'), actor)
    if comp.empty:
        comp = pd.DataFrame(columns=['competency_id', 'user_id', 'name', 'role', 'trainee_path', 'area', 'competency_level', 'scope', 'job_type', 'required_level_for_auth', 'status', 'expiry_date', 'evidence', 'created_on', 'updated_on'])
    if not privileged:
        comp = comp[comp.get('user_id', pd.Series(dtype=str)).astype(str) == str(actor_get(actor, 'user_id'))].copy()
    total = len(comp)
    ready_count = 0
    pending_count = 0
    authorized_count = 0
    due_90 = 0
    today_value = date.today()
    for _, r in comp.iterrows():
        ok, _ = readiness(str(r.get('user_id', '')), str(r.get('scope', r.get('area', ''))))
        if ok:
            ready_count += 1
        else:
            pending_count += 1
        if str(r.get('status', '')) == 'Authorized':
            authorized_count += 1
        try:
            exp = datetime.strptime(str(r.get('expiry_date', ''))[:10], '%Y-%m-%d').date()
            if today_value <= exp <= today_value + timedelta(days=90):
                due_90 += 1
        except Exception:
            pass
    metrics([('Competency Records', total), ('Evidence Ready', ready_count), ('Evidence Gaps', pending_count), ('Authorized', authorized_count), ('Expiring ≤90 Days', due_90)])
    tabs = st.tabs(['Competency Register', 'Assess / Review', 'Evidence & Gaps', 'History'])
    with tabs[0]:
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        search = f1.text_input('Search', placeholder='Employee, competency ID or scope', key='competency_search')
        status_filter = f2.selectbox('Status', ['All', 'Pending', 'Under Review', 'Ready', 'Authorized', 'Restricted', 'Expired'], key='competency_status_filter')
        level_filter = f3.selectbox('Level', ['All'] + COMPETENCY_LEVELS, key='competency_level_filter')
        scope_filter = f4.selectbox('Scope', ['All'] + SCOPES, key='competency_scope_filter')
        shown = comp.copy()
        if search.strip() and (not shown.empty):
            q = search.strip().lower()
            mask = pd.Series(False, index=shown.index)
            for col in ['name', 'competency_id', 'scope', 'area']:
                if col in shown.columns:
                    mask = mask | shown[col].astype(str).str.lower().str.contains(re.escape(q), na=False)
            shown = shown[mask]
        if status_filter != 'All' and (not shown.empty):
            shown = shown[shown['status'].astype(str) == status_filter]
        if level_filter != 'All' and (not shown.empty):
            shown = shown[shown['competency_level'].astype(str) == level_filter]
        if scope_filter != 'All' and (not shown.empty):
            shown = shown[shown['scope'].astype(str) == scope_filter]
        rows = []
        for _, r in shown.iterrows():
            ok, gaps = readiness(str(r.get('user_id', '')), str(r.get('scope', r.get('area', ''))))
            rows.append({'Competency ID': r.get('competency_id', ''), 'Employee': r.get('name', ''), 'Role': r.get('role', ''), 'Scope': r.get('scope', r.get('area', '')), 'Level': r.get('competency_level', ''), 'Status': r.get('status', 'Pending'), 'Evidence': 'Ready' if ok else f'{len(gaps)} gap(s)', 'Expiry': r.get('expiry_date', '')})
        if rows:
            table(pd.DataFrame(rows), max_rows=250)
        else:
            st.info('No competency records match the current filters.')
        if privileged:
            st.divider()
            st.subheader('Create Competency Record')
            eligible_roles = ['Trainee', 'On Probation', 'Surveyor', 'Plan Appraiser', 'QMS Auditor', 'Industrial Surveyor', 'Rule Development Rep']
            candidates = users[users['role'].isin(eligible_roles)].copy() if not users.empty else pd.DataFrame()
            with st.form('competency_create_v2', clear_on_submit=True):
                person = st.selectbox('Employee', [f'{n} — {u}' for n, u in zip(candidates.get('name', []), candidates.get('user_id', []))] if not candidates.empty else [''])
                scope = st.selectbox('Competency Scope', SCOPES)
                matrix = get_matrix_for_scope(scope)
                job_type = matrix['job_type'] if matrix is not None else st.selectbox('Job Type', JOB_TYPES)
                target_level = matrix['required_level_for_auth'] if matrix is not None else st.selectbox('Required Level', COMPETENCY_LEVELS, index=3)
                expiry = st.date_input('Target / Validity Expiry', today_value + timedelta(days=365 * 3))
                rationale = st.text_area('Purpose / Initial Rationale', placeholder='Why this competency record is being opened.')
                create = st.form_submit_button('Create Competency Record', type='primary', use_container_width=True)
            if create and person and (' — ' in person):
                name, uidv = person.split(' — ', 1)
                u = users[users['user_id'] == uidv].iloc[0]
                existing = db_where('competency_matrix', 'user_id = :uid and scope = :scope', (('uid', uidv), ('scope', scope)))
                if not existing.empty:
                    st.warning('A competency record already exists for this employee and scope. Open it from the register instead of creating a duplicate.')
                else:
                    cid = uid('COMP')
                    db_insert('competency_matrix', {'competency_id': cid, 'user_id': uidv, 'name': name, 'role': u['role'], 'trainee_path': u.get('trainee_path', ''), 'area': scope, 'competency_level': 'Level 0 - Trainee', 'scope': scope, 'job_type': job_type, 'required_training_ids': '', 'required_witness_count': int(matrix.get('required_witness_count', 0) if matrix is not None else 2), 'required_supervised_count': int(matrix.get('required_supervised_count', 0) if matrix is not None else 1), 'required_joint_plan_count': int(matrix.get('required_joint_plan_count', 0) if matrix is not None else 0), 'required_independent_plan_count': int(matrix.get('required_independent_plan_count', 0) if matrix is not None else 0), 'required_level_for_auth': target_level, 'status': 'Pending', 'expiry_date': str(expiry), 'evidence': json.dumps({'initial_rationale': rationale}, default=str), 'created_on': now(), 'updated_on': now()})
                    audit('Competency Record Created', f'Competency {cid} created for {name} / {scope}', actor=actor, entity_type='competency_matrix', entity_id=cid, reason='New competency scope')
                    st.success(f'Competency {cid} created.')
    all_comp = db_all('competency_matrix')
    if not privileged:
        all_comp = all_comp[all_comp['user_id'].astype(str) == str(actor_get(actor, 'user_id'))] if not all_comp.empty else all_comp
    if all_comp.empty:
        for _ in range(3):
            st.info('Create or open a competency record to continue.')
        return
    option_map = [f"{r.get('name', '')} — {r.get('scope', r.get('area', ''))} — {r.get('competency_id', '')}" for _, r in all_comp.iterrows()]
    with tabs[1]:
        selected = st.selectbox('Competency Record', option_map, key='competency_review_select')
        cid = selected.split(' — ')[-1]
        c = all_comp[all_comp['competency_id'].astype(str) == cid].iloc[0]
        ok, gaps = readiness(str(c['user_id']), str(c.get('scope', c.get('area', ''))))
        st.subheader(f"{c.get('name', '')} — {c.get('scope', c.get('area', ''))}")
        a, b, c1, d = st.columns(4)
        a.metric('Current Level', c.get('competency_level', 'Level 0 - Trainee'))
        b.metric('Matrix Target', c.get('required_level_for_auth', '—'))
        c1.metric('Evidence', 'Ready' if ok else 'Gap')
        d.metric('Status', c.get('status', 'Pending'))
        if ok:
            st.success('All currently configured evidence requirements are satisfied.')
        else:
            st.warning('Competency evidence is not complete.')
            for g in gaps:
                st.write('• ' + g)
        if privileged:
            with st.form('competency_review_form'):
                current_level = st.selectbox('Current Level', COMPETENCY_LEVELS, index=COMPETENCY_LEVELS.index(c.get('competency_level')) if c.get('competency_level') in COMPETENCY_LEVELS else 0)
                recommended_options = ['No Change'] + COMPETENCY_LEVELS
                recommendation = st.selectbox('Recommended Level', recommended_options, index=0)
                decision = st.selectbox('Decision', ['Open', 'Under Review', 'Ready', 'Restricted', 'Not Yet Competent', 'Renewed'])
                rationale = st.text_area('Reviewer Rationale', placeholder='Evidence-based competency decision.')
                next_review = st.date_input('Next Review Date', today_value + timedelta(days=365))
                submit_review = st.form_submit_button('Save Competency Review', type='primary', use_container_width=True)
            if submit_review:
                rec_level = current_level if recommendation == 'No Change' else recommendation
                review_id = uid('CREV')
                review_status = 'Completed' if decision in ['Ready', 'Restricted', 'Not Yet Competent', 'Renewed'] else 'Open'
                db_insert('competency_reviews', {'review_id': review_id, 'competency_id': cid, 'user_id': c['user_id'], 'name': c['name'], 'scope': c.get('scope', c.get('area', '')), 'current_level': current_level, 'recommended_level': rec_level, 'decision': decision, 'rationale': rationale, 'evidence_summary': 'Ready' if ok else 'Evidence gaps: ' + '; '.join(gaps), 'gaps': json.dumps(gaps), 'reviewer_id': actor_get(actor, 'user_id'), 'reviewer_name': actor_get(actor, 'name'), 'reviewed_on': now(), 'next_review_date': str(next_review), 'status': review_status, 'created_on': now(), 'updated_on': now()})
                new_status = 'Ready' if decision == 'Ready' else 'Restricted' if decision == 'Restricted' else 'Pending' if decision == 'Not Yet Competent' else 'Under Review'
                db_update('competency_matrix', 'competency_id', cid, {'competency_level': rec_level, 'status': new_status, 'expiry_date': str(next_review), 'evidence': json.dumps({'last_decision': decision, 'rationale': rationale}, default=str), 'updated_on': now()})
                audit('Competency Reviewed', f'{cid}: {decision}', actor=actor, entity_type='competency_matrix', entity_id=cid, reason=rationale or 'Competency review', before_value=json.dumps({'level': c.get('competency_level'), 'status': c.get('status')}, default=str), after_value=json.dumps({'level': rec_level, 'status': new_status, 'decision': decision}, default=str))
                st.success('Competency review recorded and the competency record updated.')
    with tabs[2]:
        selected = st.selectbox('Evidence Record', option_map, key='competency_evidence_select')
        cid = selected.split(' — ')[-1]
        c = all_comp[all_comp['competency_id'].astype(str) == cid].iloc[0]
        uidv, scope = (str(c['user_id']), str(c.get('scope', c.get('area', ''))))
        st.subheader('Evidence Readiness')
        ok, gaps = readiness(uidv, scope)
        training_recs = db_where('training_records', 'user_id = :uid', (('uid', uidv),))
        witness = db_where('witness_surveys', 'user_id = :uid and scope = :scope', (('uid', uidv), ('scope', scope)))
        supervised = db_where('supervised_activities', 'user_id = :uid and scope = :scope', (('uid', uidv), ('scope', scope)))
        plans = db_where('development_plans', 'user_id = :uid and competency_scope = :scope', (('uid', uidv), ('scope', scope)))
        e1, e2, e3, e4 = st.columns(4)
        e1.metric('Training Records', len(training_recs))
        e2.metric('Passed Witnesses', int((witness.get('outcome', pd.Series(dtype=str)).astype(str) == 'Pass').sum()) if not witness.empty else 0)
        e3.metric('Passed Supervised', int((supervised.get('outcome', pd.Series(dtype=str)).astype(str) == 'Pass').sum()) if not supervised.empty else 0)
        e4.metric('Development Items', len(plans))
        if ok:
            st.success('Competency evidence currently meets the configured readiness rules.')
        else:
            st.error('Evidence gaps remain.')
            for g in gaps:
                st.write('• ' + g)
        with st.expander('Training Evidence', expanded=False):
            table(training_recs[[c for c in ['training_title', 'status', 'test_status', 'score', 'progress', 'due_date', 'completed_on'] if c in training_recs.columns]] if not training_recs.empty else pd.DataFrame())
        with st.expander('Witness / Supervised Evidence', expanded=False):
            if not witness.empty:
                table(witness[[c for c in ['witness_id', 'job_type', 'witness_date', 'outcome', 'comments'] if c in witness.columns]])
            if not supervised.empty:
                table(supervised[[c for c in ['supervised_id', 'activity_kind', 'activity_date', 'outcome', 'comments'] if c in supervised.columns]])
        with st.expander('Development Evidence', expanded=False):
            table(plans[[c for c in ['plan_id', 'plan_title', 'development_type', 'progress_percent', 'status', 'target_date', 'evidence_status'] if c in plans.columns]] if not plans.empty else pd.DataFrame())
    with tabs[3]:
        selected = st.selectbox('History Record', option_map, key='competency_history_select')
        cid = selected.split(' — ')[-1]
        reviews = db_where('competency_reviews', 'competency_id = :cid', (('cid', cid),))
        audit_rows = db_where('audit_trail', 'entity_id = :eid', (('eid', cid),)) if table_exists('audit_trail') else pd.DataFrame()
        st.subheader('Competency Review History')
        if not reviews.empty:
            table(reviews[[c for c in ['reviewed_on', 'reviewer_name', 'current_level', 'recommended_level', 'decision', 'rationale', 'next_review_date'] if c in reviews.columns]].sort_values('reviewed_on', ascending=False))
        else:
            st.info('No competency reviews recorded yet.')
        st.subheader('Audit History')
        if not audit_rows.empty:
            table(audit_rows[[c for c in ['timestamp', 'actor_name', 'action', 'reason', 'before_value', 'after_value'] if c in audit_rows.columns]].sort_values('timestamp', ascending=False))
        else:
            st.info('No audit events recorded for this competency yet.')
    st.divider()
    st.subheader('Scope Authorization Matrix')
    table(db_all('authorization_matrix'))

def _practical_actor_can_manage(actor: dict, target_user_id: str='') -> bool:
    """Central RBAC + relationship scope for practical evidence."""
    if can_action(actor, 'Practical / Witness', 'Manage', 'Assigned') or can_action(actor, 'Practical / Witness', 'Create', 'Organization-wide'):
        return True
    if not target_user_id:
        return False
    return str(target_user_id) in allowed_user_ids(actor, db_all)

def _ncr_roles(actor: dict) -> bool:
    return can_action(actor, 'NCR / Corrective Action', 'View', 'Assigned') or can_action(actor, 'NCR / Corrective Action', 'View', 'Department') or can_action(actor, 'NCR / Corrective Action', 'Manage', 'Organization-wide')

def _ncr_is_open(status: str) -> bool:
    return str(status or '').casefold() not in {'closed', 'rejected', 'cancelled'}

def _ncr_risk_score(severity: str, likelihood: int) -> int:
    weights = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    return weights.get(str(severity), 2) * int(likelihood or 1)

def _ncr_priority(score: int) -> str:
    if score >= 12:
        return 'Critical'
    if score >= 8:
        return 'High'
    if score >= 4:
        return 'Medium'
    return 'Low'

def competency_ncr_page(actor):
    """Unified enterprise NCR/CAPA register used by Competency, Training, QMS, Technical Review and Client Feedback."""
    st.header('NCR / Corrective Action')
    st.caption('One enterprise NCR/CAPA workflow. Source modules raise NCRs; this page owns investigation, corrective action, verification and closure.')
    if not _ncr_roles(actor):
        st.warning('You do not have permission to manage NCR / Corrective Action records.')
        return
    ncrs = db_all('competency_ncrs')
    if ncrs.empty:
        ncrs = pd.DataFrame(columns=['ncr_id', 'user_id', 'name', 'source', 'scope', 'ncr_type', 'description', 'severity', 'impact_on_authorization', 'status', 'corrective_action', 'raised_by', 'raised_on', 'closed_on'])
    display_df = ncrs.copy()
    for c in ['category', 'source_record_id', 'priority', 'likelihood', 'risk_score', 'incident_date', 'due_date', 'owner_id', 'owner_name', 'containment_action', 'root_cause', 'corrective_action_owner_id', 'corrective_action_owner_name', 'verification_status', 'verified_by', 'verified_on', 'effectiveness_check', 'effectiveness_notes', 'closure_notes', 'closed_by', 'linked_development_plan_id', 'linked_gap_action_id', 'updated_on']:
        if c not in display_df.columns:
            display_df[c] = ''
    display_df['priority'] = display_df.apply(lambda r: str(r.get('priority') or _ncr_priority(_ncr_risk_score(str(r.get('severity', 'Medium')), int(r.get('likelihood') or 2)))), axis=1)
    display_df['risk_score'] = display_df.apply(lambda r: r.get('risk_score') if str(r.get('risk_score') or '').strip() else _ncr_risk_score(str(r.get('severity', 'Medium')), int(r.get('likelihood') or 2)), axis=1)
    open_df = display_df[display_df['status'].apply(_ncr_is_open)] if not display_df.empty else display_df
    overdue_df = open_df.copy()
    if not overdue_df.empty and 'due_date' in overdue_df.columns:
        today_iso = today()
        overdue_df = overdue_df[(overdue_df['due_date'].astype(str) != '') & (overdue_df['due_date'].astype(str) < today_iso)]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Total NCRs', len(display_df))
    c2.metric('Open', len(open_df))
    c3.metric('Overdue', len(overdue_df))
    c4.metric('High / Critical', int(open_df['priority'].isin(['High', 'Critical']).sum()) if not open_df.empty else 0)
    c5.metric('Pending Verification', int(open_df['status'].eq('Verification').sum()) if not open_df.empty else 0)
    tabs = st.tabs(['NCR Register', 'Raise NCR', 'Corrective Action', 'Verification & Closure'])
    with tabs[0]:
        a, b, c, d, e = st.columns(5)
        search = a.text_input('Search', key='ncr_search')
        src_filter = b.selectbox('Source', ['All'] + sorted([str(x) for x in display_df['source'].dropna().unique()]))
        status_filter = c.selectbox('Status', ['All', 'Draft', 'Open', 'Containment', 'Corrective Action', 'Verification', 'Closed', 'Rejected', 'Cancelled'])
        sev_filter = d.selectbox('Severity', ['All', 'Low', 'Medium', 'High', 'Critical'])
        pri_filter = e.selectbox('Priority', ['All', 'Low', 'Medium', 'High', 'Critical'])
        view = display_df.copy()
        if search:
            blob = view.fillna('').astype(str).agg(' | '.join, axis=1).str.casefold()
            view = view[blob.str.contains(search.casefold(), regex=False)]
        if src_filter != 'All':
            view = view[view['source'].astype(str) == src_filter]
        if status_filter != 'All':
            view = view[view['status'].astype(str) == status_filter]
        if sev_filter != 'All':
            view = view[view['severity'].astype(str) == sev_filter]
        if pri_filter != 'All':
            view = view[view['priority'].astype(str) == pri_filter]
        cols = [c for c in ['ncr_id', 'name', 'source', 'scope', 'category', 'severity', 'priority', 'status', 'owner_name', 'due_date', 'risk_score', 'raised_on'] if c in view.columns]
        table(view[cols].sort_values(['priority', 'raised_on'], ascending=[True, False]) if not view.empty else view, max_rows=250)
        if not view.empty:
            st.download_button('Export Filtered NCR Register', view.to_csv(index=False).encode('utf-8'), 'psb_ncr_register.csv', 'text/csv')
            st.info('NCR source records remain owned by their originating module. This register owns the corrective-action lifecycle only.')
    with tabs[1]:
        users = db_all('users')
        user_labels = _user_label_series(users) if not users.empty else []
        with st.form('raise_enterprise_ncr'):
            a, b = st.columns(2)
            person_label = a.selectbox('Person / Responsible subject', [''] + user_labels)
            source = b.selectbox('Source Module', ['Competency', 'Training', 'Practical / Witness', 'QMS', 'Technical Review', 'Survey Report Review', 'Plan Review QA', 'Client Feedback', 'Audit', 'Other'])
            c, d = st.columns(2)
            category = c.selectbox('NCR Category', ['Competency', 'Training', 'Performance', 'Technical Quality', 'QMS', 'Client Feedback', 'Audit Finding', 'Rule / Interpretation', 'Documentation', 'Other'])
            ncr_type = d.text_input('NCR Type', placeholder='e.g. Missed defect, overdue training, repeated finding')
            scope = st.selectbox('Scope', ['Not Scope-Specific'] + SCOPES)
            source_record_id = st.text_input('Source Record ID', placeholder='Link to the originating record, if available')
            incident_date = st.date_input('Incident / Finding Date')
            severity = st.selectbox('Severity', ['Low', 'Medium', 'High', 'Critical'], index=1)
            likelihood = st.slider('Likelihood', 1, 5, 2)
            risk = _ncr_risk_score(severity, likelihood)
            st.caption(f'Risk score: **{risk}** · Priority: **{_ncr_priority(risk)}**')
            desc = st.text_area('Finding / Non-conformance *')
            containment = st.text_area('Immediate containment / correction')
            root_cause = st.text_area('Root cause (initial or confirmed)')
            action = st.text_area('Corrective Action *')
            owner_label = st.selectbox('Corrective Action Owner', [''] + user_labels)
            due_date = st.date_input('Corrective Action Due Date')
            impact = st.selectbox('Authorization Impact', ['None', 'Monitor', 'Review', 'Restrict', 'Suspend', 'Withdraw', 'Re-training Required'])
            linked_dp = st.text_input('Existing Development Plan ID (optional)')
            linked_gap = st.text_input('Existing Gap Advisor Action ID (optional)')
            reason = st.text_area('Reason / context for raising NCR *')
            submit = st.form_submit_button('Raise NCR', type='primary')
        if submit:
            _, uidv = _parse_user_label(person_label)
            _, owner_id = _parse_user_label(owner_label)
            owner_name = owner_label.split(' — ')[0] if owner_label else ''
            if not desc.strip() or not action.strip() or (not reason.strip()):
                st.error('Finding, Corrective Action and Reason are mandatory.')
            else:
                duplicate = False
                if not ncrs.empty:
                    for _, r in ncrs.iterrows():
                        if _ncr_is_open(str(r.get('status', ''))) and str(r.get('user_id', '')) == str(uidv or '') and (str(r.get('source_record_id', '')) == str(source_record_id or '')) and (str(r.get('category', '')) == category) and source_record_id:
                            duplicate = True
                            break
                if duplicate:
                    st.error('An open NCR already exists for this source record and category. Update the existing NCR instead of creating a duplicate.')
                else:
                    nid = uid('NCR')
                    row = {'ncr_id': nid, 'user_id': uidv or '', 'name': person_label.split(' — ')[0] if person_label else '', 'source': source, 'source_record_id': source_record_id.strip(), 'scope': '' if scope == 'Not Scope-Specific' else scope, 'category': category, 'ncr_type': ncr_type.strip(), 'description': desc.strip(), 'severity': severity, 'likelihood': likelihood, 'risk_score': risk, 'priority': _ncr_priority(risk), 'impact_on_authorization': impact, 'status': 'Open', 'containment_action': containment.strip(), 'root_cause': root_cause.strip(), 'corrective_action': action.strip(), 'corrective_action_owner_id': owner_id or '', 'corrective_action_owner_name': owner_name, 'owner_id': owner_id or '', 'owner_name': owner_name, 'incident_date': str(incident_date), 'due_date': str(due_date), 'linked_development_plan_id': linked_dp.strip(), 'linked_gap_action_id': linked_gap.strip(), 'raised_by': actor_get(actor, 'name'), 'raised_on': now(), 'closed_on': '', 'closed_by': '', 'verification_status': 'Pending', 'verified_by': '', 'verified_on': '', 'effectiveness_check': 'Pending', 'effectiveness_notes': '', 'closure_notes': '', 'updated_on': now()}
                    db_insert('competency_ncrs', row)
                    audit('NCR Raised', f'{nid} · {category} · {source}', actor=actor, entity_type='NCR', entity_id=nid, reason=reason.strip(), after_value=json.dumps({k: row.get(k) for k in ['source', 'source_record_id', 'severity', 'priority', 'status', 'due_date']}, default=str))
                    st.success(f'NCR {nid} raised successfully.')
                    st.rerun()
    with tabs[2]:
        open_actions = display_df[display_df['status'].apply(_ncr_is_open)] if not display_df.empty else display_df
        if open_actions.empty:
            st.success('No open NCRs require corrective action.')
        else:
            labels = (open_actions['ncr_id'].astype(str) + ' — ' + open_actions['name'].astype(str) + ' — ' + open_actions['priority'].astype(str)).tolist()
            selected = st.selectbox('Select NCR', labels)
            nid = selected.split(' — ')[0]
            row = open_actions[open_actions['ncr_id'].astype(str) == nid].iloc[0]
            st.markdown(f"### {nid} · {row.get('category', 'NCR')}")
            st.write(f"**Finding:** {row.get('description', '')}")
            st.write(f"**Root cause:** {row.get('root_cause', '') or 'Not yet recorded'}")
            with st.form('ncr_action_update'):
                status = st.selectbox('Lifecycle Status', ['Open', 'Containment', 'Corrective Action', 'Verification', 'Closed', 'Rejected', 'Cancelled'], index=['Open', 'Containment', 'Corrective Action', 'Verification', 'Closed', 'Rejected', 'Cancelled'].index(str(row.get('status', 'Open'))) if str(row.get('status', 'Open')) in ['Open', 'Containment', 'Corrective Action', 'Verification', 'Closed', 'Rejected', 'Cancelled'] else 0)
                containment = st.text_area('Containment / Immediate Correction', str(row.get('containment_action', '')))
                root_cause = st.text_area('Root Cause', str(row.get('root_cause', '')))
                action = st.text_area('Corrective Action', str(row.get('corrective_action', '')))
                owner = st.text_input('Corrective Action Owner', str(row.get('corrective_action_owner_name', row.get('owner_name', ''))))
                due = st.text_input('Due Date', str(row.get('due_date', '')))
                notes = st.text_area('Progress / Update Notes')
                reason = st.text_area('Reason for update *')
                save = st.form_submit_button('Save Corrective Action', type='primary')
            if save:
                if not reason.strip():
                    st.error('Reason is required for corrective-action changes.')
                else:
                    before = json.dumps({k: row.get(k, '') for k in ['status', 'containment_action', 'root_cause', 'corrective_action', 'corrective_action_owner_name', 'due_date']}, default=str)
                    db_update('competency_ncrs', 'ncr_id', nid, {'status': status, 'containment_action': containment.strip(), 'root_cause': root_cause.strip(), 'corrective_action': action.strip(), 'corrective_action_owner_name': owner.strip(), 'owner_name': owner.strip(), 'due_date': due.strip(), 'updated_on': now()})
                    audit('NCR Corrective Action Updated', nid, actor=actor, entity_type='NCR', entity_id=nid, reason=reason.strip(), before_value=before, after_value=json.dumps({'status': status, 'owner': owner.strip(), 'due_date': due.strip(), 'progress_notes': notes.strip()}, default=str))
                    st.success('Corrective action updated.')
                    st.rerun()
    with tabs[3]:
        candidates = display_df[display_df['status'].astype(str).eq('Verification')] if not display_df.empty else display_df
        if candidates.empty:
            st.success('No NCRs are currently waiting for effectiveness verification.')
        else:
            labels = (candidates['ncr_id'].astype(str) + ' — ' + candidates['name'].astype(str)).tolist()
            selected = st.selectbox('NCR awaiting verification', labels)
            nid = selected.split(' — ')[0]
            row = candidates[candidates['ncr_id'].astype(str) == nid].iloc[0]
            st.write(f"**Corrective Action:** {row.get('corrective_action', '')}")
            with st.form('verify_ncr'):
                verification = st.selectbox('Effectiveness', ['Pending', 'Effective', 'Partially Effective', 'Not Effective'])
                effectiveness_notes = st.text_area('Verification / Effectiveness Evidence')
                closure_notes = st.text_area('Closure Notes')
                reason = st.text_area('Verification reason *')
                verify = st.form_submit_button('Record Verification', type='primary')
            if verify:
                if not reason.strip() or not effectiveness_notes.strip():
                    st.error('Verification reason and evidence are required.')
                else:
                    new_status = 'Closed' if verification == 'Effective' else 'Corrective Action' if verification in ['Partially Effective', 'Not Effective'] else 'Verification'
                    db_update('competency_ncrs', 'ncr_id', nid, {'verification_status': verification, 'effectiveness_check': verification, 'effectiveness_notes': effectiveness_notes.strip(), 'closure_notes': closure_notes.strip(), 'verified_by': actor_get(actor, 'name'), 'verified_on': now(), 'status': new_status, 'closed_on': today() if new_status == 'Closed' else '', 'closed_by': actor_get(actor, 'name') if new_status == 'Closed' else '', 'updated_on': now()})
                    audit('NCR Verification Recorded', nid, actor=actor, entity_type='NCR', entity_id=nid, reason=reason.strip(), after_value=json.dumps({'effectiveness': verification, 'status': new_status}, default=str))
                    st.success('Verification recorded.')
                    st.rerun()
    st.divider()
    st.caption('Enterprise rule: NCRs are single records. Training, Competency, Practical/Witness, QMS, Technical Review and Client Feedback may raise or reference the NCR, but none creates a competing corrective-action system.')

def _gap_advisor_action_specs(user_id: str, scope: str, actor: dict) -> list[dict]:
    """Build explainable recommendations from authoritative evidence without creating duplicate workflows."""
    users = db_all('users')
    urow = users[users['user_id'].astype(str) == str(user_id)] if not users.empty and 'user_id' in users.columns else pd.DataFrame()
    u = urow.iloc[0].to_dict() if not urow.empty else {}
    ok, gaps = readiness(user_id, scope)
    specs = []
    text = ' '.join(gaps).lower()
    today_value = date.today()
    if 'training' in text:
        for g in gaps:
            if 'training gap:' in g.lower() or 'mandatory training incomplete' in g.lower():
                specs.append({'gap_key': f'training:{scope}:{hash(g)}', 'gap_category': 'Training', 'gap_title': 'Complete required training', 'gap_detail': g, 'priority': 'High', 'target_module': 'Training', 'action_type': 'Complete / Assign Training', 'due_date': str(today_value + timedelta(days=30))})
                break
    if 'witness' in text:
        specs.append({'gap_key': f'witness:{scope}', 'gap_category': 'Practical / Witness', 'gap_title': 'Complete required witness assessment', 'gap_detail': next((g for g in gaps if 'witness' in g.lower()), 'Witness evidence is incomplete for this scope.'), 'priority': 'High', 'target_module': 'Practical / Witness', 'action_type': 'Schedule Witness', 'due_date': str(today_value + timedelta(days=30))})
    if 'supervised' in text:
        specs.append({'gap_key': f'supervised:{scope}', 'gap_category': 'Practical / Witness', 'gap_title': 'Complete supervised activity', 'gap_detail': next((g for g in gaps if 'supervised' in g.lower()), 'Supervised activity evidence is incomplete.'), 'priority': 'High', 'target_module': 'Practical / Witness', 'action_type': 'Schedule Supervised Activity', 'due_date': str(today_value + timedelta(days=45))})
    if 'joint plan' in text:
        specs.append({'gap_key': f'joint_plan:{scope}', 'gap_category': 'Practical / Witness', 'gap_title': 'Complete joint plan review', 'gap_detail': next((g for g in gaps if 'joint plan' in g.lower()), 'Joint plan review evidence is incomplete.'), 'priority': 'Medium', 'target_module': 'Practical / Witness', 'action_type': 'Schedule Joint Plan Review', 'due_date': str(today_value + timedelta(days=45))})
    if 'independent plan' in text:
        specs.append({'gap_key': f'independent_plan:{scope}', 'gap_category': 'Practical / Witness', 'gap_title': 'Complete independent plan review', 'gap_detail': next((g for g in gaps if 'independent plan' in g.lower()), 'Independent plan review evidence is incomplete.'), 'priority': 'High', 'target_module': 'Practical / Witness', 'action_type': 'Schedule Independent Plan Review', 'due_date': str(today_value + timedelta(days=60))})
    if 'development-plan' in text or 'development plan' in text:
        specs.append({'gap_key': f'development:{scope}', 'gap_category': 'Development', 'gap_title': 'Progress existing development plan', 'gap_detail': next((g for g in gaps if 'development-plan' in g.lower() or 'development plan' in g.lower()), 'An open development-plan item remains for this scope.'), 'priority': 'Medium', 'target_module': 'Development Plans', 'action_type': 'Review Existing Development Plan', 'due_date': str(today_value + timedelta(days=30))})
    cpd = db_all('cpd_records')
    cpd_hours = 0.0
    if not cpd.empty and 'user_id' in cpd.columns:
        cpd_hours = float(pd.to_numeric(cpd.loc[cpd['user_id'].astype(str) == str(user_id), 'hours'], errors='coerce').fillna(0).sum()) if 'hours' in cpd.columns else 0.0
    if cpd_hours < 20:
        specs.append({'gap_key': f'cpd:{user_id}', 'gap_category': 'CPD', 'gap_title': 'Increase CPD evidence', 'gap_detail': f'Recorded CPD is {cpd_hours:g} hours; additional verified CPD may be needed for the annual target.', 'priority': 'Medium', 'target_module': 'CPD', 'action_type': 'Record / Verify CPD', 'due_date': str(today_value + timedelta(days=90))})
    ncrs = db_all('competency_ncrs')
    if not ncrs.empty and 'user_id' in ncrs.columns:
        open_ncr = ncrs[(ncrs['user_id'].astype(str) == str(user_id)) & (ncrs.get('status', '').astype(str) != 'Closed')]
    else:
        open_ncr = pd.DataFrame()
    if not open_ncr.empty:
        specs.append({'gap_key': f'ncr:{scope}', 'gap_category': 'NCR / Corrective Action', 'gap_title': 'Close open competency NCRs', 'gap_detail': f'{len(open_ncr)} competency NCR(s) remain open and may block readiness.', 'priority': 'Critical', 'target_module': 'NCR / Corrective Action', 'action_type': 'Close Corrective Action', 'due_date': str(today_value + timedelta(days=14))})
    return specs

def competency_gap_advisor_page(actor):
    """State-of-the-art, explainable Gap Advisor. It recommends actions but never duplicates the owning workflow."""
    st.header('Gap Advisor')
    st.caption('Evidence-driven development guidance. Recommendations are calculated from existing Training, Development, CPD, Practical/Witness and Competency records; no duplicate workflow is created here.')
    role = actor_get(actor, 'role')
    users = db_all('users')
    selectable = restrict_user_frame(users, actor)
    if can_action(actor, 'Gap Advisor', 'Manage', 'Organization-wide') or can_action(actor, 'Gap Advisor', 'Review', 'Department'):
        selectable = users
    if selectable.empty:
        st.info('No employee records are available for Gap Advisor.')
        return
    person_label = st.selectbox('Employee', selectable['name'].astype(str) + ' — ' + selectable['user_id'].astype(str), key='gap_person')
    uidv = person_label.split(' — ', 1)[-1]
    scope = st.selectbox('Target Scope', SCOPES, key='gap_scope')
    specs = _gap_advisor_action_specs(uidv, scope, actor)
    ok, raw_gaps = readiness(uidv, scope)
    actions = restrict_user_frame(db_all('gap_advisor_actions'), actor)
    existing = actions[(actions.get('user_id', '').astype(str) == str(uidv)) & (actions.get('scope', '').astype(str) == str(scope))] if not actions.empty else pd.DataFrame()
    open_count = int(len(existing[existing.get('status', '').astype(str).isin(['Recommended', 'Accepted', 'In Progress'])])) if not existing.empty else 0
    gap_manage_allowed = can_action(actor, 'Gap Advisor', 'Manage', 'Organization-wide') or can_action(actor, 'Gap Advisor', 'Create', 'Assigned') or can_action(actor, 'Development Plans', 'Create', 'Assigned')
    critical_count = sum((1 for x in specs if x['priority'] == 'Critical'))
    high_count = sum((1 for x in specs if x['priority'] == 'High'))
    cpd = db_all('cpd_records')
    cpd_hours = 0.0
    if not cpd.empty and 'user_id' in cpd.columns and ('hours' in cpd.columns):
        cpd_hours = float(pd.to_numeric(cpd.loc[cpd['user_id'].astype(str) == str(uidv), 'hours'], errors='coerce').fillna(0).sum())
    metrics([('Evidence Status', 'READY' if ok else 'GAPS'), ('Open Recommendations', open_count), ('High / Critical', high_count + critical_count), ('CPD Hours', f'{cpd_hours:g}')])
    tabs = st.tabs(['Gap Overview', 'Recommendations', 'Existing Actions', 'Evidence Sources'])
    with tabs[0]:
        if ok:
            st.success('No configured competency/readiness gaps were detected for this scope.')
        else:
            st.error(f'{len(raw_gaps)} evidence gap(s) detected.')
            for g in raw_gaps:
                st.write('• ' + g)
        st.subheader('Reasoning')
        st.write("The advisor compares the employee's current evidence against the configured authorization/competency matrix and shows the source of each gap.")
        if specs:
            table(pd.DataFrame([{'Priority': x['priority'], 'Category': x['gap_category'], 'Gap': x['gap_title'], 'Target Module': x['target_module'], 'Due': x['due_date']} for x in specs]))
        else:
            st.info('No recommended action is currently required.')
    with tabs[1]:
        st.subheader('Recommended Actions')
        if not gap_manage_allowed:
            st.info('Recommendations are visible, but accepting actions requires an authorized development/workflow role.')
        for x in specs:
            duplicate = existing[(existing.get('gap_key', '').astype(str) == x['gap_key']) & existing.get('status', '').astype(str).isin(['Recommended', 'Accepted', 'In Progress'])] if not existing.empty else pd.DataFrame()
            with st.container(border=True):
                st.markdown(f"### {x['gap_title']}")
                st.write(x['gap_detail'])
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Priority:** {x['priority']}")
                c2.write(f"**Owner:** {actor_get(actor, 'name')}")
                c3.write(f"**Target:** {x['target_module']}")
                if duplicate.empty and gap_manage_allowed:
                    if st.button('Accept Recommendation', key='gap_accept_' + x['gap_key'].replace(':', '_').replace(' ', '_')):
                        aid = uid('GAP')
                        db_insert('gap_advisor_actions', {'gap_action_id': aid, 'user_id': uidv, 'name': str(person_label).split(' — ', 1)[0], 'scope': scope, 'gap_key': x['gap_key'], 'gap_category': x['gap_category'], 'gap_title': x['gap_title'], 'gap_detail': x['gap_detail'], 'priority': x['priority'], 'target_module': x['target_module'], 'action_type': x['action_type'], 'linked_record_id': '', 'development_plan_id': '', 'due_date': x['due_date'], 'status': 'Accepted', 'owner_id': actor_get(actor, 'user_id'), 'owner_name': actor_get(actor, 'name'), 'source_snapshot': json.dumps({'raw_gaps': raw_gaps, 'scope': scope}, default=str), 'created_by': actor_get(actor, 'user_id'), 'created_on': now(), 'updated_on': now(), 'completed_on': '', 'completion_notes': ''})
                        audit('Gap Recommendation Accepted', x['gap_title'], actor=actor, entity_type='gap_advisor_actions', entity_id=aid, reason='Evidence-driven recommendation accepted', after_value=json.dumps(x, default=str))
                        st.success('Recommendation accepted and recorded without creating a duplicate workflow.')
                        st.rerun()
                elif not duplicate.empty:
                    st.info('An active recommendation for this gap already exists.')
    with tabs[2]:
        st.subheader('Existing Gap Actions')
        if existing.empty:
            st.info('No Gap Advisor actions have been accepted for this employee/scope.')
        else:
            table(existing[[c for c in ['gap_action_id', 'gap_category', 'gap_title', 'priority', 'target_module', 'action_type', 'due_date', 'status', 'owner_name', 'created_on'] if c in existing.columns]])
            if gap_manage_allowed:
                active = existing[existing.get('status', '').astype(str).isin(['Accepted', 'In Progress'])]
                if not active.empty:
                    label = st.selectbox('Action', active['gap_action_id'].astype(str), key='gap_action_update')
                    selected = active[active['gap_action_id'].astype(str) == label].iloc[0]
                    new_status = st.selectbox('Status', ['Accepted', 'In Progress', 'Completed', 'Cancelled'], key='gap_action_status')
                    notes = st.text_area('Completion / Update Notes', key='gap_action_notes')
                    if st.button('Update Action', type='primary', key='gap_action_save'):
                        db_update('gap_advisor_actions', 'gap_action_id', label, {'status': new_status, 'updated_on': now(), 'completed_on': today() if new_status == 'Completed' else '', 'completion_notes': notes.strip()})
                        audit('Gap Advisor Action Updated', label, actor=actor, entity_type='gap_advisor_actions', entity_id=label, reason=notes or 'Gap action status update', after_value=json.dumps({'status': new_status, 'notes': notes}, default=str))
                        st.success('Gap action updated.')
                        st.rerun()
    with tabs[3]:
        st.subheader('Evidence Sources')
        train = db_all('training_records')
        cpd_df = db_all('cpd_records')
        witness = db_all('witness_surveys')
        supervised = db_all('supervised_activities')
        development = db_all('development_plans')
        source_rows = [('Training Records', 0 if train.empty else len(train[train.get('user_id', '').astype(str) == str(uidv)]), 'Training'), ('CPD Records', 0 if cpd_df.empty else len(cpd_df[cpd_df.get('user_id', '').astype(str) == str(uidv)]), 'CPD'), ('Witness Records', 0 if witness.empty else len(witness[witness.get('user_id', '').astype(str) == str(uidv)]), 'Practical / Witness'), ('Supervised Activities', 0 if supervised.empty else len(supervised[supervised.get('user_id', '').astype(str) == str(uidv)]), 'Practical / Witness'), ('Development Plan Items', 0 if development.empty else len(development[development.get('user_id', '').astype(str) == str(uidv)]), 'Development Plans')]
        table(pd.DataFrame(source_rows, columns=['Evidence Source', 'Records', 'Authoritative Module']))
        st.caption('Gap Advisor never copies these records. It reads them, explains the gap and routes the user to the module that owns the corrective action.')
