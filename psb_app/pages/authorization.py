from psb_app.common import (
    PUBLIC_URL,
    SCOPES,
    actor_get,
    add_months,
    audit,
    build_certificate,
    can_action,
    clean,
    date,
    days_until,
    db_all,
    db_insert,
    db_update,
    get_matrix_for_scope,
    json,
    now,
    pd,
    readiness,
    restrict_user_frame,
    select_person,
    st,
    timedelta,
    today,
    uid,
)

def _authorization_roles(actor: dict, purpose: str='view') -> bool:
    """Centralized authorization-stage permission resolver. No page-local role lists."""
    action_map = {'create': ('Create', 'Assigned'), 'principal': ('Review', 'Department'), 'technical': ('Approve', 'Organization-wide'), 'qms': ('Review', 'Department'), 'crb': ('Approve', 'Organization-wide'), 'management': ('Approve', 'Organization-wide'), 'revalidation': ('Approve', 'Organization-wide'), 'restrict': ('Manage', 'Organization-wide'), 'view': ('View', 'Organization-wide')}
    action, scope = action_map.get(purpose, action_map['view'])
    return can_action(actor, 'Authorization', action, scope) or can_action(actor, 'Authorization', 'View', 'Assigned')

def _auth_label(row) -> str:
    return f"{clean(row.get('name', ''))} — {clean(row.get('scope', ''))} — {clean(row.get('authorization_id', ''))}"

def _auth_stage(status: str) -> str:
    return {'Draft': 'Draft', 'Trainer Recommended': 'Principal Review', 'Principal Reviewed': 'Technical Authority', 'Technical Reviewed': 'QMS Review', 'QMS Reviewed': 'CRB', 'CRB Approved': 'Management', 'CRB Rejected': 'CRB Decision', 'CRB Deferred': 'CRB Decision', 'Management Approved': 'Authorized', 'Withdrawn': 'Withdrawn', 'Suspended': 'Suspended', 'Expired': 'Expired'}.get(clean(status), clean(status) or 'Draft')

def _authorization_snapshot(req: pd.Series) -> dict:
    uidv = str(req.get('user_id', ''))
    scope = str(req.get('scope', ''))
    training = db_all('training_records')
    t = training[training['user_id'].astype(str) == uidv] if not training.empty and 'user_id' in training.columns else pd.DataFrame()
    completed_training = int(t.get('status', pd.Series(dtype=str)).astype(str).isin(['Completed', 'Passed']).sum()) if not t.empty else 0
    witness = db_all('witness_surveys')
    w = witness[(witness['user_id'].astype(str) == uidv) & (witness['scope'].astype(str) == scope)] if not witness.empty and 'scope' in witness.columns else pd.DataFrame()
    supervised = db_all('supervised_activities')
    sv = supervised[(supervised['user_id'].astype(str) == uidv) & (supervised['scope'].astype(str) == scope)] if not supervised.empty and 'scope' in supervised.columns else pd.DataFrame()
    comp = db_all('competency_matrix')
    c = comp[comp['user_id'].astype(str) == uidv] if not comp.empty else pd.DataFrame()
    ncr = db_all('competency_ncrs')
    n = ncr[(ncr['user_id'].astype(str) == uidv) & ~ncr['status'].astype(str).str.casefold().isin(['closed', 'rejected', 'cancelled'])] if not ncr.empty else pd.DataFrame()
    cpd = db_all('cpd_records')
    cp = cpd[cpd['user_id'].astype(str) == uidv] if not cpd.empty else pd.DataFrame()
    return {'training_completed': completed_training, 'witness_passed': int((w.get('outcome', pd.Series(dtype=str)).astype(str) == 'Pass').sum()) if not w.empty else 0, 'supervised_passed': int((sv.get('outcome', pd.Series(dtype=str)).astype(str) == 'Pass').sum()) if not sv.empty else 0, 'competency_count': len(c), 'open_ncr': len(n), 'cpd_hours': float(pd.to_numeric(cp.get('hours', pd.Series(dtype=float)), errors='coerce').fillna(0).sum()) if not cp.empty else 0.0}

def _authorization_event(aid: str, req: pd.Series | dict, from_status: str, to_status: str, actor: dict, reason: str=''):
    user_id = req.get('user_id', '') if hasattr(req, 'get') else ''
    db_insert('authorization_events', {'event_id': uid('AEV'), 'authorization_id': aid, 'user_id': user_id, 'event_type': 'Status Change', 'from_status': from_status, 'to_status': to_status, 'actor_id': actor_get(actor, 'user_id'), 'actor_name': actor_get(actor, 'name'), 'reason': reason, 'created_on': now()})
    audit('Authorization Status Changed', f'{aid}: {from_status} → {to_status}', actor=actor, entity_type='authorization_requests', entity_id=aid, reason=reason, before_value=from_status, after_value=to_status)

def _open_authorization_exists(user_id: str, scope: str, job_type: str) -> bool:
    auths = db_all('authorization_requests')
    if auths.empty:
        return False
    same = auths[(auths['user_id'].astype(str) == str(user_id)) & (auths['scope'].astype(str) == str(scope)) & (auths['job_type'].astype(str) == str(job_type))]
    return not same[same['status'].astype(str).isin(['Draft', 'Trainer Recommended', 'Principal Reviewed', 'Technical Reviewed', 'QMS Reviewed', 'CRB Approved'])].empty

def _issue_authorization_certificate(req: pd.Series, actor: dict):
    """Issue the controlled digital Certificate of Authorization for exactly one year from approval."""
    existing = db_all('authorization_certificates')
    if not existing.empty:
        old = existing[existing['authorization_id'].astype(str) == str(req['authorization_id'])]
        if not old.empty and clean(old.iloc[0].get('status', '')) == 'Valid':
            return old.iloc[0]['certificate_id']
    # Validity starts on the final approval date, not on case-creation/CRB date.
    issue_date = today()
    expiry_date = add_months(issue_date, 12)
    req = req.copy()
    req['expiry_date'] = expiry_date
    req['decision_date'] = issue_date
    req['status'] = 'Management Approved'
    db_update('authorization_requests', 'authorization_id', req['authorization_id'], {'expiry_date': expiry_date, 'updated_on': now()})
    cert_id, html, qr = build_certificate(req)
    db_insert('authorization_certificates', {'certificate_id': cert_id, 'authorization_id': req['authorization_id'], 'user_id': req['user_id'], 'name': req['name'], 'scope': req['scope'], 'job_type': req['job_type'], 'issue_date': issue_date, 'expiry_date': expiry_date, 'certificate_html': html, 'qr_data_uri': qr, 'storage_link': f'database://authorization_certificates/{cert_id}', 'verification_url': f'{PUBLIC_URL}/verify/{cert_id}', 'status': 'Valid', 'public_status': 'Valid', 'created_on': now()})
    _certificate_history(cert_id, req['authorization_id'], req['user_id'], '', 'Valid', 'Issued', actor, 'CRB completed and final authorization approved')
    db_update('authorization_requests', 'authorization_id', req['authorization_id'], {'certificate_id': cert_id, 'certificate_html': html, 'certificate_storage_link': f'database://authorization_certificates/{cert_id}', 'qr_data_uri': qr, 'certificate_status': 'Valid', 'decision_date': issue_date, 'expiry_date': expiry_date, 'updated_on': now(), 'updated_by': actor_get(actor, 'name')})
    try:
        from psb_app.common import create_notification
        create_notification(str(req['user_id']), 'Digital Certificate of Authorization Issued', f'{cert_id} · Valid {issue_date} to {expiry_date}', 'Authorization')
    except Exception:
        pass
    audit('Authorization Certificate Issued', f'Certificate {cert_id} issued for one year ({issue_date} to {expiry_date})', actor=actor, entity_type='authorization_certificates', entity_id=cert_id, reason='CRB completed and final authorization approved')
    return cert_id


def _certificate_history(cert_id: str, auth_id: str, user_id: str, from_status: str, to_status: str, event_type: str, actor: dict, reason: str=''):
    db_insert('authorization_certificate_history', {
        'history_id': uid('CHG'), 'certificate_id': cert_id, 'authorization_id': auth_id, 'user_id': user_id,
        'from_status': from_status, 'to_status': to_status, 'event_type': event_type, 'reason': reason,
        'actor_id': actor_get(actor, 'user_id'), 'actor_name': actor_get(actor, 'name'), 'event_on': now(), 'metadata': ''
    })
def authorization_page(actor):
    st.header('Authorization & Governance')
    st.caption('One controlled authorization lifecycle from evidence readiness through technical review, QMS, CRB, management approval, certificate and expiry.')
    auths = restrict_user_frame(db_all('authorization_requests'), actor)
    if auths.empty:
        auths = pd.DataFrame(columns=['authorization_id', 'user_id', 'name', 'scope', 'job_type', 'status', 'expiry_date'])
    counts = [('Open Requests', int(auths['status'].isin(['Draft', 'Trainer Recommended', 'Principal Reviewed', 'Technical Reviewed', 'QMS Reviewed', 'CRB Approved']).sum()) if not auths.empty else 0), ('Awaiting CRB', int((auths.get('status', pd.Series(dtype=str)) == 'QMS Reviewed').sum()) if not auths.empty else 0), ('Awaiting Management', int((auths.get('status', pd.Series(dtype=str)) == 'CRB Approved').sum()) if not auths.empty else 0), ('Authorized', int((auths.get('status', pd.Series(dtype=str)) == 'Management Approved').sum()) if not auths.empty else 0), ('Expiring ≤90d', int(sum((days_until(x) <= 90 and days_until(x) >= 0 for x in auths.get('expiry_date', pd.Series(dtype=str)).astype(str)))) if not auths.empty else 0), ('Expired', int(sum((days_until(x) < 0 for x in auths.get('expiry_date', pd.Series(dtype=str)).astype(str)))) if not auths.empty else 0)]
    metrics(counts)
    tabs = st.tabs(['Requests', 'Create Request', 'Review Queue', 'Certificate Register'])
    with tabs[0]:
        if not auths.empty:
            c1, c2, c3 = st.columns(3)
            search = c1.text_input('Search', key='auth_search')
            status_filter = c2.selectbox('Status', ['All'] + sorted(auths['status'].astype(str).unique().tolist()), key='auth_status_filter')
            scope_filter = c3.selectbox('Scope', ['All'] + sorted(auths['scope'].astype(str).unique().tolist()), key='auth_scope_filter')
            view = auths.copy()
            if search:
                view = view[view.apply(lambda r: search.casefold() in ' '.join(map(str, r.tolist())).casefold(), axis=1)]
            if status_filter != 'All':
                view = view[view['status'].astype(str) == status_filter]
            if scope_filter != 'All':
                view = view[view['scope'].astype(str) == scope_filter]
            show = [c for c in ['authorization_id', 'name', 'scope', 'job_type', 'status', 'current_stage', 'risk_category', 'expiry_date', 'certificate_id', 'updated_on'] if c in view.columns]
            table(view[show] if show else view)
        else:
            st.info('No authorization requests exist.')
    with tabs[1]:
        if not _authorization_roles(actor, 'create'):
            st.info('Authorization request creation is limited to the designated recommending roles.')
        else:
            comp = db_all('competency_matrix')
            if comp.empty:
                st.info('No competency records are available yet.')
            else:
                eligible = comp[comp['status'].astype(str).str.contains('Ready|Competent|Authorized', case=False, na=False)] if 'status' in comp.columns else comp
                if eligible.empty:
                    eligible = comp
                labels = [f'{r.name} — {r.scope} — {r.competency_id}' for r in eligible.itertuples()]
                sel = st.selectbox('Competency Record', labels)
                cid = sel.rsplit(' — ', 1)[-1]
                c = eligible[eligible['competency_id'].astype(str) == cid].iloc[0]
                ok, gaps = readiness(c['user_id'], c['scope'])
                if ok:
                    st.success('Evidence readiness passed. This person can enter the authorization workflow.')
                else:
                    st.warning('Evidence is incomplete.')
                    for g in gaps:
                        st.write('• ' + str(g))
                matrix = get_matrix_for_scope(c['scope'])
                expiry = add_months(int(matrix['validity_months'])) if matrix is not None else add_months(36)
                reason = st.text_area('Application / recommendation reason', key='auth_reason')
                if st.button('Create Authorization Request', type='primary', disabled=not ok):
                    if _open_authorization_exists(c['user_id'], c['scope'], c['job_type']):
                        st.error('An active authorization request already exists for this person, scope and job type.')
                    else:
                        aid = uid('AUTH')
                        payload = {'authorization_id': aid, 'user_id': c['user_id'], 'name': c['name'], 'trainee_path': c['trainee_path'], 'job_type': c['job_type'], 'scope': c['scope'], 'competency_id': cid, 'status': 'Trainer Recommended', 'current_stage': 'Principal Review', 'risk_category': matrix.get('risk_category', '') if matrix is not None else '', 'validity_months': int(matrix.get('validity_months', 36)) if matrix is not None else 36, 'application_reason': reason, 'requested_by': actor_get(actor, 'user_id'), 'requested_on': now(), 'tutor_remarks': 'Evidence readiness satisfied; recommendation submitted.', 'tutor_signature': actor_get(actor, 'name'), 'tutor_signed_on': now(), 'principal_remarks': '', 'principal_signature': '', 'principal_signed_on': '', 'technical_remarks': '', 'technical_signature': '', 'technical_signed_on': '', 'qms_remarks': '', 'qms_signature': '', 'qms_signed_on': '', 'crb_decision': '', 'crb_remarks': '', 'management_remarks': '', 'management_signature': '', 'management_signed_on': '', 'expiry_date': expiry, 'certificate_id': '', 'certificate_html': '', 'certificate_storage_link': '', 'qr_data_uri': '', 'certificate_status': '', 'created_on': now(), 'updated_on': now(), 'updated_by': actor_get(actor, 'name')}
                        db_insert('authorization_requests', payload)
                        _authorization_event(aid, payload, '', 'Trainer Recommended', actor, reason or 'Authorization request created')
                        st.success(f'Authorization request {aid} created.')
                        st.rerun()
    with tabs[2]:
        queue = auths[auths['status'].astype(str).isin(['Trainer Recommended', 'Principal Reviewed', 'Technical Reviewed', 'QMS Reviewed', 'CRB Approved'])] if not auths.empty else pd.DataFrame()
        if queue.empty:
            st.info('No authorization reviews are currently waiting.')
        else:
            table(queue[[c for c in ['authorization_id', 'name', 'scope', 'status', 'current_stage', 'expiry_date'] if c in queue.columns]])
            st.caption('Use the dedicated Technical Authority and CRB pages for those decisions. Management approvals remain here only for the final stage.')
    with tabs[3]:
        certs = db_all('authorization_certificates')
        if certs.empty:
            st.info('No certificates have been issued.')
        else:
            table(certs[[c for c in ['certificate_id', 'authorization_id', 'name', 'scope', 'issue_date', 'expiry_date', 'status', 'public_status'] if c in certs.columns]])
    stage_candidates = pd.DataFrame()
    stage_name = ''
    target_status = ''
    remarks_field = ''
    if _authorization_roles(actor, 'principal'):
        stage_candidates = auths[auths['status'].astype(str) == 'Trainer Recommended'] if not auths.empty else pd.DataFrame()
        stage_name, target_status, remarks_field = ('Principal Review', 'Principal Reviewed', 'principal_remarks')
    elif _authorization_roles(actor, 'qms'):
        stage_candidates = auths[auths['status'].astype(str) == 'Technical Reviewed'] if not auths.empty else pd.DataFrame()
        stage_name, target_status, remarks_field = ('QMS Review', 'QMS Reviewed', 'qms_remarks')
    if not stage_candidates.empty:
        st.subheader(stage_name)
        sel = st.selectbox('Request for your review', stage_candidates.apply(_auth_label, axis=1), key=f"auth_{stage_name.replace(' ', '_').lower()}")
        aid = sel.rsplit(' — ', 1)[-1]
        req = stage_candidates[stage_candidates['authorization_id'].astype(str) == aid].iloc[0]
        decision_options = ['Approve', 'Return for Clarification', 'Reject'] if stage_name == 'Principal Review' else ['Approve', 'Return for Clarification', 'Reject']
        decision = st.selectbox('Decision', decision_options, key=f"auth_{stage_name.replace(' ', '_').lower()}_decision")
        remarks = st.text_area('Review Remarks', key=f"auth_{stage_name.replace(' ', '_').lower()}_remarks")
        if st.button(f'Record {stage_name}', type='primary', key=f"auth_{stage_name.replace(' ', '_').lower()}_btn"):
            if decision == 'Approve':
                new_status = target_status
                next_stage = _auth_stage(new_status)
            elif decision == 'Return for Clarification':
                new_status = 'Trainer Recommended' if stage_name == 'Principal Review' else 'Principal Reviewed'
                next_stage = _auth_stage(new_status)
            else:
                new_status = 'Withdrawn'
                next_stage = 'Withdrawn'
            patch = {'status': new_status, 'current_stage': next_stage, remarks_field: remarks, 'updated_on': now(), 'updated_by': actor_get(actor, 'name'), 'last_reviewed_on': now()}
            if stage_name == 'Principal Review':
                patch.update({'principal_signature': actor_get(actor, 'name'), 'principal_signed_on': now()})
            else:
                patch.update({'qms_signature': actor_get(actor, 'name'), 'qms_signed_on': now()})
            db_update('authorization_requests', 'authorization_id', aid, patch)
            _authorization_event(aid, req, req['status'], new_status, actor, remarks or f'{stage_name}: {decision}')
            st.success(f'{stage_name} recorded.')
            st.rerun()
    if _authorization_roles(actor, 'management') and (not auths.empty):
        pending = auths[auths['status'].astype(str) == 'CRB Approved']
        if not pending.empty:
            st.subheader('Management Authorization Decision')
            sel = st.selectbox('Pending CRB-approved request', pending.apply(_auth_label, axis=1), key='auth_mgmt_select')
            aid = sel.rsplit(' — ', 1)[-1]
            req = pending[pending['authorization_id'].astype(str) == aid].iloc[0]
            decision = st.selectbox('Decision', ['Approve', 'Reject', 'Return to CRB'], key='auth_mgmt_decision')
            remarks = st.text_area('Management remarks', key='auth_mgmt_remarks')
            if st.button('Record Management Decision', type='primary', key='auth_mgmt_btn'):
                if decision == 'Approve':
                    patch = {'status': 'Management Approved', 'current_stage': 'Authorized', 'management_remarks': remarks, 'management_signature': actor_get(actor, 'name'), 'management_signed_on': now(), 'decision_date': today(), 'last_reviewed_on': now(), 'updated_on': now(), 'updated_by': actor_get(actor, 'name')}
                    db_update('authorization_requests', 'authorization_id', aid, patch)
                    tmp = req.copy()
                    [tmp.__setitem__(k, v) for k, v in patch.items()]
                    _issue_authorization_certificate(tmp, actor)
                    db_update('competency_matrix', 'competency_id', req['competency_id'], {'status': 'Authorized', 'competency_level': 'Level 3 - Authorized', 'updated_on': now()})
                    db_update('users', 'user_id', req['user_id'], {'competency_level': 'Level 3 - Authorized'})
                    _authorization_event(aid, req, 'CRB Approved', 'Management Approved', actor, remarks or 'Final management approval')
                elif decision == 'Reject':
                    db_update('authorization_requests', 'authorization_id', aid, {'status': 'Withdrawn', 'current_stage': 'Withdrawn', 'rejection_reason': remarks, 'decision_date': today(), 'updated_on': now(), 'updated_by': actor_get(actor, 'name')})
                    _authorization_event(aid, req, 'CRB Approved', 'Withdrawn', actor, remarks or 'Management rejected authorization')
                else:
                    db_update('authorization_requests', 'authorization_id', aid, {'status': 'CRB Deferred', 'current_stage': 'CRB Decision', 'management_remarks': remarks, 'updated_on': now(), 'updated_by': actor_get(actor, 'name')})
                    _authorization_event(aid, req, 'CRB Approved', 'CRB Deferred', actor, remarks or 'Returned to CRB')
                st.success('Management decision recorded.')
                st.rerun()

def crb_page(actor):
    """Case-based Competency Review Board workspace. CRB is not a standalone account role."""
    st.header('Competency Review Board')
    st.caption('Board participation is assigned on each authorization case. Management participates when assigned; additional permitted board roles can be configured later without creating a CRB Member account role.')
    auths = db_all('authorization_requests')
    if auths.empty:
        st.info('No authorization cases are available.')
        return
    uidv = str(actor_get(actor,'user_id','') or '')
    role = str(actor_get(actor,'role','') or '')
    if table_exists('crb_case_board_assignments'):
        ba = db_where('crb_case_board_assignments','user_id = :uid',(('uid',uidv),))
        ids = set(ba.get('authorization_id', pd.Series(dtype=str)).astype(str).tolist()) if not ba.empty else set()
        enterprise = can_action(actor,'Authorization','Manage','Organization-wide') or can_action(actor,'CRB','Manage','Organization-wide')
        if not enterprise:
            auths = auths[auths.get('authorization_id',pd.Series(dtype=str)).astype(str).isin(ids)]
    else:
        auths = restrict_user_frame(auths, actor)
    if auths.empty:
        st.info('No CRB cases are assigned to you.')
        return
    pending = auths[auths.get('status',pd.Series(dtype=str)).astype(str).isin(['QMS Reviewed','Technical Reviewed','CRB Pending','Ready for CRB'])]
    if pending.empty: pending=auths
    table(pending[[c for c in ['authorization_id','name','scope','status','current_stage','expiry_date'] if c in pending.columns]])
    sel=st.selectbox('Case', pending.apply(_auth_label,axis=1), key='crb_request')
    aid=sel.rsplit(' — ',1)[-1]; req=pending[pending['authorization_id'].astype(str)==aid].iloc[0]
    snapshot=_authorization_snapshot(req); c1,c2,c3,c4=st.columns(4); c1.metric('Training Completed',snapshot['training_completed']); c2.metric('Witness Passed',snapshot['witness_passed']); c3.metric('Supervised Passed',snapshot['supervised_passed']); c4.metric('Open NCR',snapshot['open_ncr'])
    if table_exists('crb_case_board_assignments'):
        board=db_where('crb_case_board_assignments','authorization_id = :aid',(('aid',aid),))
        st.subheader('Assigned Board')
        if board.empty: st.info('The board has not yet been constituted for this case.')
        else: table(board[[c for c in ['system_role','board_role','voting_authority','conflict_declared','attendance_status','decision','comments'] if c in board.columns]])
    decision=st.selectbox('My CRB Decision',['Recommend Approval','Recommend Rejection','Defer','Request Clarification'],key='crb_decision')
    remarks=st.text_area('CRB Remarks',key='crb_remarks')
    if st.button('Record My CRB Decision',type='primary'):
        if table_exists('crb_case_board_assignments'):
            board=db_where('crb_case_board_assignments','authorization_id = :aid AND user_id = :uid',(('aid',aid),('uid',uidv)))
            if board.empty and role not in {'GM','Admin'}:
                st.error('You are not assigned to this CRB case.'); return
            if not board.empty:
                db_update('crb_case_board_assignments','board_assignment_id',str(board.iloc[0]['board_assignment_id']),{'attendance_status':'Present','decision':decision,'comments':remarks,'decided_on':now()})
        audit('CRB Board Decision Recorded',f'{aid}: {decision}',actor=actor,entity_type='authorization_requests',entity_id=aid,reason=remarks or decision)
        st.success('Your case-based CRB decision has been recorded.')

def revalidation_page(actor):
    st.header('Revalidation / Reauthorization')
    st.caption('Revalidation reuses the live evidence already held by Training, CPD, Competency, NCR, Client Feedback and Authorization.')
    if not _authorization_roles(actor, 'revalidation'):
        st.info('Revalidation is restricted to authorized governance roles.')
        return
    auths = db_all('authorization_requests')
    approved = auths[auths['status'].astype(str) == 'Management Approved'] if not auths.empty else pd.DataFrame()
    if approved.empty:
        st.info('No active authorizations are available for revalidation.')
        return
    approved = approved.copy()
    approved['days_to_expiry'] = approved['expiry_date'].astype(str).apply(days_until)
    st.subheader('Authorization Health')
    metrics([('Active', len(approved)), ('Due ≤180d', int((approved['days_to_expiry'] <= 180).sum())), ('Due ≤90d', int((approved['days_to_expiry'] <= 90).sum())), ('Expired', int((approved['days_to_expiry'] < 0).sum()))])
    due = approved[approved['days_to_expiry'] <= 180]
    table(due[[c for c in ['authorization_id', 'name', 'scope', 'expiry_date', 'days_to_expiry', 'certificate_id'] if c in due.columns]])
    reqs = restrict_user_frame(db_all('revalidation_requests'), actor)
    if not due.empty:
        sel = st.selectbox('Authorization for revalidation', due.apply(_auth_label, axis=1), key='reval_auth')
        aid = sel.rsplit(' — ', 1)[-1]
        req = approved[approved['authorization_id'].astype(str) == aid].iloc[0]
        existing = reqs[(reqs['authorization_id'].astype(str) == aid) & reqs['final_status'].astype(str).isin(['Open', 'Under Review', 'Decision Pending'])] if not reqs.empty else pd.DataFrame()
        if existing.empty and st.button('Initiate Revalidation', type='primary'):
            snap = _authorization_snapshot(req)
            rid = uid('REV')
            db_insert('revalidation_requests', {'revalidation_id': rid, 'authorization_id': aid, 'user_id': req['user_id'], 'name': req['name'], 'scope': req['scope'], 'refresher_training_status': 'Pending', 'annual_review_status': 'Pending', 'kpi_review_status': 'Pending', 'tutor_confirmation': 'Pending', 'crb_status': 'Pending', 'final_status': 'Open', 'due_date': req['expiry_date'], 'created_on': now(), 'updated_on': now(), 'initiated_on': now(), 'initiated_by': actor_get(actor, 'name'), 'readiness_status': 'Pending', 'evidence_snapshot': json.dumps(snap, default=str)})
            audit('Revalidation Initiated', f'{aid} / {rid}', actor=actor, entity_type='revalidation_requests', entity_id=rid, reason='Authorization approaching expiry')
            st.success('Revalidation initiated.')
            st.rerun()
        active = reqs[reqs['authorization_id'].astype(str) == aid] if not reqs.empty else pd.DataFrame()
        if not active.empty:
            rv = active.sort_values('created_on').iloc[-1]
            snap = _authorization_snapshot(req)
            cols = st.columns(5)
            cols[0].metric('Training', '%s' % snap['training_completed'])
            cols[1].metric('Witness', '%s' % snap['witness_passed'])
            cols[2].metric('Supervised', '%s' % snap['supervised_passed'])
            cols[3].metric('Open NCR', snap['open_ncr'])
            cols[4].metric('CPD Hours', f"{snap['cpd_hours']:.1f}")
            decision = st.selectbox('Revalidation Decision', ['Revalidate', 'Revalidate with Restrictions', 'Suspend', 'Withdraw'], key='reval_decision')
            reason = st.text_area('Decision Reason', key='reval_reason')
            if st.button('Record Revalidation Decision', type='primary'):
                if decision == 'Revalidate':
                    matrix = get_matrix_for_scope(req['scope'])
                    new_expiry = add_months(int(matrix['validity_months'])) if matrix is not None else add_months(36)
                    db_update('authorization_requests', 'authorization_id', aid, {'status': 'Management Approved', 'expiry_date': new_expiry, 'current_stage': 'Authorized', 'last_reviewed_on': now(), 'updated_on': now(), 'updated_by': actor_get(actor, 'name')})
                    db_update('revalidation_requests', 'revalidation_id', rv['revalidation_id'], {'final_status': 'Completed', 'decision': decision, 'decision_reason': reason, 'decided_by': actor_get(actor, 'name'), 'decided_on': now(), 'readiness_status': 'Eligible', 'updated_on': now()})
                    _authorization_event(aid, req, 'Management Approved', 'Management Approved', actor, reason or 'Revalidated')
                elif decision == 'Revalidate with Restrictions':
                    db_update('revalidation_requests', 'revalidation_id', rv['revalidation_id'], {'final_status': 'Completed', 'decision': decision, 'decision_reason': reason, 'decided_by': actor_get(actor, 'name'), 'decided_on': now(), 'readiness_status': 'Restricted', 'updated_on': now()})
                else:
                    new_status = 'Suspended' if decision == 'Suspend' else 'Withdrawn'
                    db_update('authorization_requests', 'authorization_id', aid, {'status': new_status, 'current_stage': new_status, 'updated_on': now(), 'updated_by': actor_get(actor, 'name')})
                    db_update('revalidation_requests', 'revalidation_id', rv['revalidation_id'], {'final_status': 'Completed', 'decision': decision, 'decision_reason': reason, 'decided_by': actor_get(actor, 'name'), 'decided_on': now(), 'readiness_status': new_status, 'updated_on': now()})
                    _authorization_event(aid, req, 'Management Approved', new_status, actor, reason or decision)
                    cert = db_all('authorization_certificates')
                    if not cert.empty:
                        mine = cert[cert['authorization_id'].astype(str) == aid]
                        for _, row in mine.iterrows():
                            db_update('authorization_certificates', 'certificate_id', row['certificate_id'], {'status': 'Revoked', 'public_status': 'Invalid', 'revoked_on': now(), 'revocation_reason': reason or decision})
                            _certificate_history(str(row['certificate_id']), str(row.get('authorization_id','')), str(row.get('user_id','')), str(row.get('status','')), 'Revoked', 'Revoked', actor, reason or decision)
                st.success('Revalidation decision recorded.')
                st.rerun()
    st.subheader('Revalidation History')
    table(reqs.sort_values('created_on', ascending=False) if not reqs.empty and 'created_on' in reqs.columns else reqs)

def technical_authority_page(actor):
    st.header('Technical Authority')
    st.caption('Technical Authority is a scoped review stage in the authorization lifecycle, not a second authorization system.')
    if not can_action(actor, 'Technical Authority', 'Review', 'Organization-wide') and (not can_action(actor, 'Technical Authority', 'Manage', 'Organization-wide')):
        st.info('Technical Authority administration/review is restricted to authorized technical roles.')
        return
    tabs = st.tabs(['Assignments', 'Authorization Reviews', 'History'])
    with tabs[0]:
        if can_action(actor, 'Technical Authority', 'Manage', 'Organization-wide') or can_action(actor, 'Technical Authority', 'Approve', 'Organization-wide'):
            with st.form('ta'):
                name, uidv, _ = select_person('Authority Person', ['Department Manager', 'QMS Auditor', 'Management'], key='ta_person')
                discipline = st.selectbox('Discipline', ['Hull', 'Machinery', 'Electrical', 'Statutory', 'Plan Approval', 'Audit', 'Industrial', 'Rule Development'])
                level = st.selectbox('Authority Level', ['Discipline Expert', 'Principal', 'Head of Discipline', 'Technical Authority'])
                limit = st.text_area('Approval Limit')
                scope = st.text_input('Decision Scope', 'Defined by authorization scope and delegated authority.')
                c1, c2 = st.columns(2)
                eff = c1.date_input('Effective From', date.today())
                exp = c2.date_input('Effective To', date.today() + timedelta(days=3650))
                remarks = st.text_area('Remarks')
                if st.form_submit_button('Appoint Technical Authority', type='primary') and uidv:
                    db_insert('technical_authorities', {'authority_id': uid('TA'), 'user_id': uidv, 'name': name, 'discipline': discipline, 'authority_level': level, 'approval_limit': limit, 'decision_scope': scope, 'active': 'Yes', 'appointed_by': actor_get(actor, 'name'), 'appointed_on': today(), 'effective_from': str(eff), 'effective_to': str(exp), 'remarks': remarks})
                    audit('Technical Authority Appointed', f'{name} / {discipline}', actor=actor, entity_type='technical_authorities', entity_id=uidv, reason=remarks)
                    st.success('Technical authority appointed.')
                    st.rerun()
    with tabs[1]:
        auths = db_all('authorization_requests')
        pending = auths[auths['status'].astype(str) == 'Principal Reviewed'] if not auths.empty else pd.DataFrame()
        if pending.empty:
            st.info('No authorization requests are awaiting Technical Authority review.')
        else:
            table(pending[[c for c in ['authorization_id', 'name', 'scope', 'job_type', 'status', 'risk_category'] if c in pending.columns]])
            sel = st.selectbox('Request', pending.apply(_auth_label, axis=1), key='ta_auth_req')
            aid = sel.rsplit(' — ', 1)[-1]
            req = pending[pending['authorization_id'].astype(str) == aid].iloc[0]
            decision = st.selectbox('Technical Decision', ['Approved', 'Approved with Conditions', 'Rejected', 'Return for Clarification'], key='ta_decision')
            remarks = st.text_area('Technical Review Remarks', key='ta_remarks')
            if st.button('Record Technical Review', type='primary'):
                new_status = 'Technical Reviewed' if decision in ['Approved', 'Approved with Conditions'] else 'Trainer Recommended' if decision == 'Return for Clarification' else 'Withdrawn'
                db_update('authorization_requests', 'authorization_id', aid, {'status': new_status, 'current_stage': 'QMS Review' if new_status == 'Technical Reviewed' else _auth_stage(new_status), 'technical_remarks': remarks, 'technical_signature': actor_get(actor, 'name'), 'technical_signed_on': now(), 'last_reviewed_on': now(), 'updated_on': now(), 'updated_by': actor_get(actor, 'name')})
                _authorization_event(aid, req, req['status'], new_status, actor, remarks or f'Technical decision: {decision}')
                st.success('Technical review recorded.')
                st.rerun()
    with tabs[2]:
        table(db_all('technical_authorities'))

def annual_competency_board_page(actor):
    st.header('Annual Authorization & Competency Review')
    st.caption('Annual review consumes live evidence from existing systems; reviewers record only the governance decision.')
    if not (can_action(actor, 'Annual Review', 'Review', 'Department') or can_action(actor, 'Annual Review', 'Review', 'Organization-wide') or can_action(actor, 'Annual Review', 'Approve', 'Organization-wide')):
        st.info('Annual review is restricted to authorized governance/review permissions.')
        return
    users = db_all('users')
    auths = db_all('authorization_requests')
    if users.empty:
        st.info('No employees available.')
        return
    name, uidv, u = select_person('Person', ['Surveyor', 'Plan Appraiser', 'QMS Auditor', 'Industrial Surveyor', 'Rule Development Rep', 'Trainee', 'On Probation'], key='annual_person')
    if not uidv:
        return
    scope = st.selectbox('Scope', SCOPES, key='annual_scope')
    year = st.number_input('Review Year', 2020, 2100, date.today().year, key='annual_year')
    train = db_all('training_records')
    t = train[train['user_id'].astype(str) == uidv] if not train.empty else pd.DataFrame()
    comp = db_all('competency_matrix')
    c = comp[(comp['user_id'].astype(str) == uidv) & (comp['scope'].astype(str) == scope)] if not comp.empty else pd.DataFrame()
    auth = auths[(auths['user_id'].astype(str) == uidv) & (auths['scope'].astype(str) == scope)] if not auths.empty else pd.DataFrame()
    ncr = db_all('competency_ncrs')
    n = ncr[(ncr['user_id'].astype(str) == uidv) & ~ncr['status'].astype(str).str.casefold().isin(['closed', 'rejected', 'cancelled'])] if not ncr.empty else pd.DataFrame()
    cpd = db_all('cpd_records')
    cp = cpd[cpd['user_id'].astype(str) == uidv] if not cpd.empty else pd.DataFrame()
    fb = db_all('client_feedback')
    f = fb[fb['user_id'].astype(str) == uidv] if not fb.empty else pd.DataFrame()
    snap = {'Training': f"{int(t.get('status', pd.Series(dtype=str)).astype(str).isin(['Completed', 'Passed']).sum())}/{len(t)} complete" if not t.empty else 'No records', 'Competency': str(c.iloc[-1].get('status', 'Pending')) if not c.empty else 'No scope record', 'Authorization': str(auth.iloc[-1].get('status', 'None')) if not auth.empty else 'None', 'Open NCR': str(len(n)), 'CPD Hours': f"{float(pd.to_numeric(cp.get('hours', pd.Series(dtype=float)), errors='coerce').fillna(0).sum()):.1f}", 'Client Feedback': f"{float(pd.to_numeric(f.get('rating', pd.Series(dtype=float)), errors='coerce').fillna(0).mean()):.1f}/5" if not f.empty else 'No feedback'}
    st.subheader('Evidence Snapshot')
    cols = st.columns(len(snap))
    for col, (k, v) in zip(cols, snap.items()):
        col.metric(k, v)
    decision = st.selectbox('Board Decision', ['Maintain', 'Upgrade', 'Restrict', 'Suspend', 'Withdraw', 'Additional Training'], key='annual_decision')
    remarks = st.text_area('Board Remarks', key='annual_remarks')
    if st.button('Record Annual Decision', type='primary'):
        existing = db_all('annual_reviews')
        dup = existing[(existing['user_id'].astype(str) == uidv) & (existing['scope'].astype(str) == scope) & (existing['review_year'].astype(str) == str(int(year)))] if not existing.empty else pd.DataFrame()
        payload = {'review_id': dup.iloc[0]['review_id'] if not dup.empty else uid('AR'), 'user_id': uidv, 'name': name, 'scope': scope, 'review_year': int(year), 'training_status': snap['Training'], 'kpi_status': 'Auto-reviewed', 'complaint_status': 'Auto-reviewed', 'capa_status': str(len(n)), 'decision': decision, 'reviewer': actor_get(actor, 'name'), 'review_date': today(), 'remarks': remarks, 'training_summary': snap['Training'], 'competency_summary': snap['Competency'], 'authorization_summary': snap['Authorization'], 'ncr_summary': snap['Open NCR'], 'cpd_summary': snap['CPD Hours'], 'client_feedback_summary': snap['Client Feedback']}
        if dup.empty:
            db_insert('annual_reviews', payload)
        else:
            db_update('annual_reviews', 'review_id', payload['review_id'], payload)
        audit('Annual Authorization Review Recorded', f'{uidv}/{scope}/{int(year)} → {decision}', actor=actor, entity_type='annual_reviews', entity_id=payload['review_id'], reason=remarks, after_value=decision)
        st.success('Annual review recorded.')
        st.rerun()
    history = db_all('annual_reviews')
    mine = history[(history['user_id'].astype(str) == uidv) & (history['scope'].astype(str) == scope)] if not history.empty else history
    st.subheader('Review History')
    table(mine.sort_values('review_year', ascending=False) if not mine.empty and 'review_year' in mine.columns else mine)

def authorization_restrictions_page(actor):
    st.header('Authorization Restrictions')
    st.caption('Restrictions are attached to an authorization and are enforced by job allocation; they are not a separate authorization record.')
    auths = db_all('authorization_requests')
    approved = auths[auths['status'].astype(str) == 'Management Approved'] if not auths.empty else pd.DataFrame()
    if _authorization_roles(actor, 'restrict') and (not approved.empty):
        with st.form('res'):
            sel = st.selectbox('Authorization', approved.apply(_auth_label, axis=1))
            aid = sel.rsplit(' — ', 1)[-1]
            auth = approved[approved['authorization_id'].astype(str) == aid].iloc[0]
            rtype = st.selectbox('Restriction Type', ['Scope Limit', 'Complexity Limit', 'Power/Capacity Limit', 'Only Under Supervision', 'Audit Type Limit', 'Temporary Restriction', 'Other'])
            detail = st.text_area('Restriction Detail')
            eff = st.date_input('Effective Date', date.today())
            exp = st.date_input('Expiry Date', date.today() + timedelta(days=365))
            reason = st.text_area('Reason')
            if st.form_submit_button('Add Restriction', type='primary'):
                db_insert('authorization_restrictions', {'restriction_id': uid('RES'), 'authorization_id': aid, 'user_id': auth['user_id'], 'name': auth['name'], 'scope': auth['scope'], 'restriction_type': rtype, 'restriction_detail': detail, 'effective_date': str(eff), 'expiry_date': str(exp), 'status': 'Active', 'imposed_by': actor_get(actor, 'name'), 'reason': reason, 'created_on': now()})
                audit('Authorization Restriction Added', f'{aid}: {rtype}', actor=actor, entity_type='authorization_restrictions', entity_id=aid, reason=reason, after_value=detail)
                st.success('Restriction added.')
                st.rerun()
    restrictions = db_all('authorization_restrictions')
    if restrictions.empty:
        st.info('No authorization restrictions recorded.')
    else:
        table(restrictions.sort_values('created_on', ascending=False) if 'created_on' in restrictions.columns else restrictions)
        active = restrictions[restrictions['status'].astype(str) == 'Active']
        if _authorization_roles(actor, 'restrict') and (not active.empty):
            sel = st.selectbox('Active restriction', active['restriction_id'].astype(str), key='res_revoke')
            reason = st.text_area('Revocation reason', key='res_rev_reason')
            if st.button('Revoke Restriction', type='primary'):
                db_update('authorization_restrictions', 'restriction_id', sel, {'status': 'Revoked', 'revoked_on': now(), 'revoked_by': actor_get(actor, 'name'), 'revoked_reason': reason})
                audit('Authorization Restriction Revoked', sel, actor=actor, entity_type='authorization_restrictions', entity_id=sel, reason=reason, after_value='Revoked')
                st.success('Restriction revoked.')
                st.rerun()
