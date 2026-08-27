from psb_app.services.database_service import ensure_accreditation_schema, ensure_client_feedback_schema, ensure_interpretation_schema
from psb_app.common import (
    DEPARTMENTS,
    SCOPES,
    actor_get,
    audit,
    can_action,
    date,
    db_all,
    db_insert,
    db_update,
    json,
    now,
    pd,
    restrict_user_frame,
    select_person,
    st,
    timedelta,
    today,
    uid,
)

def qms_page(actor):
    """Professional QMS workspace.

    QMS is the governance/control layer: audits, compliance obligations,
    management review and evidence acceptance. NCR/CAPA remains the single
    enterprise corrective-action engine and is referenced here, not duplicated.
    """
    st.header('QMS')
    st.caption('Quality governance hub for audits, compliance, management review and evidence assurance. NCR/CAPA remains the single enterprise corrective-action workflow.')
    if not (can_action(actor, 'QMS', 'View', 'Department') or can_action(actor, 'QMS', 'View', 'Organization-wide')):
        st.info('QMS is restricted to authorized quality, technical and management roles.')
        return
    audits = db_all('qms_audits')
    compliance = db_all('qms_compliance_items')
    reviews = db_all('qms_management_reviews')
    ncrs = restrict_user_frame(db_all('competency_ncrs'), actor)
    technical = restrict_user_frame(db_all('technical_reviews'), actor)
    today_str = str(date.today())

    def _days(d):
        try:
            return (pd.to_datetime(d).date() - date.today()).days
        except Exception:
            return None
    open_audits = int(audits.get('status', pd.Series(dtype=str)).astype(str).isin(['Planned', 'In Progress', 'Under Review']).sum()) if not audits.empty else 0
    overdue_compliance = int(compliance.get('next_review_due', pd.Series(dtype=str)).astype(str).apply(lambda x: _days(x) is not None and _days(x) < 0).sum()) if not compliance.empty else 0
    open_ncr = int(ncrs.get('status', pd.Series(dtype=str)).astype(str).isin(['Open', 'Containment', 'Root Cause', 'Corrective Action', 'Verification', 'Effectiveness Review'])).sum() if not ncrs.empty else 0
    recent_tech = int(technical.get('status', pd.Series(dtype=str)).astype(str).isin(['Completed', 'Approved', 'Accepted']).sum()) if not technical.empty else 0
    metrics([('Audits Open', open_audits), ('Compliance Overdue', overdue_compliance), ('Open NCR/CAPA', open_ncr), ('Technical Reviews Complete', recent_tech)])
    tabs = st.tabs(['QMS Dashboard', 'Audits', 'Compliance Register', 'Management Review', 'Evidence Review'])
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        c1.subheader('Quality Health')
        if not compliance.empty:
            counts = compliance.get('status', pd.Series(dtype=str)).astype(str).value_counts().rename_axis('status').reset_index(name='count')
            table(counts)
        else:
            c1.info('No compliance obligations have been configured.')
        c2.subheader('Open Corrective Actions')
        if not ncrs.empty:
            shown = ncrs[ncrs.get('status', pd.Series(dtype=str)).astype(str).isin(['Open', 'Containment', 'Root Cause', 'Corrective Action', 'Verification', 'Effectiveness Review'])].copy()
            table(shown[[c for c in ['ncr_id', 'severity', 'priority', 'source', 'due_date', 'status', 'owner_name'] if c in shown.columns]].sort_values('due_date') if not shown.empty and 'due_date' in shown.columns else shown)
        else:
            c2.info('No NCR/CAPA records found.')
        c3.subheader('Audit Activity')
        if not audits.empty:
            summary = audits.get('status', pd.Series(dtype=str)).astype(str).value_counts().rename_axis('status').reset_index(name='count')
            table(summary)
        else:
            c3.info('No QMS audits have been planned yet.')
        st.subheader('Quality Governance Rules')
        st.markdown('- QMS does not create a second NCR system; all findings use the enterprise NCR/CAPA engine.\n- Technical Reviews remain the authoritative technical-review record.\n- Compliance items are requirements to monitor, not duplicate documents.\n- Management Review records decisions and actions; action execution remains in the owning workflow.')
    with tabs[1]:
        st.subheader('QMS Audit Register')
        filters = st.columns(4)
        status_filter = filters[0].selectbox('Status', ['All', 'Planned', 'In Progress', 'Under Review', 'Completed', 'Cancelled'], key='qms_audit_status')
        type_filter = filters[1].selectbox('Audit Type', ['All', 'Internal Audit', 'Process Audit', 'Witness Audit', 'Supplier Audit', 'Surveillance', 'Management System Audit'], key='qms_audit_type')
        dept_filter = filters[2].selectbox('Department', ['All'] + DEPARTMENTS, key='qms_audit_dept')
        standard_filter = filters[3].selectbox('Standard', ['All', 'ISO 9001', 'ISO/IEC 17020', 'IMO RO Code', 'IACS PR7', 'Internal QMS'], key='qms_audit_std')
        shown = audits.copy()
        if not shown.empty:
            if status_filter != 'All':
                shown = shown[shown.get('status', '').astype(str) == status_filter]
            if type_filter != 'All':
                shown = shown[shown.get('audit_type', '').astype(str) == type_filter]
            if dept_filter != 'All':
                shown = shown[shown.get('department', '').astype(str) == dept_filter]
            if standard_filter != 'All':
                shown = shown[shown.get('standard', '').astype(str) == standard_filter]
            table(shown.sort_values('planned_date', ascending=True) if 'planned_date' in shown.columns else shown)
        else:
            st.info('No audits are currently registered.')
        if can_action(actor, 'Accreditation Readiness', 'Create', 'Organization-wide') or can_action(actor, 'Accreditation Readiness', 'Review', 'Organization-wide'):
            with st.expander('Plan New QMS Audit', expanded=False):
                with st.form('qms_audit_create'):
                    a1, a2 = st.columns(2)
                    audit_type = a1.selectbox('Audit Type', ['Internal Audit', 'Process Audit', 'Witness Audit', 'Supplier Audit', 'Surveillance', 'Management System Audit'])
                    department = a2.selectbox('Department', DEPARTMENTS)
                    standard = a1.selectbox('Standard', ['ISO 9001', 'ISO/IEC 17020', 'IMO RO Code', 'IACS PR7', 'Internal QMS'])
                    scope = a2.text_input('Audit Scope')
                    lead_name, lead_id, _ = select_person('Lead Auditor', ['QMS Auditor', 'QMR', 'Department Manager'], key='qms_lead')
                    planned = a1.date_input('Planned Date', date.today() + timedelta(days=14))
                    objective = a2.text_area('Objective')
                    if st.form_submit_button('Create Audit', type='primary') and lead_id and scope.strip():
                        aid = uid('QAUD')
                        db_insert('qms_audits', {'audit_id': aid, 'audit_type': audit_type, 'department': department, 'standard': standard, 'audit_scope': scope.strip(), 'lead_auditor_id': lead_id, 'lead_auditor_name': lead_name, 'planned_date': str(planned), 'completed_date': '', 'status': 'Planned', 'overall_result': '', 'objective': objective.strip(), 'report_summary': '', 'created_by': actor_get(actor, 'name'), 'created_on': now(), 'updated_on': now()})
                        audit('QMS Audit Created', f'{aid}: {audit_type} / {scope}', actor=actor, entity_type='qms_audits', entity_id=aid, reason='New QMS audit planned')
                        st.success('QMS audit created.')
                        st.rerun()
            if not audits.empty:
                st.subheader('Record Audit Result')
                options = audits[audits.get('status', pd.Series(dtype=str)).astype(str).isin(['Planned', 'In Progress', 'Under Review'])]['audit_id'].astype(str).tolist()
                if options:
                    aid = st.selectbox('Audit', options, key='qms_audit_update')
                    row = audits[audits['audit_id'].astype(str) == aid].iloc[0]
                    r1, r2 = st.columns(2)
                    new_status = r1.selectbox('Status', ['In Progress', 'Under Review', 'Completed', 'Cancelled'], key=f'qms_audit_new_{aid}')
                    result = r2.selectbox('Overall Result', ['', 'Conforming', 'Minor Findings', 'Major Findings', 'Unsatisfactory'], key=f'qms_audit_result_{aid}')
                    summary = st.text_area('Report Summary', key=f'qms_audit_summary_{aid}')
                    if st.button('Save Audit Result', key=f'qms_audit_save_{aid}', type='primary'):
                        before = str(row.get('status', ''))
                        done = str(date.today()) if new_status == 'Completed' else str(row.get('completed_date', ''))
                        db_update('qms_audits', 'audit_id', aid, {'status': new_status, 'overall_result': result, 'report_summary': summary.strip(), 'completed_date': done, 'updated_on': now()})
                        audit('QMS Audit Updated', f'{aid}: {before} -> {new_status}', actor=actor, entity_type='qms_audits', entity_id=aid, reason=summary.strip() or 'QMS audit status/result update', before_value=before, after_value=new_status)
                        st.success('Audit updated.')
                        st.rerun()
                else:
                    st.info('No open audits require an audit-result update.')
    with tabs[2]:
        st.subheader('QMS Compliance Register')
        if not compliance.empty:
            table(compliance.sort_values('next_review_due') if 'next_review_due' in compliance.columns else compliance)
        else:
            st.info('No compliance requirements configured yet.')
        if can_action(actor, 'Accreditation Readiness', 'Approve', 'Organization-wide'):
            with st.expander('Add Compliance Requirement', expanded=False):
                with st.form('qms_comp_create'):
                    r1, r2 = st.columns(2)
                    std = r1.selectbox('Standard', ['ISO 9001', 'ISO/IEC 17020', 'IMO RO Code', 'IACS PR7', 'Internal QMS'])
                    clause = r2.text_input('Clause')
                    reqtxt = r1.text_area('Requirement')
                    owner_dept = r2.selectbox('Owner Department', DEPARTMENTS)
                    owner_name, owner_id, _ = select_person('Owner', ['QMR', 'QMS Auditor', 'Department Manager'], key='qms_comp_owner')
                    frequency = r1.selectbox('Review Frequency', ['Monthly', 'Quarterly', 'Semi-Annual', 'Annual', 'Event-driven'])
                    due = r2.date_input('Next Review Due', date.today() + timedelta(days=90))
                    notes = st.text_area('Notes')
                    if st.form_submit_button('Add Requirement', type='primary') and reqtxt.strip():
                        cid = uid('QCOMP')
                        db_insert('qms_compliance_items', {'compliance_id': cid, 'standard': std, 'clause': clause.strip(), 'requirement': reqtxt.strip(), 'owner_department': owner_dept, 'owner_id': owner_id, 'owner_name': owner_name, 'frequency': frequency, 'due_date': '', 'status': 'Open', 'evidence_record': '', 'last_reviewed': '', 'next_review_due': str(due), 'notes': notes.strip(), 'created_on': now(), 'updated_on': now()})
                        audit('QMS Compliance Requirement Created', f'{cid}: {clause}', actor=actor, entity_type='qms_compliance_items', entity_id=cid, reason='New compliance obligation')
                        st.success('Compliance requirement created.')
                        st.rerun()
    with tabs[3]:
        st.subheader('Management Review')
        table(reviews.sort_values('review_date', ascending=False) if not reviews.empty and 'review_date' in reviews.columns else reviews)
        if can_action(actor, 'Accreditation Readiness', 'Approve', 'Organization-wide'):
            with st.form('qms_mgmt_review'):
                period = st.text_input('Review Period', value=str(date.today().year))
                chair_name, chair_id, _ = select_person('Chair', ['Management', 'QMR', 'Department Manager'], key='qms_mr_chair')
                review_date = st.date_input('Review Date', date.today())
                inputs = st.text_area('Inputs Summary', placeholder='Audit results, NCR/CAPA, customer feedback, competency, training, technical review, risks...')
                decisions = st.text_area('Decisions')
                actions = st.text_area('Actions / Follow-up')
                owner_name, owner_id, _ = select_person('Action Owner', None, key='qms_mr_owner')
                due = st.date_input('Action Due Date', date.today() + timedelta(days=30))
                if st.form_submit_button('Record Management Review', type='primary') and chair_id and inputs.strip():
                    rid = uid('QMRV')
                    db_insert('qms_management_reviews', {'review_id': rid, 'review_period': period.strip(), 'chair_id': chair_id, 'chair_name': chair_name, 'review_date': str(review_date), 'inputs_summary': inputs.strip(), 'decisions': decisions.strip(), 'actions': actions.strip(), 'responsible_owner_id': owner_id, 'responsible_owner_name': owner_name, 'due_date': str(due), 'status': 'Open', 'created_by': actor_get(actor, 'name'), 'created_on': now(), 'updated_on': now()})
                    audit('QMS Management Review Recorded', f'{rid}: {period}', actor=actor, entity_type='qms_management_reviews', entity_id=rid, reason='Management review record')
                    st.success('Management review recorded.')
                    st.rerun()
    with tabs[4]:
        st.subheader('Evidence Review')
        st.caption('QMS evidence acceptance references existing records; it does not duplicate the source workflow or file repository.')
        ev = db_all('qms_evidence_reviews')
        table(ev.sort_values('reviewed_on', ascending=False) if not ev.empty and 'reviewed_on' in ev.columns else ev)
        if can_action(actor, 'QMS', 'Review', 'Department') or can_action(actor, 'QMS', 'Manage', 'Organization-wide'):
            source = st.selectbox('Source Module', ['Technical Reviews', 'Training', 'Competency', 'Practical / Witness', 'NCR / Corrective Action', 'Knowledge Library', 'Client Feedback'])
            source_id = st.text_input('Source Record ID')
            title = st.text_input('Evidence / Record Title')
            decision = st.selectbox('Evidence Decision', ['Accepted', 'Accepted with Conditions', 'Rejected', 'Need Clarification'])
            comments = st.text_area('Comments')
            if st.button('Record Evidence Review', type='primary') and source_id.strip() and title.strip():
                eid = uid('QEVID')
                db_insert('qms_evidence_reviews', {'evidence_review_id': eid, 'source_module': source, 'source_record_id': source_id.strip(), 'evidence_title': title.strip(), 'reviewer_id': actor_get(actor, 'user_id'), 'reviewer_name': actor_get(actor, 'name'), 'decision': decision, 'comments': comments.strip(), 'reviewed_on': now(), 'created_on': now()})
                audit('QMS Evidence Reviewed', f'{source}:{source_id}', actor=actor, entity_type='qms_evidence_reviews', entity_id=eid, reason=comments.strip(), after_value=decision)
                st.success('Evidence review recorded.')
                st.rerun()

def technical_reviews_page(actor):
    """Unified Technical Reviews workspace for Survey Report Review and Plan Review QA.
    One review engine, specialized fields per review type, common audit/NCR linkage,
    and a single review register without duplicating source workflows.
    """
    st.header('Technical Reviews')
    st.caption('Unified technical quality review workspace. Survey Report Review and Plan Review QA share one review lifecycle while retaining discipline-specific criteria.')
    role = actor_get(actor, 'role')
    if not (can_action(actor, 'Technical Reviews', 'View', 'Department') or can_action(actor, 'Technical Reviews', 'View', 'Organization-wide')):
        st.info('Technical Reviews are restricted to authorized technical and quality roles.')
        return
    common = restrict_user_frame(db_all('technical_reviews'), actor)
    if common.empty:
        common = pd.DataFrame(columns=['review_id', 'review_type', 'user_id', 'name', 'scope', 'subject_name', 'source_record_id', 'reviewer_id', 'reviewer_name', 'overall_score', 'decision', 'status', 'comments', 'created_on', 'updated_on'])
    for c in ['review_id', 'review_type', 'user_id', 'name', 'scope', 'subject_name', 'source_record_id', 'reviewer_id', 'reviewer_name', 'overall_score', 'decision', 'status', 'comments', 'created_on', 'updated_on']:
        if c not in common.columns:
            common[c] = ''
    open_reviews = common[common['status'].astype(str).isin(['Open', 'In Review', 'Returned'])] if not common.empty else common
    approved = common[common['status'].astype(str).eq('Approved')] if not common.empty else common
    avg_score = pd.to_numeric(common['overall_score'], errors='coerce').dropna().mean() if not common.empty else 0
    overdue = 0
    if not common.empty and 'due_date' in common.columns:
        overdue = int(((common['due_date'].astype(str) != '') & (common['due_date'].astype(str) < today()) & common['status'].astype(str).isin(['Open', 'In Review', 'Returned'])).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Total Reviews', len(common))
    c2.metric('Open / In Review', len(open_reviews))
    c3.metric('Approved', len(approved))
    c4.metric('Average Score', f'{avg_score:.1f}%' if avg_score else '—')
    tabs = st.tabs(['Review Register', 'Survey Report Review', 'Plan Review QA', 'Review Detail'])
    with tabs[0]:
        f1, f2, f3, f4 = st.columns(4)
        search = f1.text_input('Search', key='tr_search')
        typ = f2.selectbox('Review Type', ['All', 'Survey Report Review', 'Plan Review QA'], key='tr_type')
        status = f3.selectbox('Status', ['All', 'Draft', 'Open', 'In Review', 'Returned', 'Approved', 'Approved with Comments', 'Rejected'], key='tr_status')
        decision = f4.selectbox('Decision', ['All', 'Accepted', 'Accepted with Comments', 'Rejected', 'Re-training Required', 'Further Supervision Required', 'Approved', 'Approved with Comments', 'Return for Clarification'], key='tr_decision')
        v = common.copy()
        if search:
            blob = v.fillna('').astype(str).agg(' | '.join, axis=1).str.casefold()
            v = v[blob.str.contains(search.casefold(), regex=False)]
        if typ != 'All':
            v = v[v['review_type'].astype(str) == typ]
        if status != 'All':
            v = v[v['status'].astype(str) == status]
        if decision != 'All':
            v = v[v['decision'].astype(str) == decision]
        cols = [c for c in ['review_id', 'review_type', 'name', 'scope', 'subject_name', 'reviewer_name', 'overall_score', 'decision', 'status', 'created_on'] if c in v.columns]
        table(v[cols].sort_values('created_on', ascending=False) if not v.empty else v, max_rows=250)
        st.caption('The register is a unified view. The underlying employee, training, witness, NCR and authorization records remain owned by their respective modules.')
    with tabs[1]:
        if not (can_action(actor, 'Technical Reviews', 'Review', 'Department') or can_action(actor, 'Technical Reviews', 'Review', 'Organization-wide')):
            st.info('You do not have permission to record Survey Report Reviews.')
        else:
            with st.form('technical_srr'):
                name, uidv, _ = select_person('Surveyor', ['Trainee', 'Surveyor', 'On Probation', 'Industrial Surveyor'], key='tr_srr_person')
                scope = st.selectbox('Survey Scope', SCOPES, key='tr_srr_scope')
                discipline = st.selectbox('Technical Discipline', sorted(['Hull','Machinery','Electrical','Industrial','Plan','QMS']), key='tr_srr_discipline')
                report_ref = st.text_input('Report / Survey Reference', key='tr_srr_ref')
                vessel = st.text_input('Vessel / Project', key='tr_srr_vessel')
                file_id = st.text_input('Report File ID / Evidence Reference', key='tr_srr_file')
                due_date = st.text_input('Review Due Date (YYYY-MM-DD)', key='tr_srr_due')
                st.markdown('**Assessment Criteria (1–5)**')
                a, b, c, d, e = st.columns(5)
                tq = a.slider('Technical Quality', 1, 5, 3, key='tr_srr_tq')
                di = b.slider('Deficiency Identification', 1, 5, 3, key='tr_srr_di')
                ri = c.slider('Rule Interpretation', 1, 5, 3, key='tr_srr_ri')
                rw = d.slider('Report Writing', 1, 5, 3, key='tr_srr_rw')
                dq = e.slider('Decision Quality', 1, 5, 3, key='tr_srr_dq')
                decision = st.selectbox('Decision', ['Accepted', 'Accepted with Comments', 'Rejected', 'Re-training Required'], key='tr_srr_decision')
                comments = st.text_area('Reviewer Comments', key='tr_srr_comments')
                reason = st.text_area('Review Reason / Context *', key='tr_srr_reason')
                submitted = st.form_submit_button('Record Survey Report Review', type='primary')
            if submitted:
                if not uidv or not reason.strip():
                    st.error('Surveyor and review reason are required.')
                else:
                    score = round((tq + di + ri + rw + dq) / 25 * 100, 2)
                    rid = uid('TRR')
                    status = 'Rejected' if decision == 'Rejected' else 'Approved with Comments' if decision == 'Accepted with Comments' else 'Open'
                    row = {'review_id': rid, 'review_type': 'Survey Report Review', 'discipline': discipline, 'user_id': uidv, 'name': name, 'scope': scope, 'subject_name': vessel, 'source_record_id': report_ref or file_id, 'reviewer_id': actor_get(actor, 'user_id'), 'reviewer_name': actor_get(actor, 'name'), 'assigned_reviewer_id': actor_get(actor, 'user_id'), 'assigned_reviewer_name': actor_get(actor, 'name'), 'overall_score': score, 'decision': decision, 'status': status, 'comments': comments, 'created_on': now(), 'updated_on': now(), 'due_date': due_date, 'technical_quality': tq, 'deficiency_identification': di, 'rule_interpretation': ri, 'report_writing': rw, 'decision_quality': dq, 'report_file_id': file_id, 'vessel_name': vessel}
                    db_insert('technical_reviews', row)
                    db_insert('technical_review_assignments', {'assignment_id': uid('TRA'), 'review_id': rid, 'assigned_reviewer_id': actor_get(actor, 'user_id'), 'assigned_reviewer_name': actor_get(actor, 'name'), 'discipline': discipline, 'assigned_by': actor_get(actor, 'user_id'), 'assigned_by_name': actor_get(actor, 'name'), 'assigned_on': now(), 'due_date': due_date, 'status': 'Assigned', 'reason': 'Assigned at review creation', 'created_on': now(), 'updated_on': now()})
                    db_insert('technical_reviews', {'review_id': rid, 'review_type': 'Survey Report Review', 'user_id': uidv, 'name': name, 'scope': scope, 'subject_name': vessel, 'source_record_id': report_ref, 'reviewer_id': actor_get(actor, 'user_id'), 'reviewer_name': actor_get(actor, 'name'), 'technical_quality': tq, 'deficiency_identification': di, 'rule_interpretation': ri, 'report_writing': rw, 'decision_quality': dq, 'overall_score': score, 'decision': decision, 'status': 'Completed', 'comments': comments, 'created_on': now(), 'updated_on': now(), 'due_date': ''})
                    audit('Technical Review Created', f'{rid} · Survey Report Review', actor=actor, entity_type='technical_reviews', entity_id=rid, reason=reason.strip(), after_value=json.dumps({'type': 'Survey Report Review', 'score': score, 'decision': decision}, default=str))
                    if decision in ['Rejected', 'Re-training Required']:
                        existing_ncr = db_all('competency_ncrs')
                        dup = False
                        if not existing_ncr.empty and 'source_record_id' in existing_ncr.columns:
                            dup = not existing_ncr[(existing_ncr['source_record_id'].astype(str) == rid) & existing_ncr.get('status', '').astype(str).isin(['Open', 'Containment', 'Corrective Action', 'Verification'])].empty
                        if not dup:
                            nid = uid('CNCR')
                            db_insert('competency_ncrs', {'ncr_id': nid, 'user_id': uidv, 'name': name, 'source': 'Technical Review', 'source_record_id': rid, 'scope': scope, 'ncr_type': 'Survey Report Quality', 'description': comments or decision, 'severity': 'High' if decision == 'Rejected' else 'Medium', 'impact_on_authorization': 'Review during revalidation', 'status': 'Open', 'corrective_action': 'Retraining/further supervision required', 'raised_by': actor_get(actor, 'name'), 'raised_on': today(), 'closed_on': ''})
                    st.success(f'Review {rid} recorded — {score:.1f}%.')
                    st.rerun()
    with tabs[2]:
        if not (can_action(actor, 'Technical Reviews', 'Review', 'Department') or can_action(actor, 'Technical Reviews', 'Approve', 'Organization-wide')):
            st.info('You do not have permission to record Plan Review QA.')
        else:
            with st.form('technical_pqa'):
                name, uidv, _ = select_person('Plan Appraiser', ['Trainee', 'Plan Appraiser', 'On Probation'], key='tr_pqa_person')
                scope = st.selectbox('Plan Scope', ['Plan Approval Hull', 'Plan Approval Machinery', 'Plan Approval Electrical'], key='tr_pqa_scope')
                discipline = st.selectbox('Technical Discipline', ['Plan','Hull','Machinery','Electrical'], key='tr_pqa_discipline')
                project = st.text_input('Project / Drawing Package', key='tr_pqa_project')
                plan_ref = st.text_input('Plan Review Reference', key='tr_pqa_ref')
                file_id = st.text_input('Plan File ID / Evidence Reference', key='tr_pqa_file')
                due_date = st.text_input('Review Due Date (YYYY-MM-DD)', key='tr_pqa_due')
                a, b, c, d = st.columns(4)
                cq = a.slider('Comments Quality', 1, 5, 3, key='tr_pqa_cq')
                missed = b.number_input('Missed Findings', 0, 100, 0, key='tr_pqa_missed')
                turnaround = c.number_input('Turnaround Days', 0, 365, 5, key='tr_pqa_turn')
                acc = d.slider('Accuracy', 1, 5, 3, key='tr_pqa_acc')
                result = st.selectbox('Result', ['Accepted', 'Accepted with Comments', 'Rejected', 'Further Supervision Required'], key='tr_pqa_result')
                comments = st.text_area('Reviewer Comments', key='tr_pqa_comments')
                reason = st.text_area('Review Reason / Context *', key='tr_pqa_reason')
                submitted = st.form_submit_button('Record Plan Review QA', type='primary')
            if submitted:
                if not uidv or not reason.strip():
                    st.error('Plan Appraiser and review reason are required.')
                else:
                    score = max(0, round((cq + acc) / 10 * 100 - missed * 5 - max(0, turnaround - 10), 2))
                    rid = uid('TRR')
                    status = 'Rejected' if result == 'Rejected' else 'Approved with Comments' if result == 'Accepted with Comments' else 'Open'
                    row = {'review_id': rid, 'review_type': 'Plan Review QA', 'discipline': discipline, 'user_id': uidv, 'name': name, 'scope': scope, 'subject_name': project, 'source_record_id': plan_ref or file_id, 'reviewer_id': actor_get(actor, 'user_id'), 'reviewer_name': actor_get(actor, 'name'), 'assigned_reviewer_id': actor_get(actor, 'user_id'), 'assigned_reviewer_name': actor_get(actor, 'name'), 'overall_score': score, 'decision': result, 'status': status, 'comments': comments, 'created_on': now(), 'updated_on': now(), 'due_date': due_date, 'comments_quality': cq, 'missed_findings': missed, 'turnaround_days': turnaround, 'accuracy_score': acc, 'project_name': project, 'plan_file_id': file_id}
                    db_insert('technical_reviews', row)
                    db_insert('technical_review_assignments', {'assignment_id': uid('TRA'), 'review_id': rid, 'assigned_reviewer_id': actor_get(actor, 'user_id'), 'assigned_reviewer_name': actor_get(actor, 'name'), 'discipline': discipline, 'assigned_by': actor_get(actor, 'user_id'), 'assigned_by_name': actor_get(actor, 'name'), 'assigned_on': now(), 'due_date': due_date, 'status': 'Assigned', 'reason': 'Assigned at review creation', 'created_on': now(), 'updated_on': now()})
                    db_insert('technical_reviews', {'review_id': rid, 'review_type': 'Plan Review QA', 'user_id': uidv, 'name': name, 'scope': scope, 'subject_name': project, 'source_record_id': plan_ref, 'reviewer_id': actor_get(actor, 'user_id'), 'reviewer_name': actor_get(actor, 'name'), 'assigned_reviewer_id': actor_get(actor, 'user_id'), 'assigned_reviewer_name': actor_get(actor, 'name'), 'comments_quality': cq, 'missed_findings': missed, 'turnaround_days': turnaround, 'accuracy_score': acc, 'overall_score': score, 'decision': result, 'status': 'Completed', 'comments': comments, 'created_on': now(), 'updated_on': now(), 'due_date': ''})
                    audit('Technical Review Created', f'{rid} · Plan Review QA', actor=actor, entity_type='technical_reviews', entity_id=rid, reason=reason.strip(), after_value=json.dumps({'type': 'Plan Review QA', 'score': score, 'result': result}, default=str))
                    if result in ['Rejected', 'Further Supervision Required'] or missed > 0:
                        existing_ncr = db_all('competency_ncrs')
                        dup = False
                        if not existing_ncr.empty and 'source_record_id' in existing_ncr.columns:
                            dup = not existing_ncr[(existing_ncr['source_record_id'].astype(str) == rid) & existing_ncr.get('status', '').astype(str).isin(['Open', 'Containment', 'Corrective Action', 'Verification'])].empty
                        if not dup:
                            nid = uid('CNCR')
                            db_insert('competency_ncrs', {'ncr_id': nid, 'user_id': uidv, 'name': name, 'source': 'Technical Review', 'source_record_id': rid, 'scope': scope, 'ncr_type': 'Plan Review Quality', 'description': comments or result, 'severity': 'High' if missed >= 3 or result == 'Rejected' else 'Medium', 'impact_on_authorization': 'Review during revalidation/restriction', 'status': 'Open', 'corrective_action': 'Additional plan review supervision', 'raised_by': actor_get(actor, 'name'), 'raised_on': today(), 'closed_on': ''})
                    st.success(f'Review {rid} recorded — {score:.1f}%.')
                    st.rerun()
    with tabs[3]:
        if common.empty:
            st.info('No technical reviews recorded yet.')
        else:
            labels = (common['review_id'].astype(str) + ' — ' + common['review_type'].astype(str) + ' — ' + common['name'].astype(str)).tolist()
            selected = st.selectbox('Review', labels, key='tr_detail_select')
            rid = selected.split(' — ', 1)[0]
            row = common[common['review_id'].astype(str) == rid].iloc[0]
            d1, d2, d3, d4 = st.columns(4)
            d1.metric('Score', f"{float(row.get('overall_score') or 0):.1f}%")
            d2.metric('Status', str(row.get('status', '—')))
            d3.metric('Decision', str(row.get('decision', '—')))
            d4.metric('Reviewer', str(row.get('reviewer_name', '—')))
            st.markdown(f"**Employee / Subject:** {row.get('name', '')} / {row.get('subject_name', '')}")
            st.markdown(f"**Scope:** {row.get('scope', '')}  ")
            st.markdown(f"**Source Reference:** {row.get('source_record_id', '')}")
            st.markdown(f"**Comments:** {row.get('comments', '')}")
            if st.button('Open NCR / Corrective Action', key='tr_open_ncr'):
                st.session_state['psb_current_page'] = 'NCR / Corrective Action'
                st.rerun()

def accreditation_readiness_page(actor):
    """Calculated accreditation readiness dashboard.

    This is a governance/readiness view over existing authoritative records. It does
    not recreate Training, Competency, Authorization, QMS or NCR workflows.
    """
    ensure_accreditation_schema()
    ensure_interpretation_schema()
    ensure_client_feedback_schema()
    st.header('Accreditation Readiness')
    st.caption('A calculated readiness view using existing PSB records. Gaps link back to the owning workflow rather than creating duplicate compliance records.')
    standards = ['IMO RO Code', 'ISO 9001', 'ISO/IEC 17020', 'IACS PR7', 'Internal QMS']
    departments = ['All'] + [str(x) for x in db_all('departments').get('department_name', pd.Series(dtype=str)).dropna().tolist()] if not db_all('departments').empty else ['All']
    f1, f2, f3 = st.columns(3)
    with f1:
        standard = st.selectbox('Standard', standards, key='acc_std')
    with f2:
        period = st.selectbox('Assessment Period', [str(date.today().year), str(date.today().year - 1), str(date.today().year + 1)], key='acc_period')
    with f3:
        dept_filter = st.selectbox('Department', departments, key='acc_dept')
    users = db_all('users')
    if not users.empty and dept_filter != 'All' and ('department' in users.columns):
        users = users[users['department'].astype(str).str.contains(dept_filter, case=False, na=False)]
    training = db_all('training_records')
    comp = db_all('competency_matrix')
    witness = db_all('witness_surveys')
    supervised = db_all('supervised_activities')
    auth = db_all('authorization_requests')
    certs = db_all('authorization_certificates')
    ncr = db_all('competency_ncrs')
    capa = db_all('capa_register')
    audits = db_all('qms_audits')
    qms_comp = db_all('qms_compliance_items')
    tech = db_all('technical_reviews')
    cpds = db_all('cpd_records')
    evidence = db_all('accreditation_evidence')
    active_people = len(users[users.get('status', pd.Series(dtype=str)).astype(str).str.lower().isin(['active', 'yes'])]) if not users.empty and 'status' in users.columns else len(users)
    trained = 0
    if not training.empty and 'user_id' in training.columns:
        passed = training[training.get('test_status', pd.Series(dtype=str)).astype(str).str.lower().eq('passed')]
        trained = passed['user_id'].nunique()
    training_score = trained / active_people * 100 if active_people else 0
    comp_score = 0.0
    if not comp.empty:
        authorized_levels = comp.get('status', pd.Series(dtype=str)).astype(str).str.contains('Authorized|Ready', case=False, na=False)
        comp_score = authorized_levels.sum() / len(comp) * 100 if len(comp) else 0
    auth_score = 0.0
    if not auth.empty:
        valid = auth[auth.get('status', pd.Series(dtype=str)).astype(str).str.contains('Approved|Authorized|Active', case=False, na=False)]
        auth_score = len(valid) / len(auth) * 100 if len(auth) else 0
    qms_score = 100.0
    if not qms_comp.empty:
        closed = qms_comp.get('status', pd.Series(dtype=str)).astype(str).str.contains('Compliant|Closed|Complete|Verified', case=False, na=False)
        qms_score = closed.sum() / len(qms_comp) * 100
    tech_score = 100.0
    if not tech.empty:
        approved = tech.get('decision', pd.Series(dtype=str)).astype(str).str.contains('Accepted|Approved|Pass', case=False, na=False)
        tech_score = approved.sum() / len(tech) * 100
    ncr_open = 0
    for frame in (ncr, capa):
        if not frame.empty and 'status' in frame.columns:
            ncr_open += int((~frame['status'].astype(str).str.contains('Closed|Resolved|Complete', case=False, na=False)).sum())
    ncr_score = max(0.0, 100.0 - min(ncr_open * 10, 100))
    evidence_score = 100.0
    if not evidence.empty:
        ready = evidence.get('status', pd.Series(dtype=str)).astype(str).str.contains('Ready|Verified', case=False, na=False)
        evidence_score = ready.sum() / len(evidence) * 100
    weights = {'Training': 0.15, 'Competency': 0.2, 'Authorization': 0.2, 'QMS': 0.2, 'Technical Reviews': 0.1, 'NCR/CAPA': 0.1, 'Evidence': 0.05}
    scores = {'Training': training_score, 'Competency': comp_score, 'Authorization': auth_score, 'QMS': qms_score, 'Technical Reviews': tech_score, 'NCR/CAPA': ncr_score, 'Evidence': evidence_score}
    overall = sum((scores[k] * weights[k] for k in scores))
    status = 'Ready' if overall >= 90 and ncr_open == 0 else 'Ready with Actions' if overall >= 75 else 'Partial' if overall >= 60 else 'Gap'
    metrics = [('Overall Readiness', f'{overall:.0f}%'), ('Training', f'{training_score:.0f}%'), ('Competency', f'{comp_score:.0f}%'), ('Authorization', f'{auth_score:.0f}%'), ('QMS', f'{qms_score:.0f}%'), ('Open NCR/CAPA', str(ncr_open))]
    cols = st.columns(6)
    for c, (label, val) in zip(cols, metrics):
        c.metric(label, val)
    if status == 'Ready':
        st.success('Accreditation readiness: READY')
    elif status == 'Ready with Actions':
        st.warning('Accreditation readiness: READY WITH ACTIONS')
    elif status == 'Partial':
        st.warning('Accreditation readiness: PARTIAL')
    else:
        st.error('Accreditation readiness: GAP')
    tabs = st.tabs(['Readiness Areas', 'Evidence & Gaps', 'Assessment Record'])
    with tabs[0]:
        rows = pd.DataFrame([{'Area': k, 'Score': round(v, 1), 'Weight': f'{weights[k] * 100:.0f}%', 'Status': 'Ready' if v >= 90 else 'Watch' if v >= 75 else 'Gap'} for k, v in scores.items()])
        table(rows)
        st.bar_chart(rows.set_index('Area')['Score'])
    with tabs[1]:
        existing = evidence[evidence.get('standard', pd.Series(dtype=str)).astype(str).eq(standard)] if not evidence.empty and 'standard' in evidence.columns else pd.DataFrame()
        if not existing.empty:
            show = existing[[c for c in ['clause', 'requirement', 'source_module', 'linked_id', 'evidence_type', 'severity', 'status', 'owner', 'due_date', 'last_reviewed'] if c in existing.columns]]
            table(show, max_rows=200)
        else:
            st.info('No manually registered evidence for this standard. Readiness is still calculated from the live PSB systems.')
        if can_action(actor, 'Accreditation Readiness', 'Create', 'Organization-wide') or can_action(actor, 'Accreditation Readiness', 'Review', 'Organization-wide'):
            with st.expander('Register an accreditation evidence gap/evidence item'):
                with st.form('acc_evidence_form'):
                    a, b, c = st.columns(3)
                    with a:
                        clause = st.text_input('Clause / Requirement Ref')
                        req = st.text_area('Requirement')
                    with b:
                        source_module = st.selectbox('Source Module', ['Training', 'Competency', 'Authorization', 'QMS', 'Technical Reviews', 'NCR/CAPA', 'CPD', 'Knowledge Library', 'Other'])
                        evidence_type = st.selectbox('Evidence Type', ['Document', 'Record', 'KPI', 'Audit Finding', 'Interview', 'Observation', 'System Record'])
                    with c:
                        severity = st.selectbox('Severity', ['Informational', 'Minor', 'Major', 'Critical'])
                        owner = st.text_input('Owner', actor_get(actor, 'name'))
                    linked_id = st.text_input('Linked Record ID (optional)')
                    summary = st.text_area('Evidence / Gap Summary')
                    due = st.date_input('Due Date', date.today())
                    item_status = st.selectbox('Status', ['Ready', 'Partial', 'Gap', 'Not Applicable', 'Verified'])
                    if st.form_submit_button('Save Evidence Item') and req.strip():
                        eid = uid('ACC')
                        db_insert('accreditation_evidence', {'evidence_id': eid, 'standard': standard, 'clause': clause.strip(), 'requirement': req.strip(), 'linked_table': source_module, 'linked_id': linked_id.strip(), 'evidence_summary': summary.strip(), 'status': item_status, 'owner': owner.strip(), 'last_reviewed': today(), 'evidence_type': evidence_type, 'severity': severity, 'due_date': str(due), 'verified_by': actor_get(actor, 'name'), 'verified_on': today() if item_status == 'Verified' else '', 'source_module': source_module, 'created_on': now(), 'updated_on': now()})
                        audit('Accreditation Evidence Updated', f'{standard} {clause}: {item_status}', actor=actor, entity_type='accreditation_evidence', entity_id=eid, reason='Accreditation evidence/gap register update')
                        st.success('Evidence item recorded.')
                        st.rerun()
    with tabs[2]:
        st.markdown('### Assessment Record')
        st.write(f'**Standard:** {standard}  |  **Period:** {period}  |  **Readiness:** {status}  |  **Score:** {overall:.1f}%')
        if can_action(actor, 'Accreditation Readiness', 'Approve', 'Organization-wide'):
            summary = st.text_area('Executive Summary', f'Calculated readiness for {standard}: {status} ({overall:.1f}%).', key='acc_summary')
            approval = st.selectbox('Approval Status', ['Draft', 'Submitted', 'Approved', 'Returned'])
            approved_by = st.text_input('Approved By', actor_get(actor, 'name'))
            if st.button('Save Assessment Snapshot', type='primary'):
                aid = uid('ACCASESS')
                db_insert('accreditation_assessments', {'assessment_id': aid, 'standard': standard, 'assessment_period': period, 'overall_score': round(overall, 2), 'readiness_status': status, 'assessed_on': today(), 'assessed_by': actor_get(actor, 'name'), 'approved_by': approved_by.strip(), 'approval_status': approval, 'executive_summary': summary.strip(), 'created_on': now(), 'updated_on': now()})
                audit('Accreditation Assessment Saved', f'{standard} {period}: {status} {overall:.1f}%', actor=actor, entity_type='accreditation_assessments', entity_id=aid, reason='Accreditation readiness assessment snapshot')
                st.success('Assessment snapshot saved.')
        hist = db_all('accreditation_assessments')
        if not hist.empty:
            table(hist.sort_values('created_on', ascending=False), max_rows=100)

def interpretation_portal_page(actor):
    """Controlled Interpretation + Rule Development workspace.

    One lifecycle: question -> technical interpretation -> review -> approval ->
    publication to Knowledge Library -> change/impact tracking.
    """
    role = actor_get(actor, 'role')
    st.header('Interpretation Portal')
    st.caption('Controlled technical interpretations and rule-development decisions. Approved knowledge is published through the existing Knowledge Library.')
    can_manage = can_action(actor, 'Interpretation Portal', 'Manage', 'Organization-wide') or can_action(actor, 'Interpretation Portal', 'Create', 'Department')
    can_review = can_action(actor, 'Interpretation Portal', 'Review', 'Organization-wide') or can_action(actor, 'Interpretation Portal', 'Approve', 'Organization-wide')
    interpretations = db_all('technical_interpretations')
    changes = db_all('rule_change_requests')
    if interpretations.empty:
        interpretations = pd.DataFrame(columns=['interpretation_id', 'title', 'discipline', 'related_rule', 'question', 'interpretation', 'approval_status', 'priority', 'rule_family', 'submitted_on', 'issue_date', 'published_knowledge_id'])
    if changes.empty:
        changes = pd.DataFrame(columns=['change_id', 'title', 'related_rule', 'change_type', 'priority', 'status', 'owner_name', 'proposed_revision', 'effective_date', 'source_interpretation_id'])
    stats = [('Open Questions', int(interpretations.get('approval_status', pd.Series(dtype=str)).astype(str).isin(['Draft', 'Submitted', 'Under Review']).sum())), ('Awaiting Approval', int((interpretations.get('approval_status', pd.Series(dtype=str)).astype(str) == 'Pending Approval').sum())), ('Published', int((interpretations.get('approval_status', pd.Series(dtype=str)).astype(str) == 'Published').sum())), ('Rule Changes', int((changes.get('status', pd.Series(dtype=str)).astype(str).isin(['Draft', 'Under Review', 'Approved', 'Implementation']) if not changes.empty else pd.Series(dtype=bool)).sum()))]
    cols = st.columns(4)
    for c, (label, value) in zip(cols, stats):
        with c:
            st.metric(label, value)
    tabs = st.tabs(['Register', 'Submit Interpretation', 'Review & Approval', 'Rule Development', 'Publication & Impact'])
    with tabs[0]:
        st.markdown('### Interpretation Register')
        f1, f2, f3, f4 = st.columns(4)
        search = f1.text_input('Search', key='interp_search')
        discipline_filter = f2.selectbox('Discipline', ['All'] + sorted([str(x) for x in interpretations.get('discipline', pd.Series(dtype=str)).dropna().unique().tolist() if str(x)]), key='interp_disc')
        status_filter = f3.selectbox('Status', ['All', 'Draft', 'Submitted', 'Under Review', 'Pending Approval', 'Published', 'Returned', 'Withdrawn', 'Superseded'], key='interp_status')
        priority_filter = f4.selectbox('Priority', ['All', 'Critical', 'High', 'Medium', 'Low'], key='interp_priority')
        view = interpretations.copy()
        if search:
            mask = view.apply(lambda r: search.lower() in ' '.join(map(str, r.values)).lower(), axis=1)
            view = view[mask]
        if discipline_filter != 'All' and 'discipline' in view.columns:
            view = view[view['discipline'].astype(str) == discipline_filter]
        if status_filter != 'All' and 'approval_status' in view.columns:
            view = view[view['approval_status'].astype(str) == status_filter]
        if priority_filter != 'All' and 'priority' in view.columns:
            view = view[view['priority'].astype(str) == priority_filter]
        show_cols = [c for c in ['interpretation_id', 'title', 'discipline', 'rule_family', 'related_rule', 'priority', 'approval_status', 'revision', 'issue_date', 'published_knowledge_id'] if c in view.columns]
        if not view.empty:
            table(view[show_cols].sort_values('issue_date', ascending=False) if 'issue_date' in view.columns else view[show_cols], max_rows=200)
        else:
            st.info('No interpretations match the current filters.')
        if not interpretations.empty:
            selected = st.selectbox('Open interpretation', ['—'] + interpretations['interpretation_id'].astype(str).tolist(), key='interp_open')
            if selected != '—':
                rec = interpretations[interpretations['interpretation_id'].astype(str) == selected].iloc[0].to_dict()
                st.markdown(f"### {rec.get('title', 'Untitled')} · `{selected}`")
                a, b, c = st.columns(3)
                a.metric('Status', rec.get('approval_status', '—'))
                b.metric('Priority', rec.get('priority', '—'))
                c.metric('Revision', rec.get('revision', '—'))
                st.markdown(f"**Discipline:** {rec.get('discipline', '—')}  |  **Rule / Clause:** {rec.get('related_rule', '—')}  |  **Rule family:** {rec.get('rule_family', '—')}")
                st.markdown('**Question / Case**')
                st.write(rec.get('question', '—'))
                st.markdown('**Interpretation / Decision**')
                st.write(rec.get('interpretation', '—'))
                if rec.get('published_knowledge_id'):
                    st.success(f"Published to Knowledge Library: {rec.get('published_knowledge_id')}")
    with tabs[1]:
        st.markdown('### Submit a Technical Interpretation')
        if not can_manage:
            st.info('This workflow is restricted to technical / quality / rule-development roles.')
        else:
            with st.form('submit_interpretation_form'):
                c1, c2, c3 = st.columns(3)
                with c1:
                    title = st.text_input('Title *')
                    discipline = st.selectbox('Discipline', ['Hull', 'Machinery', 'Electrical', 'Statutory', 'Plan Approval', 'Audit', 'Industrial', 'Rule Development'])
                with c2:
                    rule_family = st.text_input('Rule Family / Topic')
                    related_rule = st.text_input('Related Rule / Clause')
                with c3:
                    priority = st.selectbox('Priority', ['Critical', 'High', 'Medium', 'Low'], index=2)
                    review_due = st.date_input('Review Due', date.today())
                question = st.text_area('Question / Technical Case *', height=120)
                proposed = st.text_area('Proposed Interpretation / Technical Position', height=140)
                source_ref = st.text_input('Source Reference / Case ID (optional)')
                impact = st.text_area('Initial Impact Summary', height=90)
                if st.form_submit_button('Submit for Technical Review', type='primary'):
                    if not title.strip() or not question.strip():
                        st.error('Title and Question / Technical Case are required.')
                    else:
                        iid = uid('INT')
                        payload = {'interpretation_id': iid, 'title': title.strip(), 'discipline': discipline, 'rule_family': rule_family.strip(), 'related_rule': related_rule.strip(), 'question': question.strip(), 'interpretation': proposed.strip(), 'approved_by': '', 'approval_status': 'Submitted', 'revision': 'Rev.0', 'issue_date': '', 'requester_id': actor_get(actor, 'user_id'), 'requester_name': actor_get(actor, 'name'), 'submitted_on': now(), 'review_due_date': str(review_due), 'priority': priority, 'impact_summary': impact.strip(), 'created_on': now(), 'updated_on': now()}
                        db_insert('technical_interpretations', payload)
                        audit('Interpretation Submitted', f'{iid}: {title.strip()}', actor=actor, entity_type='technical_interpretations', entity_id=iid, reason='Submitted for technical interpretation review', after_value='Submitted')
                        st.success(f'Interpretation {iid} submitted.')
                        st.rerun()
    with tabs[2]:
        st.markdown('### Technical Review & Approval')
        if not can_review:
            st.info('You do not have the required review authority.')
        else:
            reviewable = interpretations[interpretations.get('approval_status', pd.Series(dtype=str)).astype(str).isin(['Submitted', 'Under Review', 'Pending Approval', 'Returned'])] if not interpretations.empty else interpretations
            if reviewable.empty:
                st.success('No interpretation is currently awaiting review.')
            else:
                rid = st.selectbox('Interpretation', reviewable['interpretation_id'].astype(str).tolist(), key='interp_review_id')
                rec = reviewable[reviewable['interpretation_id'].astype(str) == rid].iloc[0].to_dict()
                st.info(f"**{rec.get('title', '')}** · {rec.get('discipline', '')} · Rule: {rec.get('related_rule', '—')}")
                st.write(f"**Question:** {rec.get('question', '—')}")
                st.write(f"**Proposed Position:** {rec.get('interpretation', '—')}")
                decision = st.selectbox('Decision', ['Under Review', 'Return for Revision', 'Recommend Approval', 'Reject'], key='interp_decision')
                comments = st.text_area('Technical Review Comments', key='interp_comments')
                reason = st.text_input('Decision Reason', key='interp_reason')
                if st.button('Record Review', type='primary', key='record_interp_review'):
                    current = rec.get('approval_status', 'Submitted')
                    db_insert('interpretation_reviews', {'review_id': uid('INTREV'), 'interpretation_id': rid, 'reviewer_id': actor_get(actor, 'user_id'), 'reviewer_name': actor_get(actor, 'name'), 'stage': 'Technical Review', 'decision': decision, 'comments': comments.strip(), 'reviewed_on': now(), 'created_on': now()})
                    next_status = {'Under Review': 'Under Review', 'Return for Revision': 'Returned', 'Recommend Approval': 'Pending Approval', 'Reject': 'Withdrawn'}[decision]
                    db_update('technical_interpretations', 'interpretation_id', rid, {'approval_status': next_status, 'updated_on': now()})
                    audit('Interpretation Review', f'{rid}: {decision}', actor=actor, entity_type='technical_interpretations', entity_id=rid, reason=reason or comments.strip(), before_value=current, after_value=next_status)
                    st.success(f'Review recorded: {next_status}')
                    st.rerun()
                if rec.get('approval_status') == 'Pending Approval':
                    st.markdown('#### Approval Gate')
                    approve = st.radio('Approval', ['Approve', 'Return for Revision', 'Withdraw'], horizontal=True, key='interp_approval')
                    approval_reason = st.text_area('Approval / Return Reason', key='interp_approval_reason')
                    if st.button('Confirm Governance Decision', key='confirm_interp_approval'):
                        if str(rec.get('requester_id') or '') == str(actor_get(actor, 'user_id')) and approve == 'Approve':
                            st.error('Maker-checker control: the requester cannot approve their own interpretation.')
                            return
                        new_status = {'Approve': 'Approved', 'Return for Revision': 'Returned', 'Withdraw': 'Withdrawn'}[approve]
                        db_update('technical_interpretations', 'interpretation_id', rid, {'approval_status': new_status, 'approved_by': actor_get(actor, 'name') if new_status == 'Approved' else '', 'approval_date': now() if new_status == 'Approved' else '', 'updated_on': now()})
                        audit('Interpretation Governance Decision', f'{rid}: {approve}', actor=actor, entity_type='technical_interpretations', entity_id=rid, reason=approval_reason.strip(), after_value=new_status)
                        st.success(f'Interpretation {new_status}.')
                        st.rerun()
    with tabs[3]:
        st.markdown('### Rule Development & Change Control')
        st.caption('Rule changes are tracked here; the actual approved rule/document remains in the existing Rule Library / Knowledge Library.')
        change_view = changes.copy()
        if not change_view.empty:
            table(change_view[[c for c in ['change_id', 'title', 'related_rule', 'change_type', 'priority', 'status', 'owner_name', 'proposed_revision', 'effective_date'] if c in change_view.columns]], max_rows=150)
        if can_manage:
            with st.form('rule_change_form'):
                a, b, c = st.columns(3)
                with a:
                    change_title = st.text_input('Change Title *')
                    change_type = st.selectbox('Change Type', ['New Rule', 'Revision', 'Technical Circular', 'Interpretation Change', 'Withdrawal'])
                with b:
                    change_rule = st.text_input('Related Rule / Document')
                    proposed_revision = st.text_input('Proposed Revision', 'Rev.1')
                with c:
                    change_priority = st.selectbox('Change Priority', ['Critical', 'High', 'Medium', 'Low'], index=2)
                    effective_date = st.date_input('Proposed Effective Date', date.today())
                reason = st.text_area('Reason / Trigger *')
                impact_summary = st.text_area('Impact Summary')
                affected_departments = st.text_input('Affected Departments', 'Survey NSC; Survey Inservice; Plan Appraisal; QMS')
                affected_modules = st.text_input('Affected System Modules', 'Knowledge Library; Training; Technical Reviews')
                owner_name = st.text_input('Responsible Owner', actor_get(actor, 'name'))
                if st.form_submit_button('Create Change Request', type='primary'):
                    if not change_title.strip() or not reason.strip():
                        st.error('Change Title and Reason / Trigger are required.')
                    else:
                        cid = uid('RULE')
                        db_insert('rule_change_requests', {'change_id': cid, 'title': change_title.strip(), 'related_rule': change_rule.strip(), 'change_type': change_type, 'reason': reason.strip(), 'impact_summary': impact_summary.strip(), 'affected_departments': affected_departments.strip(), 'affected_modules': affected_modules.strip(), 'priority': change_priority, 'owner_id': actor_get(actor, 'user_id'), 'owner_name': owner_name.strip(), 'status': 'Draft', 'proposed_revision': proposed_revision.strip(), 'effective_date': str(effective_date), 'source_interpretation_id': '', 'approved_by': '', 'approved_on': '', 'created_by': actor_get(actor, 'user_id'), 'created_on': now(), 'updated_on': now()})
                        audit('Rule Change Created', f'{cid}: {change_title.strip()}', actor=actor, entity_type='rule_change_requests', entity_id=cid, reason=reason.strip(), after_value='Draft')
                        st.success(f'Rule change request {cid} created.')
                        st.rerun()
    with tabs[4]:
        st.markdown('### Publication & Impact')
        approved = interpretations[interpretations.get('approval_status', pd.Series(dtype=str)).astype(str) == 'Approved'] if not interpretations.empty else interpretations
        if approved.empty:
            st.info('No approved interpretation is currently available for publication.')
        else:
            pub_id = st.selectbox('Approved Interpretation', approved['interpretation_id'].astype(str).tolist(), key='interp_pub_id')
            rec = approved[approved['interpretation_id'].astype(str) == pub_id].iloc[0].to_dict()
            st.write(f"**{rec.get('title', '')}** — {rec.get('discipline', '')} — {rec.get('related_rule', '—')}")
            existing_kid = rec.get('published_knowledge_id', '')
            if existing_kid:
                st.success(f'Already published to Knowledge Library as `{existing_kid}`.')
            elif can_manage:
                summary = st.text_area('Controlled Library Summary', rec.get('interpretation', ''), key='pub_summary')
                audience = st.text_input('Audience', 'All technical staff', key='pub_audience')
                keywords = st.text_input('Keywords', key='pub_keywords')
                mandatory_ack = st.selectbox('Acknowledgement Required', ['No', 'Yes'], key='pub_ack')
                if st.button('Publish to Knowledge Library', type='primary', key='publish_interp'):
                    kid = uid('KNW')
                    db_insert('knowledge_library', {'knowledge_id': kid, 'title': rec.get('title', ''), 'category': 'Technical Interpretation', 'summary': summary.strip(), 'standard': rec.get('related_rule', ''), 'revision': rec.get('revision', 'Rev.0'), 'issue_date': today(), 'file_id': '', 'mandatory_ack': mandatory_ack, 'uploaded_by': actor_get(actor, 'name'), 'created_on': now(), 'source_interpretation_id': pub_id, 'status': 'Published', 'audience': audience.strip(), 'owner_name': actor_get(actor, 'name'), 'approved_by': rec.get('approved_by', actor_get(actor, 'name')), 'approved_on': now(), 'effective_from': rec.get('effective_date', today()), 'review_due_date': rec.get('review_due_date', today()), 'keywords': keywords.strip(), 'updated_on': now()})
                    db_insert('knowledge_versions', {'version_id': uid('KVER'), 'knowledge_id': kid, 'version_no': rec.get('revision', 'Rev.0'), 'revision_date': today(), 'change_summary': 'Published approved technical interpretation', 'file_link': '', 'uploaded_by': actor_get(actor, 'name'), 'approved_by': rec.get('approved_by', actor_get(actor, 'name')), 'status': 'Published', 'created_on': now()})
                    db_update('technical_interpretations', 'interpretation_id', pub_id, {'approval_status': 'Published', 'published_knowledge_id': kid, 'issue_date': today(), 'updated_on': now()})
                    audit('Interpretation Published', f'{pub_id} published as {kid}', actor=actor, entity_type='technical_interpretations', entity_id=pub_id, reason='Approved technical interpretation published to controlled Knowledge Library', after_value=kid)
                    st.success(f'Published as Knowledge Library item {kid}.')
                    st.rerun()
        st.markdown('#### Impact Review')
        impact_changes = changes[changes.get('status', pd.Series(dtype=str)).astype(str).isin(['Draft', 'Under Review', 'Approved', 'Implementation'])] if not changes.empty else changes
        if not impact_changes.empty:
            table(impact_changes[[c for c in ['change_id', 'title', 'affected_departments', 'affected_modules', 'priority', 'status', 'effective_date'] if c in impact_changes.columns]], max_rows=100)
            st.caption('Use the change record to coordinate updates in Training, Technical Reviews, QMS and the Knowledge Library. Those modules remain authoritative for their own records.')
