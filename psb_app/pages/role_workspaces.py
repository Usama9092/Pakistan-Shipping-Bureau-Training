from core.access_policy import allowed_disciplines
from core.view_context import context_for
from psb_app.common import (
    actor_get,
    audit,
    can_action,
    date,
    datetime,
    days_until,
    db_all,
    db_insert,
    db_update,
    db_where,
    now,
    pd,
    restrict_user_frame,
    st,
    table_exists,
    timedelta,
    today,
    uuid,
)


def _id(actor):
    return str(actor_get(actor, 'user_id', '') or '')


def _scoped(df, actor):
    return restrict_user_frame(df, actor) if df is not None else pd.DataFrame()


def _match_any(df, columns, user_id):
    if df.empty:
        return df
    mask = pd.Series(False, index=df.index)
    for col in columns:
        if col in df.columns:
            mask = mask | df[col].astype(str).eq(str(user_id))
    return df[mask].copy()

def _assigned_people(actor, relationship_type: str):
    users = db_all('users')
    if users.empty:
        return users
    uidv=_id(actor); role=str(actor_get(actor,'role','') or '')
    id_col={'Trainer':'trainer_id'}.get(role)
    if not id_col:
        return users.iloc[0:0].copy()
    mask=users.get(id_col,pd.Series('',index=users.index)).astype(str).eq(uidv)
    try:
        assigns=db_all('user_assignments')
        if not assigns.empty:
            m=assigns.get('assignment_type',pd.Series('',index=assigns.index)).astype(str).str.casefold().eq(relationship_type.casefold())
            m=m & assigns.get('assigned_user_id',pd.Series('',index=assigns.index)).astype(str).eq(uidv)
            ids=set(assigns.loc[m,'user_id'].astype(str).tolist()) if 'user_id' in assigns.columns else set()
            if ids:
                mask=mask | users.get('user_id',pd.Series('',index=users.index)).astype(str).isin(ids)
    except Exception:
        pass
    return users[mask].copy()

def _open_assigned_profile(actor, users, title, key_prefix):
    st.header(title)
    if users.empty:
        st.info('No people are currently assigned to you.')
        return
    opts=[f"{r.get('name','')} — {r.get('employee_id',r.get('user_id',''))} — {r.get('user_id','')}" for _,r in users.iterrows()]
    chosen=st.selectbox('Select person',opts,key=f'{key_prefix}_select')
    selected_uid=chosen.rsplit(' — ',1)[-1]
    row=users[users['user_id'].astype(str).eq(selected_uid)].iloc[0]
    a,b,c,d=st.columns(4); a.metric('Name',row.get('name','—')); b.metric('Role',row.get('role','—')); c.metric('Department',row.get('primary_department',row.get('department','—'))); d.metric('Availability',row.get('availability','—'))
    st.caption('This workspace is restricted to explicitly assigned people. Employee Profile remains the single 360° source of truth.')
    selected_uid_frame = users[users['user_id'].astype(str).eq(selected_uid)]
    try:
        uidv = selected_uid
        tr = db_where('training_records', 'user_id = :uid', (('uid', uidv),))
        cp = db_where('competency_matrix', 'user_id = :uid', (('uid', uidv),))
        jobs = db_where('job_requests', 'assigned_user_id = :uid', (('uid', uidv),)) if table_exists('job_requests') else pd.DataFrame()
        a,b,c = st.columns(3)
        a.metric('Training Due/Open', int(len(tr[tr.get('status', pd.Series(dtype=str)).astype(str).isin(['Assigned','In Progress','Pending','Due'])])) if not tr.empty else 0)
        b.metric('Competency Gaps', int(len(cp[~cp.get('status', pd.Series(dtype=str)).astype(str).isin(['Approved','Competent','Current'])])) if not cp.empty else 0)
        c.metric('Open Jobs', int(len(jobs[jobs.get('status', pd.Series(dtype=str)).astype(str).isin(['Assigned','In Progress'])])) if not jobs.empty else 0)
    except Exception:
        pass
    if st.button('Open Employee Profile',type='primary',key=f'{key_prefix}_open'):
        st.session_state['profile_target_user_id']=selected_uid
        st.session_state['psb_current_page']='Employee Profile'
        st.rerun()

def assigned_learners_page(actor):
    _open_assigned_profile(actor,_assigned_people(actor,'Trainer'),'Assigned Learners','trainer_assigned')

def assigned_trainees_page(actor):
    _open_assigned_profile(actor,_assigned_people(actor,'Trainer'),'Assigned Learners','trainer_assigned')

def my_authorization_page(actor):
    st.header('My Authorization')
    st.caption('Your authorization status, evidence readiness, restrictions and expiry. You cannot approve your own authorization.')
    authorization_page(actor)

def my_performance_page(actor):
    """Self-service performance view; never exposes enterprise KPI filters or other people."""
    st.header('My Performance')
    st.caption('Your evidence-derived performance scorecard. This view is strictly self-scoped; source records remain authoritative in their existing modules.')
    uid = _id(actor)
    users = db_where('users', 'user_id = :uid', (('uid', uid),))
    if users.empty:
        st.info('Your employee profile is not available.')
        return
    user = users.iloc[0]
    period = st.selectbox('Performance Period', [str((datetime.now()-pd.DateOffset(months=i)).strftime('%Y-%m')) for i in range(6)], key='my_perf_period')
    try:
        snap = _calculate_performance_snapshot(user, period)
    except Exception:
        snap = {}
    if not snap:
        st.info('No performance data is currently available for this period.')
        return
    c1,c2,c3 = st.columns(3)
    c1.metric('Overall Score', f"{float(snap.get('overall_score',0) or 0):.0f}%")
    c2.metric('Status', str(snap.get('status','—')))
    c3.metric('Calculation Version', str(snap.get('calculation_version','—')))
    st.subheader('My Evidence Scorecard')
    metrics_data=[('Training','training_score'),('Competency','competency_score'),('Authorization','authorization_score'),('Technical Review','technical_review_score'),('QMS','quality_score'),('Delivery','delivery_score'),('Client Feedback','client_feedback_score'),('NCR/CAPA','ncr_score'),('Utilization','utilization_score')]
    cols=st.columns(3)
    for i,(label,key) in enumerate(metrics_data):
        cols[i%3].metric(label, f"{float(snap.get(key,0) or 0):.0f}%")
    st.divider()
    st.subheader('Performance Interpretation')
    st.write(f"Your current performance status is **{snap.get('status','—')}** for **{period}**.")
    st.info('Performance is calculated from authoritative Training, Competency, Authorization, Technical Review, QMS, Job, Client Feedback and NCR/CAPA records. You cannot edit KPI values here.')


def probation_progress_page(actor):
    """Unified probation progress board composed from authoritative source records."""
    st.header('Probation Progress')
    st.caption('A single progress board combining objectives, training, competency, Trainer assessment, performance and probation decision. Source records remain authoritative in their existing modules.')
    role = str(actor_get(actor, 'role', '') or '')
    view_ctx = context_for(role, 'Probation Progress')
    uidv = _id(actor)
    reviews = db_all('probation_reviews')
    if view_ctx == 'Own':
        reviews = reviews[reviews.get('user_id', pd.Series(dtype=str)).astype(str).eq(uidv)] if not reviews.empty else reviews
    elif view_ctx == 'Assigned':
        assigned = _assigned_people(actor, 'Trainer')
        ids = set(assigned.get('user_id', pd.Series(dtype=str)).astype(str).tolist()) if not assigned.empty else set()
        reviews = reviews[reviews.get('user_id', pd.Series(dtype=str)).astype(str).isin(ids)] if not reviews.empty else reviews
    else:
        reviews = _scoped(reviews, actor) if not reviews.empty else reviews
    if reviews.empty:
        st.info('No probation progress records are available for your current scope.')
        return
    if view_ctx == 'Assigned':
        options=[f"{r.get('name','')} — {r.get('user_id','')}" for _,r in reviews.iterrows()]
        pick=st.selectbox('Probationer', options, key='probation_progress_person')
        target_uid=pick.rsplit(' — ',1)[-1]
        target_reviews=reviews[reviews['user_id'].astype(str).eq(target_uid)]
        latest=target_reviews.sort_values('review_date', ascending=False).iloc[0] if 'review_date' in target_reviews.columns else target_reviews.iloc[0]
    else:
        latest=reviews.sort_values('review_date', ascending=False).iloc[0] if 'review_date' in reviews.columns else reviews.iloc[0]
        target_uid=str(latest.get('user_id',''))

    def _count(table, success_values):
        try:
            df=db_where(table, 'user_id = :uid', (('uid', target_uid),))
            if df.empty: return (0,0)
            status=df.get('status', pd.Series('', index=df.index)).astype(str)
            return (len(df), int(status.isin(success_values).sum()))
        except Exception:
            return (0,0)

    tr_total,tr_done=_count('training_records', {'Completed','Complete'})
    cp_total,cp_done=_count('competency_matrix', {'Approved','Competent','Current'})
    wit_total,wit_done=_count('witness_surveys', {'Passed','Pass','Approved','Completed'})
    try:
        perf=db_where('kpi_snapshots', 'user_id = :uid', (('uid', target_uid),))
        perf=perf.sort_values('period_end', ascending=False) if not perf.empty and 'period_end' in perf.columns else perf
        score=float(perf.iloc[0].get('overall_score')) if not perf.empty and str(perf.iloc[0].get('overall_score','')).strip() else None
    except Exception:
        score=None

    objective_ready=bool(str(latest.get('objectives','') or '').strip())
    tutor_ready=bool(str(latest.get('tutor_assessment','') or '').strip())
    decision=str(latest.get('decision','Pending') or 'Pending')
    completed_blocks=sum([tr_done==tr_total and tr_total>0, cp_done==cp_total and cp_total>0, wit_done==wit_total and wit_total>0, objective_ready, tutor_ready, score is not None])
    total_blocks=6
    percent=int(round(100*completed_blocks/total_blocks))
    if decision in {'Confirm','Confirmed'}:
        band='Ready / Confirmed'
    elif decision in {'Not Confirmed','Extend'}:
        band='Decision Required'
    elif percent >= 80:
        band='On Track'
    elif percent >= 50:
        band='Needs Attention'
    else:
        band='At Risk'

    st.markdown(f"### {latest.get('name','—')} · {band}")
    metrics([
        ('Progress', f'{percent}%'),
        ('Training', f'{tr_done}/{tr_total}'),
        ('Competency', f'{cp_done}/{cp_total}'),
        ('Witness', f'{wit_done}/{wit_total}'),
        ('Performance', '—' if score is None else f'{score:.1f}'),
        ('Decision', decision),
    ])
    st.markdown('### Progress Gates')
    gate_rows=[
        ('Objectives', 'Ready' if objective_ready else 'Missing', 'Probation review objectives recorded'),
        ('Training', 'Ready' if tr_total and tr_done==tr_total else 'In Progress', f'{tr_done} of {tr_total} complete'),
        ('Competency', 'Ready' if cp_total and cp_done==cp_total else 'In Progress', f'{cp_done} of {cp_total} current'),
        ('Practical / Witness', 'Ready' if wit_total and wit_done==wit_total else 'In Progress', f'{wit_done} of {wit_total} passed/complete'),
        ('Performance', 'Ready' if score is not None else 'Missing', 'Latest KPI snapshot available' if score is not None else 'No KPI snapshot available'),
        ('Trainer Assessment', 'Ready' if tutor_ready else 'Missing', 'Trainer assessment recorded' if tutor_ready else 'Trainer assessment pending'),
    ]
    table(pd.DataFrame(gate_rows, columns=['Gate','Status','Evidence']))
    st.markdown('### Probation Timeline')
    timeline=[('Start',latest.get('probation_start','—')),('Review',latest.get('review_date','—')),('End',latest.get('probation_end','—')),('Decision',decision)]
    table(pd.DataFrame(timeline, columns=['Milestone','Value']))
    if view_ctx == 'Own':
        st.info('This is a read-only personal progress view. Review and decision actions remain with authorized reviewers.')
    else:
        st.caption('Reviewer view: use the linked source modules for detailed evidence and the Probation Review workflow for formal decisions.')

def certificates_page(actor):
    is_enterprise = can_action(actor,'Authorization','Manage','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
    st.header('Certificate Center' if is_enterprise else 'My Certificates')
    certs=_scoped(db_all('authorization_certificates'),actor)
    if certs.empty:
        st.info('No certificates are available for your current scope.')
        return
    certs=certs.copy(); status_cf=certs.get('status',pd.Series('',index=certs.index)).astype(str).str.strip().str.casefold(); days=certs.get('expiry_date',pd.Series('',index=certs.index)).astype(str).map(days_until); certs['days_to_expiry']=days
    revoked=status_cf.isin(['revoked','suspended','withdrawn','invalid']); replaced=status_cf.isin(['replaced','superseded']); expired=(days < 0) & ~revoked & ~replaced; active=(status_cf.eq('valid')) & (days >= 0) & ~revoked & ~replaced; expiring=(days >= 0)&(days<=90)&active
    metrics([('Active',int(active.sum())),('Expiring ≤90d',int(expiring.sum())),('Suspended/Revoked',int(revoked.sum())),('Expired',int(expired.sum()))])
    tabs=st.tabs(['Active','Expired','Suspended / Revoked','Replaced','History','Verify'])
    def show(mask):
        frame=certs[mask].copy()
        if frame.empty: st.info('Nothing to display in this view.'); return
        cols=[c for c in ['certificate_id','authorization_id','name','scope','job_type','issue_date','expiry_date','status','verification_url'] if c in frame.columns]
        table(frame[cols].sort_values('issue_date',ascending=False) if 'issue_date' in frame.columns else frame[cols],max_rows=200)
        ids=frame['certificate_id'].astype(str).tolist() if 'certificate_id' in frame.columns else []
        if ids:
            chosen=st.selectbox('Certificate detail',['—']+ids,key=f"cert_detail_{len(ids)}_{str(mask.sum())}")
            if chosen!='—':
                row=frame[frame['certificate_id'].astype(str).eq(chosen)].iloc[0]
                a,b,c=st.columns(3); a.metric('Status',row.get('status','—')); b.metric('Issue Date',row.get('issue_date','—')); c.metric('Expiry',row.get('expiry_date','—'))
                if row.get('verification_url'): st.link_button('Open Public Verification',str(row.get('verification_url')))
    with tabs[0]: show(active)
    with tabs[1]: show(expired)
    with tabs[2]: show(revoked)
    with tabs[3]: show(replaced)
    with tabs[4]:
        history = db_all('authorization_certificate_history')
        if history.empty:
            st.info('No certificate history is available for your current scope.')
        else:
            if 'certificate_id' in history.columns and 'certificate_id' in certs.columns:
                allowed=set(certs['certificate_id'].astype(str))
                history=history[history['certificate_id'].astype(str).isin(allowed)]
            cols=[c for c in ['certificate_id','event_type','from_status','to_status','reason','actor_name','event_on'] if c in history.columns]
            table(history[cols].sort_values('event_on',ascending=False) if 'event_on' in history.columns else history[cols], max_rows=300)
    with tabs[5]:
        cert_id=st.text_input('Certificate ID',key='certificate_center_verify')
        if cert_id.strip() and st.button('Verify Certificate',type='primary',key='certificate_center_verify_btn'):
            row=certs[certs.get('certificate_id',pd.Series(dtype=str)).astype(str).eq(cert_id.strip())]
            if row.empty: st.error('Certificate not found within your accessible records.')
            else:
                r=row.iloc[0]; valid=bool(active.loc[r.name]); st.success('Certificate is currently valid.') if valid else st.warning(f"Certificate status: {r.get('status','Unknown')}"); st.write({'Certificate':r.get('certificate_id',''),'Holder':r.get('name',''),'Scope':r.get('scope',''),'Expiry':r.get('expiry_date',''),'Status':r.get('status','')})


def my_technical_reviews_page(actor):
    """Assigned technical-review workspace backed by explicit assignment records.

    The technical_reviews table remains the single source of review content.
    technical_review_assignments owns assignment lifecycle/history.
    """
    st.header('My Technical Reviews')
    st.caption('Assigned technical-review work from the unified Technical Reviews register.')
    reviews = db_all('technical_reviews')
    assignments = db_all('technical_review_assignments')
    uidv = _id(actor)
    if reviews.empty:
        st.info('No technical reviews are available.')
        return
    if assignments.empty:
        st.info('No technical reviews are currently assigned to you.')
        return
    # Only current assignments grant the self-service work view. Historical review authorship is not sufficient.
    if 'status' in assignments.columns:
        active_assignments = assignments[~assignments['status'].astype(str).isin(['Released', 'Completed', 'Cancelled'])].copy()
    else:
        active_assignments = assignments.copy()
    mine = active_assignments[active_assignments.get('assigned_reviewer_id', pd.Series(dtype=str)).astype(str).eq(uidv)].copy() if 'assigned_reviewer_id' in active_assignments.columns else active_assignments.iloc[0:0].copy()
    if mine.empty:
        st.info('No technical reviews are currently assigned to you.')
        return
    ids = mine.get('review_id', pd.Series(dtype=str)).astype(str).tolist()
    scoped = reviews[reviews.get('review_id', pd.Series(dtype=str)).astype(str).isin(ids)].copy()
    if 'discipline' in scoped.columns:
        allowed = allowed_disciplines(str((actor or {}).get('role','')))
        if 'All Technical' not in allowed and allowed:
            scoped = scoped[scoped['discipline'].fillna('').astype(str).isin(allowed)]
    if scoped.empty:
        st.info('Your current technical-review assignments have no matching review records.')
        return
    # Join assignment metadata without duplicating the review source record.
    ameta = mine[['review_id','assignment_id','assigned_on','due_date','status']].copy() if all(c in mine.columns for c in ['review_id','assignment_id','assigned_on','due_date','status']) else mine.copy()
    scoped = scoped.merge(ameta, on='review_id', how='left', suffixes=('','_assignment'))
    metrics([('Assigned Reviews', len(scoped)), ('Open', int(scoped.get('status', pd.Series(dtype=str)).astype(str).isin(['Open','In Progress','Under Review']).sum())), ('Due Soon', int(((scoped.get('due_date', pd.Series(dtype=str)).astype(str) != '') & (scoped.get('due_date', pd.Series(dtype=str)).astype(str) <= today())).sum()))])
    filters = st.columns(3)
    typ = filters[0].selectbox('Review Type', ['All'] + sorted(scoped.get('review_type', pd.Series(dtype=str)).astype(str).unique().tolist()), key='my_tech_type')
    status = filters[1].selectbox('Status', ['All'] + sorted(scoped.get('status', pd.Series(dtype=str)).astype(str).unique().tolist()), key='my_tech_status')
    search = filters[2].text_input('Search', key='my_tech_search')
    view = scoped.copy()
    if typ != 'All': view = view[view['review_type'].astype(str) == typ]
    if status != 'All': view = view[view['status'].astype(str) == status]
    if search:
        blob = view.fillna('').astype(str).agg(' | '.join, axis=1).str.casefold()
        view = view[blob.str.contains(search.casefold(), regex=False)]
    cols = [c for c in ['review_id','review_type','name','subject_name','scope','status','decision','overall_score','assigned_on','due_date'] if c in view.columns]
    table(view[cols].sort_values('assigned_on', ascending=False) if 'assigned_on' in view.columns else view[cols], max_rows=200)

def audit_workspace_page(actor, audit_id=None):
    """True audit workspace for an assigned QMS/lead-auditor audit.

    It composes the existing QMS audit record with evidence, findings/NCRs,
    corrective actions and closure status. It never creates duplicate audit
    records; QMS audits, NCR/CAPA and evidence reviews remain authoritative.
    """
    st.header('Audit Workspace')
    st.caption('Single audit workspace: scope → evidence → findings/NCR → corrective action → verification → closure. Source records remain in QMS, NCR/CAPA and Evidence Review.')
    audits = db_all('qms_audits')
    if audits.empty:
        st.info('No audits are currently registered.')
        return
    uidv = _id(actor)
    assigned = _match_any(audits, ['lead_auditor_id','assigned_auditor_id'], uidv)
    if assigned.empty and not (can_action(actor,'QMS','View','Organization-wide') or can_action(actor,'QMS','Manage','Organization-wide')):
        st.info('No audits are assigned to you.')
        return
    view = assigned if not assigned.empty else audits
    ids = view['audit_id'].astype(str).tolist() if 'audit_id' in view.columns else []
    if not ids:
        st.info('No audit identifiers are available.')
        return
    selected = audit_id or st.selectbox('Audit', ids, key='audit_workspace_select')
    if selected not in ids:
        st.warning('The selected audit is outside your current scope.')
        return
    row = view[view['audit_id'].astype(str).eq(str(selected))].iloc[0]
    audit_key = str(selected)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Status', row.get('status','—')); c2.metric('Result', row.get('overall_result','—')); c3.metric('Planned', row.get('planned_date','—')); c4.metric('Completed', row.get('completed_date','—'))
    st.markdown(f"### {audit_key} · {row.get('audit_type','—')}")
    a,b = st.columns(2)
    with a:
        st.write({'Standard':row.get('standard','—'),'Department':row.get('department','—'),'Audit Scope':row.get('audit_scope','—')})
    with b:
        st.write({'Objective':row.get('objective','—'),'Lead Auditor':row.get('lead_auditor_name','—'),'Assigned Auditor':row.get('assigned_auditor_name','—')})

    evidence = db_where('qms_evidence_reviews', 'source_module = :source_module and source_record_id = :source_record_id', (('source_module','QMS Audit'),('source_record_id',audit_key))) if table_exists('qms_evidence_reviews') else pd.DataFrame()
    ncr_all = db_all('competency_ncrs')
    if ncr_all.empty:
        findings = ncr_all
    else:
        src = ncr_all.get('source', pd.Series('', index=ncr_all.index)).astype(str).str.casefold()
        rid = ncr_all.get('source_record_id', pd.Series('', index=ncr_all.index)).astype(str)
        findings = ncr_all[src.isin(['qms audit','audit','qms']) & rid.eq(audit_key)].copy()

    tabs = st.tabs(['Scope & Plan','Evidence','Findings / NCR','Corrective Actions','Verification & Closure'])
    with tabs[0]:
        st.subheader('Audit Scope & Plan')
        st.write({'Audit Type':row.get('audit_type','—'),'Standard':row.get('standard','—'),'Scope':row.get('audit_scope','—'),'Objective':row.get('objective','—'),'Planned Date':row.get('planned_date','—')})
        if row.get('report_summary'): st.info(str(row.get('report_summary')))
    with tabs[1]:
        st.subheader('Evidence Review')
        if evidence.empty:
            st.info('No evidence-review records are linked to this audit yet.')
        else:
            cols=[c for c in ['evidence_review_id','source_module','source_record_id','decision','comments','reviewer_name','reviewed_on'] if c in evidence.columns]
            table(evidence[cols] if cols else evidence,max_rows=200)
    with tabs[2]:
        st.subheader('Findings / NCR')
        if findings.empty:
            st.success('No NCR/finding records are currently linked to this audit.')
        else:
            cols=[c for c in ['ncr_id','severity','priority','description','status','due_date','owner_name','corrective_action'] if c in findings.columns]
            table(findings[cols] if cols else findings,max_rows=200)
    with tabs[3]:
        st.subheader('Corrective Actions')
        if findings.empty:
            st.info('Corrective actions are created and maintained in the enterprise NCR/CAPA workflow.')
        else:
            cols=[c for c in ['ncr_id','corrective_action','owner_name','due_date','status','verification_notes'] if c in findings.columns]
            table(findings[cols] if cols else findings,max_rows=200)
        st.caption('No duplicate corrective-action store is created here; NCR/CAPA remains the source of truth.')
    with tabs[4]:
        st.subheader('Verification & Closure')
        open_findings = int(findings.get('status', pd.Series(dtype=str)).astype(str).isin(['Open','Containment','Root Cause','Corrective Action','Verification','Effectiveness Review']).sum()) if not findings.empty else 0
        evidence_open = int(evidence.get('decision', pd.Series(dtype=str)).astype(str).isin(['','Pending','Open']).sum()) if not evidence.empty else 0
        c1,c2,c3 = st.columns(3); c1.metric('Open Findings',open_findings); c2.metric('Open Evidence Reviews',evidence_open); c3.metric('Audit Status',row.get('status','—'))
        if open_findings == 0 and evidence_open == 0 and str(row.get('status','')) == 'Completed':
            st.success('Audit workspace indicates closure readiness: no open findings/evidence reviews and audit is completed.')
        else:
            st.warning('Audit is not yet closure-ready. Resolve open findings/evidence reviews and complete the audit result in QMS.')
        if can_action(actor,'QMS','Manage','Organization-wide') or str(row.get('lead_auditor_id','')) == uidv:
            st.markdown('#### Update audit outcome')
            r1,r2 = st.columns(2)
            new_status = r1.selectbox('Status',['Planned','In Progress','Under Review','Completed','Cancelled'],index=['Planned','In Progress','Under Review','Completed','Cancelled'].index(str(row.get('status','Planned'))) if str(row.get('status','Planned')) in ['Planned','In Progress','Under Review','Completed','Cancelled'] else 0,key=f'audit_ws_status_{audit_key}')
            result = r2.selectbox('Overall Result',['','Conforming','Minor Findings','Major Findings','Unsatisfactory'],index=['','Conforming','Minor Findings','Major Findings','Unsatisfactory'].index(str(row.get('overall_result',''))) if str(row.get('overall_result','')) in ['','Conforming','Minor Findings','Major Findings','Unsatisfactory'] else 0,key=f'audit_ws_result_{audit_key}')
            summary = st.text_area('Audit report summary',value=str(row.get('report_summary','') or ''),key=f'audit_ws_summary_{audit_key}')
            if st.button('Save Audit Outcome',type='primary',key=f'audit_ws_save_{audit_key}'):
                before=str(row.get('status','')); completed=str(date.today()) if new_status == 'Completed' else str(row.get('completed_date',''))
                db_update('qms_audits','audit_id',audit_key,{'status':new_status,'overall_result':result,'report_summary':summary.strip(),'completed_date':completed,'updated_on':now()})
                audit('QMS Audit Updated',f'{audit_key}: {before} -> {new_status}',actor=actor,entity_type='qms_audits',entity_id=audit_key,reason=summary.strip() or 'Audit workspace outcome update',before_value=before,after_value=new_status)
                st.success('Audit outcome updated.')
                st.rerun()

def my_audits_page(actor):
    """Assigned QMS/lead-auditor audits with an integrated audit workspace."""
    st.header('My Audits')
    st.caption('Assigned audits with a complete audit workspace. Findings/actions remain in enterprise NCR/CAPA and evidence review remains in QMS Evidence Review.')
    audits = db_all('qms_audits')
    if audits.empty:
        st.info('No audits are currently registered.')
        return
    uidv = _id(actor)
    view = _match_any(audits, ['lead_auditor_id','assigned_auditor_id'], uidv)
    if view.empty and not (can_action(actor,'QMS','View','Organization-wide') or can_action(actor,'QMS','Manage','Organization-wide')):
        st.info('No audits are assigned to you.')
        return
    if view.empty: view = audits
    metrics([('Assigned', len(view)), ('Open', int(view.get('status', pd.Series(dtype=str)).astype(str).isin(['Planned','In Progress','Under Review']).sum())), ('Completed', int((view.get('status', pd.Series(dtype=str)) == 'Completed').sum()))])
    cols = [c for c in ['audit_id','audit_type','department','standard','planned_date','status','overall_result'] if c in view.columns]
    table(view[cols] if cols else view, max_rows=200)
    ids=view['audit_id'].astype(str).tolist() if 'audit_id' in view.columns else []
    if ids:
        selected=st.selectbox('Open Audit Workspace',['—']+ids,key='my_audit_workspace')
        if selected!='—':
            audit_workspace_page(actor, selected)


def crb_case_workspace_page(actor):
    """CRB Case Workspace aggregates existing records for assigned CRB cases without duplicating them."""
    st.header('CRB Case Workspace')
    st.caption('Case-based CRB board workspace. Board participation is assigned on the authorization case; CRB is not a standalone account role. Evidence remains in its owning records and is referenced here.')
    auths = db_all('authorization_requests')
    uidv = _id(actor)
    # CRB is a case-based board function, not a standalone system role.
    if table_exists('crb_case_board_assignments'):
        ba = db_where('crb_case_board_assignments', 'user_id = :uid', (('uid', uidv),))
        case_ids = set(ba.get('authorization_id', pd.Series(dtype=str)).astype(str).tolist()) if not ba.empty else set()
        if case_ids:
            auths = auths[auths.get('authorization_id', pd.Series(dtype=str)).astype(str).isin(case_ids)].copy()
        elif actor_get(actor, 'role') not in {'GM','Admin'}:
            auths = auths.iloc[0:0].copy()
    else:
        auths = _scoped(auths, actor)
    if auths.empty:
        st.info('No CRB cases are assigned to you.')
        return
    st.metric('Assigned CRB Cases', len(auths))
    options = auths['authorization_id'].astype(str).tolist()
    selected = st.selectbox('Case', options, key='crb_workspace_case')
    req = auths[auths['authorization_id'].astype(str) == selected].iloc[0]
    user_id = str(req.get('user_id',''))
    scope = str(req.get('scope',''))
    st.markdown(f"### {req.get('name','—')} · {scope}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Status', req.get('status','—'))
    c2.metric('Job Type', req.get('job_type','—'))
    c3.metric('CRB Decision', req.get('crb_decision','Pending'))
    c4.metric('Expiry', req.get('expiry_date','—'))
    tabs = st.tabs(['Authorization','Case Evidence Package','Competency','Witness','Technical Review','NCR / QMS'])
    links = db_where('authorization_evidence_links', 'authorization_id = :authorization_id', (('authorization_id', selected),)) if table_exists('authorization_evidence_links') else pd.DataFrame()
    can_link = (can_action(actor, 'Technical Reviews', 'Review', 'Organization-wide') or can_action(actor, 'Authorization', 'Manage', 'Organization-wide') or can_action(actor, 'Administration', 'Manage', 'Organization-wide'))
    required_case_modules = ['Competency','Witness','Technical Review','QMS','NCR']
    linked_modules = set(links.get('source_module', pd.Series(dtype=str)).astype(str).tolist()) if not links.empty else set()
    readiness_rows = []
    for mod in required_case_modules:
        status = 'Verified' if mod in linked_modules else 'Missing'
        readiness_rows.append((mod, status))
    readiness_df = pd.DataFrame(readiness_rows, columns=['Gate','Status'])
    verified = int((readiness_df['Status'] == 'Verified').sum()) if not readiness_df.empty else 0
    total = len(readiness_df)
    missing = total - verified
    with tabs[1]:
        st.subheader('Case Evidence Package')
        st.caption('A single decision-readiness view for this exact authorization case. Evidence remains owned by its source module; only explicit authorization_evidence_links make it part of the case package.')
        r1, r2, r3 = st.columns(3)
        r1.metric('Required Gates', total)
        r2.metric('Verified', verified)
        r3.metric('Missing', missing)
        table(readiness_df)
        if missing == 0:
            st.success('CRB case is decision-ready: all required evidence gates are linked to this exact authorization case.')
        else:
            st.warning(f'CRB case is not decision-ready. {missing} required evidence gate(s) are still missing.')
        st.markdown('### Decision Readiness')
        readiness_notes = []
        if str(req.get('status','')).casefold() in {'management approved','authorized','valid'}:
            readiness_notes.append('Authorization status is already approved/active.')
        else:
            readiness_notes.append(f"Authorization status: {req.get('status','—')}")
        if str(req.get('crb_decision','')).strip():
            readiness_notes.append(f"CRB decision recorded: {req.get('crb_decision')}")
        else:
            readiness_notes.append('CRB decision is still pending.')
        if missing:
            readiness_notes.append('Resolve all missing evidence gates before final board decision.')
        for note in readiness_notes:
            st.write(f'• {note}')
        if not links.empty:
            table(links[[c for c in ['source_module','source_record_id','linked_by','linked_on','reason'] if c in links.columns]])
    if can_link and table_exists('authorization_evidence_links'):
        with st.expander('Link Existing Evidence to This CRB Case'):
            source_defs={'Competency':('competency_matrix','competency_id'),'Witness':('witness_surveys','witness_id'),'Supervised':('supervised_activities','supervised_id'),'Technical Review':('technical_reviews','review_id'),'NCR':('competency_ncrs','ncr_id'),'QMS':('qms_evidence_reviews','review_id')}
            options=[]
            for mod,(tbl,idc) in source_defs.items():
                src=db_all(tbl)
                if src.empty or idc not in src.columns: continue
                if 'user_id' in src.columns: src=src[src['user_id'].astype(str).eq(user_id)]
                options.extend([(mod,str(r[idc])) for _,r in src.iterrows()])
            existing=set((str(r.get('source_module','')),str(r.get('source_record_id',''))) for _,r in links.iterrows()) if not links.empty else set()
            options=[x for x in options if x not in existing]
            if options:
                pick=st.selectbox('Source evidence', ['—']+[f'{m} — {rid}' for m,rid in options], key=f'crb_link_{selected}')
                reason=st.text_input('Link reason', key=f'crb_link_reason_{selected}')
                if pick!='—' and st.button('Link to CRB Case', key=f'crb_link_btn_{selected}'):
                    mod,rid=pick.split(' — ',1)
                    link_id=uid('AEL')
                    db_insert('authorization_evidence_links', {'link_id':link_id,'authorization_id':selected,'source_module':mod,'source_record_id':rid,'linked_by':actor_get(actor,'user_id'),'linked_on':now(),'reason':reason.strip()})
                    audit('Authorization Evidence Linked', f'{selected}: {mod}/{rid}', actor=actor, entity_type='authorization_evidence_links', entity_id=link_id, reason=reason.strip() or 'Exact evidence linked to authorization case')
                    st.success('Evidence linked to the exact CRB case.')
                    st.rerun()
            else:
                st.info('No unlinked evidence for this person is available to attach.')
    with tabs[0]:
        table(auths[auths['authorization_id'].astype(str) == selected][[c for c in auths.columns if c in ['authorization_id','scope','job_type','status','crb_decision','crb_remarks','expiry_date','certificate_id']]])
    def linked_source(module_name):
        if links.empty: return pd.DataFrame()
        ids=set(links[links.get('source_module',pd.Series(dtype=str)).astype(str).eq(module_name)].get('source_record_id',pd.Series(dtype=str)).astype(str).tolist())
        if not ids: return pd.DataFrame()
        mapping={'Competency':('competency_matrix','competency_id'),'Witness':('witness_surveys','witness_id'),'Supervised':('supervised_activities','supervised_id'),'Technical Review':('technical_reviews','review_id'),'NCR':('competency_ncrs','ncr_id'),'QMS':('qms_evidence_reviews','review_id')}
        tbl,idc=mapping[module_name]; src=db_all(tbl)
        return src[src.get(idc,pd.Series('',index=src.index)).astype(str).isin(ids)].copy() if not src.empty else src
    with tabs[2]:
        comp=linked_source('Competency'); table(comp[[c for c in ['competency_id','scope','competency_level','status','expiry_date','evidence'] if c in comp.columns]] if not comp.empty else comp)
    with tabs[3]:
        w=linked_source('Witness'); s=linked_source('Supervised'); st.write('Witness'); table(w[[c for c in ['witness_id','witness_date','outcome','status','comments'] if c in w.columns]] if not w.empty else w); st.write('Supervised Activities'); table(s[[c for c in ['supervised_id','activity_date','outcome','status','comments'] if c in s.columns]] if not s.empty else s)
    with tabs[4]:
        tr=linked_source('Technical Review'); table(tr[[c for c in ['review_id','review_type','status','decision','overall_score','comments'] if c in tr.columns]] if not tr.empty else tr)
    with tabs[5]:
        ncr=linked_source('NCR'); qms=linked_source('QMS'); table(ncr[[c for c in ['ncr_id','severity','status','impact_on_authorization','corrective_action'] if c in ncr.columns]] if not ncr.empty else ncr);
        if not qms.empty: table(qms)
        if links.empty: st.warning('No evidence is linked to this authorization case. Unrelated records are intentionally excluded.')


def management_review_dashboard_page(actor):
    """Management Review governance workspace with child action tracking."""
    st.header('Management Review Dashboard')
    st.caption('Governance workflow: review decisions → action register → owner → due date → progress → closure. Review records remain authoritative; actions are tracked as child governance records.')
    reviews=db_all('qms_management_reviews')
    actions=db_all('qms_management_review_actions') if table_exists('qms_management_review_actions') else pd.DataFrame()
    if reviews.empty:
        st.info('No management reviews have been recorded yet.')
        return
    if actions.empty:
        actions=pd.DataFrame(columns=['action_id','review_id','action_text','owner_name','due_date','status','progress','closure_note','created_on','updated_on'])
    status=reviews.get('status',pd.Series(dtype=str)).astype(str)
    overdue_actions=0
    if not actions.empty and 'due_date' in actions.columns:
        overdue_actions=int(actions['due_date'].astype(str).map(days_until).fillna(9999).lt(0).sum())
    metrics([('Reviews',len(reviews)),('Open Reviews',int(status.isin(['Draft','Scheduled','In Progress','Open']).sum())),('Open Actions',int(actions.get('status',pd.Series(dtype=str)).astype(str).isin(['Open','In Progress','At Risk']).sum())),('Overdue Actions',overdue_actions)])
    tabs=st.tabs(['Executive View','Review Register','Action Register'])
    with tabs[0]:
        latest=reviews.sort_values('review_date',ascending=False).head(10) if 'review_date' in reviews.columns else reviews.head(10)
        table(latest[[c for c in ['review_id','review_period','chair_name','review_date','status','due_date'] if c in latest.columns]])
        if not actions.empty:
            state=actions.get('status',pd.Series(dtype=str)).astype(str).value_counts().rename_axis('status').reset_index(name='actions')
            st.subheader('Action Status')
            table(state)
    with tabs[1]:
        table(reviews.sort_values('review_date',ascending=False) if 'review_date' in reviews.columns else reviews,max_rows=100)
    with tabs[2]:
        st.subheader('Action Register')
        if not actions.empty:
            table(actions[[c for c in ['action_id','review_id','action_text','owner_name','due_date','status','progress','closure_note'] if c in actions.columns]],max_rows=100)
        can_manage=can_action(actor,'QMS','Review','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
        if can_manage:
            review_options=['—']+reviews['review_id'].astype(str).tolist()
            rid=st.selectbox('Review',review_options,key='mr_action_review')
            if rid!='—':
                with st.form(f'mr_action_add_{rid}'):
                    txt=st.text_area('Action',key='mr_action_text')
                    owner=st.text_input('Responsible Owner',key='mr_action_owner')
                    due=st.text_input('Due Date',key='mr_action_due')
                    prog=st.slider('Initial Progress %',0,100,0,key='mr_action_progress')
                    if st.form_submit_button('Add Governance Action',type='primary') and txt.strip():
                        aid='MRA-'+uuid.uuid4().hex[:10].upper()
                        db_insert('qms_management_review_actions',{'action_id':aid,'review_id':rid,'action_text':txt.strip(),'owner_name':owner.strip(),'due_date':due.strip(),'status':'Open' if prog<100 else 'Completed','progress':prog,'created_by':actor_get(actor,'name'),'created_on':now(),'updated_on':now()})
                        audit('Management Review Action Created',f'{aid}: child action',actor=actor,entity_type='qms_management_review_actions',entity_id=aid,reason='Management review action governance')
                        st.success('Governance action added.')
                        st.rerun()
                owned=actions[actions['review_id'].astype(str).eq(rid)] if not actions.empty and 'review_id' in actions.columns else actions
                if not owned.empty:
                    aid=st.selectbox('Manage Action',['—']+owned['action_id'].astype(str).tolist(),key='mr_action_manage')
                    if aid!='—':
                        rr=owned[owned['action_id'].astype(str).eq(aid)].iloc[0]
                        with st.form(f'mr_action_edit_{aid}'):
                            pval=int(float(rr.get('progress',0) or 0))
                            progress=st.slider('Progress %',0,100,pval,key=f'p_{aid}')
                            status_opts=['Open','In Progress','At Risk','Completed','Closed']
                            cur=str(rr.get('status','Open'))
                            status_val=st.selectbox('Status',status_opts,index=status_opts.index(cur) if cur in status_opts else 0,key=f's_{aid}')
                            note=st.text_area('Closure / Progress Note',value=str(rr.get('closure_note','') or ''),key=f'n_{aid}')
                            if st.form_submit_button('Save Governance Action'):
                                db_update('qms_management_review_actions','action_id',aid,{'progress':progress,'status':('Completed' if progress>=100 and status_val in {'Open','In Progress','At Risk'} else status_val),'closure_note':note.strip(),'completed_on':now() if progress>=100 else rr.get('completed_on'),'updated_on':now()})
                                audit('Management Review Action Updated',f'{aid}: progress/status updated',actor=actor,entity_type='qms_management_review_actions',entity_id=aid,reason='Management review action governance')
                                st.success('Governance action updated.')
                                st.rerun()


def probation_review_page(actor):
    """Formal probation review workflow. Probationer can view; authorized reviewers can edit/decide."""
    st.header('Probation Review')
    st.caption('Formal probation review linking objectives, development, training, competency, performance and trainer assessment. One review record per active probation cycle.')
    role = actor_get(actor, 'role', '')
    is_probation_self = role in {'Trainee','On Probation'}
    uidv = _id(actor)
    reviews = db_all('probation_reviews')
    if is_probation_self:
        reviews = reviews[reviews.get('user_id', pd.Series(dtype=str)).astype(str).eq(uidv)] if not reviews.empty else reviews
    elif not reviews.empty:
        reviews = _scoped(reviews, actor)
    metrics([('Reviews', len(reviews)), ('Open', int(reviews.get('status', pd.Series(dtype=str)).astype(str).isin(['Draft','In Progress','Pending Decision']).sum()) if not reviews.empty else 0), ('Completed', int((reviews.get('status', pd.Series(dtype=str)).astype(str) == 'Confirmed').sum()) if not reviews.empty else 0)])
    if not reviews.empty:
        table(reviews.sort_values('review_date', ascending=False) if 'review_date' in reviews.columns else reviews)
    can_manage_enterprise = (can_action(actor, 'Annual Review', 'Approve', 'Organization-wide') or can_action(actor, 'Administration', 'Manage', 'Organization-wide') or can_action(actor, 'QMS', 'Review', 'Organization-wide'))
    is_assigned_tutor = actor_get(actor, 'role','') == 'Trainer'
    can_manage_assigned = is_assigned_tutor and can_action(actor, 'Development Plans', 'Edit', 'Assigned')
    can_manage = can_manage_enterprise or can_manage_assigned
    if can_manage:
        users = _assigned_people(actor, 'Trainer') if can_manage_assigned else db_where('users', "status = 'Active'", ())
        if can_manage_assigned:
            st.caption('Trainer scope: only probationers explicitly assigned to you are available for review.')
        user_options = {f"{r.get('name','')} — {r.get('user_id','')}": r for r in users.to_dict('records')} if not users.empty else {}
        with st.form('probation_review_form'):
            selected = st.selectbox('Employee', ['—'] + list(user_options.keys()))
            start = st.date_input('Probation Start', date.today())
            end = st.date_input('Probation End', date.today() + timedelta(days=180))
            objectives = st.text_area('Objectives')
            performance = st.text_area('Performance Summary')
            training = st.text_area('Training Status')
            competency = st.text_area('Competency Status')
            tutor_assessment = st.text_area('Trainer Assessment / Development Note')
            decision = st.selectbox('Decision', ['Pending', 'Confirm', 'Extend', 'Not Confirmed'])
            decision_notes = st.text_area('Decision Notes')
            if st.form_submit_button('Save Probation Review', type='primary') and selected != '—':
                person = user_options[selected]
                rid = uid('PROB')
                data = {'review_id': rid, 'user_id': person.get('user_id',''), 'name': person.get('name',''), 'probation_start': str(start), 'probation_end': str(end), 'objectives': objectives.strip(), 'performance_summary': performance.strip(), 'training_status': training.strip(), 'competency_status': competency.strip(), 'tutor_assessment': tutor_assessment.strip(), 'decision': decision, 'decision_notes': decision_notes.strip(), 'reviewer_id': actor_get(actor,'user_id'), 'reviewer_name': actor_get(actor,'name'), 'review_date': today(), 'status': 'Confirmed' if decision in {'Confirm','Not Confirmed'} else 'Pending Decision', 'created_on': now(), 'updated_on': now()}
                db_insert('probation_reviews', data)
                audit('Probation Review Saved', f'{rid}: {person.get("name","")} → {decision}', actor=actor, entity_type='probation_reviews', entity_id=rid, reason='Formal probation review')
                st.success('Probation review saved.')
                st.rerun()
    else:
        st.info('Probationers can view their review; only authorized reviewers can create or decide a probation review.')
