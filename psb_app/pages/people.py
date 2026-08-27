from psb_app.common import (
    DEPARTMENTS,
    ROLES,
    SCOPES,
    actor_get,
    allowed_user_ids,
    audit,
    can_action,
    date,
    datetime,
    days_until,
    db_all,
    db_insert,
    db_update,
    db_where,
    first_row,
    json,
    now,
    pd,
    re,
    restrict_user_frame,
    split_list,
    st,
    timedelta,
    today,
    uid,
)

def employee_profile_page(actor):
    """360-degree employee view.

    This page is intentionally read-only. It is a consolidated view over the
    authoritative Users, Development, Training, Competency, Authorization,
    Performance, Files and Audit records; it does not create duplicate workflows.
    """
    st.header('Employee Profile')
    st.caption('One 360° view of the employee. Business records remain owned by their respective modules.')
    users = db_all('users')
    if users.empty:
        st.info('No employee records are available.')
        return
    actor_role = actor_get(actor, 'role')
    can_view_all = can_action(actor, 'Employee Profile', 'View', 'Organization-wide')
    if can_view_all:
        visible = users.copy()
    else:
        visible_ids = allowed_user_ids(actor, users, db_all('user_departments'))
        visible = users[users['user_id'].astype(str).isin(visible_ids)].copy()
    if visible.empty:
        st.warning("You do not have access to another employee's profile.")
        return
    if can_view_all:
        c1, c2, c3 = st.columns([2, 1, 1])
        search = c1.text_input('Search employee', placeholder='Name, Employee ID, email', key='emp_profile_search')
        dept_options = ['All'] + sorted({d for value in visible.get('department', pd.Series(dtype=str)).fillna('') for d in split_list(value)})
        dept = c2.selectbox('Department', dept_options, key='emp_profile_dept')
        status = c3.selectbox('Account Status', ['All'] + sorted(visible.get('status', pd.Series(dtype=str)).fillna('').astype(str).unique().tolist()), key='emp_profile_status')
        if search.strip():
            q = search.strip().lower()
            mask = visible.apply(lambda r: q in ' '.join((str(r.get(k, '')) for k in ['name', 'user_id', 'employee_id', 'email'])).lower(), axis=1)
            visible = visible[mask]
        if dept != 'All':
            visible = visible[visible.get('department', '').astype(str).apply(lambda x: dept in split_list(x))]
        if status != 'All':
            visible = visible[visible.get('status', '').astype(str) == status]
    if visible.empty:
        st.info('No employees match the selected filters.')
        return
    people_options = [f"{r.get('name', '')} — {r.get('employee_id', r.get('user_id', ''))} — {r.get('user_id', '')}" for _, r in visible.iterrows()]
    preselected_uid = str(st.session_state.pop('profile_target_user_id', '') or '')
    pre_index = next((i for i, label in enumerate(people_options) if label.endswith(f'— {preselected_uid}')), 0) if preselected_uid else 0
    selected = st.selectbox('Employee', people_options, index=pre_index, key='employee_profile_selected')
    selected_uid = selected.rsplit(' — ', 1)[-1]
    row = first_row(db_where('users', 'user_id = :user_id', (('user_id', selected_uid),))) or {}
    name = actor_get(row, 'name', 'Employee')
    role = actor_get(row, 'role', '—')
    employee_id = actor_get(row, 'employee_id', selected_uid)
    primary_department = actor_get(row, 'primary_department', '')
    all_departments = actor_get(row, 'department', primary_department)
    account_status = actor_get(row, 'status', '—')
    availability = actor_get(row, 'availability', '—')
    location = actor_get(row, 'current_location', '—')
    competency_level = actor_get(row, 'competency_level', 'Not yet assigned')
    st.markdown(f'## {name}')
    st.caption(f'{role}  •  Employee ID: {employee_id}')
    metrics([('Account', account_status), ('Availability', availability), ('Competency', competency_level), ('Primary Department', primary_department or 'Not assigned')])
    info1, info2 = st.columns(2)
    with info1:
        st.markdown('### Organization')
        st.write(f"**Primary Department:** {primary_department or '—'}")
        st.write(f"**Additional Departments:** {', '.join([d for d in split_list(all_departments) if d != primary_department]) or '—'}")
        st.write(f"**Current Location:** {location or '—'}")
        st.write(f"**Availability:** {availability or '—'}")
    with info2:
        st.markdown('### Responsibilities')
        st.write(f"**Assigner:** {actor_get(row, 'assigner_name', '—')}")
        st.write(f"**Trainer / Mentor:** {actor_get(row, 'trainer_name', row.get('tutor_name', row.get('mentor_name', '—')))}")
        st.write(f"**Trainer:** {actor_get(row, 'trainer_name', '—')}")
        st.write(f"**Trainee / Competency Path:** {actor_get(row, 'trainee_path', '—')}")
    st.divider()
    tabs = st.tabs(['Overview', 'Development', 'Training', 'Competency', 'Authorization', 'Performance', 'Documents', 'History'])
    plans = db_where('development_plans', 'user_id = :user_id', (('user_id', selected_uid),))
    training = db_where('training_records', 'user_id = :user_id', (('user_id', selected_uid),))
    competency = db_where('competency_matrix', 'user_id = :user_id', (('user_id', selected_uid),))
    auths = db_where('authorization_requests', 'user_id = :user_id', (('user_id', selected_uid),))
    cpd = db_where('cpd_records', 'user_id = :user_id', (('user_id', selected_uid),))
    feedback = db_where('client_feedback', 'user_id = :user_id', (('user_id', selected_uid),))
    files_df = db_where('files', 'owner_user_id = :user_id', (('user_id', selected_uid),))
    audits = db_where('audit_trail', 'entity_id = :user_id', (('user_id', selected_uid),))
    with tabs[0]:
        total_trainings = len(training)
        completed = int((training['status'].astype(str) == 'Completed').sum()) if not training.empty and 'status' in training else 0
        auth_active = int(auths['status'].astype(str).isin(['Management Approved', 'Active', 'Approved']).sum()) if not auths.empty and 'status' in auths else 0
        open_plans = int((plans['status'].astype(str) != 'Closed').sum()) if not plans.empty and 'status' in plans else 0
        st.markdown('### Current Position')
        metrics([('Training Records', total_trainings), ('Completed Training', completed), ('Open Development Items', open_plans), ('Authorizations', auth_active)])
        st.info('Use the dedicated module pages to create, update, assess or approve records. This profile does not duplicate those workflows.')
        if st.button('Open Development Plans', key=f'profile_dev_{selected_uid}'):
            st.session_state['psb_current_page'] = 'Development Plans'
            st.rerun()
        if st.button('Open Training & Competency', key=f'profile_training_{selected_uid}'):
            st.session_state['psb_current_page'] = 'Training'
            st.rerun()
        if st.button('Open Authorization', key=f'profile_auth_{selected_uid}'):
            st.session_state['psb_current_page'] = 'Authorization'
            st.rerun()
    with tabs[1]:
        st.subheader('Development Plan')
        table(plans[[c for c in ['plan_id', 'competency_scope', 'month_no', 'activity', 'target_date', 'status', 'mentor_name'] if c in plans.columns]]) if not plans.empty else st.info('No development-plan records found.')
    with tabs[2]:
        st.subheader('Training')
        table(training[[c for c in ['record_id', 'training_title', 'status', 'score', 'progress', 'due_date', 'completed_on'] if c in training.columns]]) if not training.empty else st.info('No training records found.')
        st.subheader('CPD')
        table(cpd[[c for c in ['cpd_id', 'activity', 'category', 'hours', 'date', 'verified', 'status'] if c in cpd.columns]]) if not cpd.empty else st.info('No CPD records found.')
    with tabs[3]:
        st.subheader('Competency')
        table(competency[[c for c in ['competency_id', 'area', 'competency_level', 'scope', 'status', 'expiry_date', 'required_level_for_auth'] if c in competency.columns]]) if not competency.empty else st.info('No competency records found.')
    with tabs[4]:
        st.subheader('Authorization')
        table(auths[[c for c in ['auth_id', 'authorization_id', 'scope', 'status', 'expiry_date', 'restriction'] if c in auths.columns]]) if not auths.empty else st.info('No authorization records found.')
    with tabs[5]:
        st.subheader('Performance & Feedback')
        kpi = db_where('kpi_records', 'user_id = :user_id', (('user_id', selected_uid),))
        metrics([('KPI Records', len(kpi)), ('Client Feedback', len(feedback)), ('CPD Records', len(cpd))])
        if not kpi.empty:
            table(kpi[[c for c in ['kpi_id', 'period', 'kpi_score', 'status', 'created_on'] if c in kpi.columns]])
        else:
            st.info('No KPI records found.')
        if not feedback.empty:
            st.subheader('Client Feedback')
            table(feedback[[c for c in ['feedback_id', 'date', 'rating', 'category', 'status', 'summary'] if c in feedback.columns]])
        else:
            st.caption('No client feedback records found.')
    with tabs[6]:
        st.subheader('Employee Documents')
        if not files_df.empty:
            table(files_df[[c for c in ['file_id', 'file_name', 'category', 'linked_table', 'linked_id', 'review_status', 'created_on'] if c in files_df.columns]])
        else:
            st.info('No employee-level documents are attached. Documents remain owned by their relevant business record.')
    with tabs[7]:
        st.subheader('Employee History')
        if not audits.empty:
            cols = [c for c in ['date_time', 'actor_name', 'actor_role', 'action', 'entity_type', 'result', 'reason', 'before_value', 'after_value'] if c in audits.columns]
            table(audits.sort_values('date_time', ascending=False)[cols])
        else:
            st.info('No audit events are linked directly to this employee yet.')
    st.caption('Security: passwords, tokens and other credentials are never displayed on the employee profile.')

def development_plan_page(actor):
    """Authoritative employee development-plan workflow.

    Development Plans answer: what does this person need to develop, why,
    by when, who owns the action, and what evidence proves completion?
    Training, Competency, Witness and Authorization remain separate
    authoritative workflows; this page links to them rather than duplicating
    their records.
    """
    st.header('Development Plans')
    st.caption('Plan, assign, monitor and evidence professional development. Training, competency and authorization records remain authoritative in their own modules.')
    users = db_all('users')
    plans = restrict_user_frame(db_all('development_plans'), actor)
    allowed_roles = ['Admin', 'Trainer', 'Department Manager', 'QMS Auditor', 'Management']
    can_manage = actor_get(actor, 'role') in allowed_roles
    actor_uid = actor_get(actor, 'user_id')
    defaults = {'plan_title': '', 'objective': '', 'development_type': 'Training', 'priority': 'Medium', 'owner_id': '', 'owner_name': '', 'progress_percent': 0, 'evidence_required': '', 'evidence_status': 'Not Required', 'review_date': '', 'completed_on': '', 'source_gap': '', 'success_criteria': '', 'updated_by': '', 'plan_group_id': ''}
    for col, default in defaults.items():
        if col not in plans.columns:
            plans[col] = default
    if not can_manage and (not plans.empty):
        plans = plans[(plans['user_id'].astype(str) == str(actor_uid)) | (plans['owner_id'].astype(str) == str(actor_uid))].copy()
    today_value = date.today()

    def _date(v):
        try:
            return datetime.strptime(str(v)[:10], '%Y-%m-%d').date()
        except Exception:
            return None
    active = plans[plans['status'].astype(str).isin(['Draft', 'Active', 'On Hold', 'At Risk'])] if not plans.empty else plans
    completed = plans[plans['status'].astype(str) == 'Completed'] if not plans.empty else plans
    overdue_count = 0
    due_30 = 0
    if not active.empty:
        for _, r in active.iterrows():
            d = _date(r.get('target_date', ''))
            if d:
                if d < today_value:
                    overdue_count += 1
                elif d <= today_value + timedelta(days=30):
                    due_30 += 1
    people_count = plans['user_id'].nunique() if not plans.empty else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('People with Plans', people_count)
    c2.metric('Active Items', len(active))
    c3.metric('Completed', len(completed))
    c4.metric('Due in 30 Days', due_30)
    c5.metric('Overdue', overdue_count)
    if not can_manage:
        learner_tabs=st.tabs(['My Plan','Submit Progress / Evidence'])
        with learner_tabs[0]:
            st.subheader('My Development Plan')
            if plans.empty:
                st.info('No development plan has been assigned to you.')
            else:
                rows=[]
                for _,r in plans.iterrows():
                    rows.append({'Plan ID':r.get('plan_id',''),'Plan':r.get('plan_title','') or r.get('activity',''),'Objective':r.get('objective',''),'Action':r.get('activity',''),'Owner':r.get('owner_name','') or r.get('mentor_name',''),'Due':r.get('target_date',''),'Progress':f"{int(float(r.get('progress_percent',0) or 0))}%",'Evidence Required':r.get('evidence_required',''),'Evidence Status':r.get('evidence_status',''),'Status':r.get('status','')})
                table(pd.DataFrame(rows),max_rows=200)
        with learner_tabs[1]:
            st.subheader('Submit My Progress / Evidence')
            if plans.empty:
                st.info('No development-plan items are available for progress submission.')
            else:
                labels=[f"{r.get('plan_id','')} — {r.get('plan_title','') or r.get('activity','')}" for _,r in plans.iterrows()]
                selected_label=st.selectbox('Plan item',labels,key='learner_dev_item'); selected_id=selected_label.split(' — ',1)[0]; selected=plans[plans['plan_id'].astype(str).eq(selected_id)].iloc[-1]; current_progress=int(float(selected.get('progress_percent',0) or 0))
                with st.form('learner_development_progress'):
                    learner_progress=st.slider('My progress',0,100,current_progress,5)
                    learner_notes=st.text_area('Progress update',value=str(selected.get('learner_progress_notes') or ''),placeholder='Describe the work completed and what remains.')
                    evidence_reference=st.text_input('Evidence link / reference',value=str(selected.get('learner_evidence_reference') or ''),placeholder='Document reference, file link, certificate or record ID')
                    learner_declare=st.checkbox('I confirm this progress and evidence relate to my assigned development-plan item.')
                    submit_progress=st.form_submit_button('Submit Progress / Evidence',type='primary',use_container_width=True)
                if submit_progress:
                    if not learner_declare or not learner_notes.strip(): st.error('Progress details and confirmation are required.')
                    else:
                        evidence_status='In Progress' if evidence_reference.strip() else str(selected.get('evidence_status') or 'Not Started')
                        db_update('development_plans','plan_id',selected_id,{'progress_percent':int(learner_progress),'learner_progress_notes':learner_notes.strip(),'learner_evidence_reference':evidence_reference.strip(),'learner_updated_on':now(),'evidence_status':evidence_status,'updated_by':actor_uid,'updated_on':now()})
                        audit('Learner Development Progress Submitted',f'{selected_id} progress {learner_progress}%',actor=actor,entity_type='development_plan',entity_id=selected_id,reason='Learner progress/evidence submission'); st.success('Your progress and evidence were submitted to the development-plan owner.'); st.rerun()
        return
    tabs = st.tabs(['Plan Register', 'Create Plan', 'Review / Update'])
    with tabs[0]:
        st.subheader('Development Plan Register')
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        search = f1.text_input('Search', placeholder='Employee, objective, activity or plan ID', key='dev_search')
        status_filter = f2.selectbox('Status', ['All', 'Draft', 'Active', 'At Risk', 'On Hold', 'Completed', 'Cancelled'], key='dev_status')
        type_filter = f3.selectbox('Type', ['All', 'Training', 'Experience', 'Witness', 'Mentoring', 'CPD', 'Rule Development', 'Other'], key='dev_type')
        priority_filter = f4.selectbox('Priority', ['All', 'High', 'Medium', 'Low'], key='dev_priority')
        shown = plans.copy()
        if search.strip():
            q = search.strip().lower()
            mask = False
            for col in ['name', 'plan_id', 'plan_title', 'objective', 'activity', 'owner_name', 'source_gap']:
                if col in shown.columns:
                    mask = mask | shown[col].astype(str).str.lower().str.contains(q, na=False)
            shown = shown[mask]
        if status_filter != 'All':
            shown = shown[shown['status'].astype(str) == status_filter]
        if type_filter != 'All':
            shown = shown[shown['development_type'].astype(str) == type_filter]
        if priority_filter != 'All':
            shown = shown[shown['priority'].astype(str) == priority_filter]
        if not shown.empty:
            rows = []
            for _, r in shown.iterrows():
                d = _date(r.get('target_date', ''))
                status = str(r.get('status', 'Active'))
                health = 'Completed' if status == 'Completed' else 'Overdue' if d and d < today_value else 'Due Soon' if d and d <= today_value + timedelta(days=30) else 'On Track'
                rows.append({'Plan ID': r.get('plan_id', ''), 'Employee': r.get('name', ''), 'Plan': r.get('plan_title', '') or r.get('activity', ''), 'Type': r.get('development_type', ''), 'Scope': r.get('competency_scope', ''), 'Owner': r.get('owner_name', '') or r.get('mentor_name', ''), 'Due': r.get('target_date', ''), 'Progress': f"{int(float(r.get('progress_percent', 0) or 0))}%", 'Status': status, 'Health': health, 'Priority': r.get('priority', 'Medium')})
            table(pd.DataFrame(rows), max_rows=200)
        else:
            st.info('No development-plan items match the current filters.')
        if can_manage:
            st.divider()
            st.subheader('Employee Development Summary')
            if not plans.empty:
                summary = plans.groupby(['user_id', 'name'], dropna=False).agg(plan_items=('plan_id', 'count'), completed=('status', lambda s: int((s.astype(str) == 'Completed').sum())), avg_progress=('progress_percent', 'mean')).reset_index()
                summary['Completion'] = summary.apply(lambda r: f"{(int(round(r['completed'] / r['plan_items'] * 100)) if r['plan_items'] else 0)}%", axis=1)
                summary['Avg Progress'] = summary['avg_progress'].round(0).astype(int).astype(str) + '%'
                table(summary[['user_id', 'name', 'plan_items', 'completed', 'Completion', 'Avg Progress']].rename(columns={'user_id': 'Employee ID', 'name': 'Employee', 'plan_items': 'Items'}))
    with tabs[1]:
        st.subheader('Create Development Plan Item')
        if not can_manage:
            st.info('Your role can view assigned development plans but cannot create or modify plan items.')
        else:
            eligible_roles = ['Trainee', 'On Probation', 'Surveyor', 'Plan Appraiser', 'QMS Auditor', 'Industrial Surveyor', 'Rule Development Rep']
            candidates = users[users['role'].isin(eligible_roles)].copy() if not users.empty else pd.DataFrame()
            if candidates.empty:
                st.warning('No eligible employees are available for development planning.')
            else:
                with st.form('development_plan_create', clear_on_submit=True):
                    person_options = candidates['name'].astype(str) + ' — ' + candidates['user_id'].astype(str)
                    person = st.selectbox('Employee', person_options)
                    row = candidates[candidates['user_id'] == person.split(' — ', 1)[1]].iloc[0]
                    default_owner = row.get('tutor_id', '') or actor_uid
                    owner_candidates = users[users['role'].isin(['Trainer', 'Department Manager', 'QMS Auditor'])].copy() if not users.empty else pd.DataFrame()
                    owner_options = ['System / Current Assigner — '] + ([f'{n} — {u}' for n, u in zip(owner_candidates['name'], owner_candidates['user_id'])] if not owner_candidates.empty else [])
                    default_idx = 0
                    for i, opt in enumerate(owner_options):
                        if str(default_owner) and opt.endswith(f'— {default_owner}'):
                            default_idx = i
                            break
                    owner = st.selectbox('Development Owner / Trainer', owner_options, index=default_idx, help="The owner monitors progress. This does not change the employee's master Trainer assignment.")
                    plan_title = st.text_input('Plan Item Title', placeholder='e.g. Complete Electrical Survey Competency Development')
                    c1, c2, c3 = st.columns(3)
                    development_type = c1.selectbox('Development Type', ['Training', 'Experience', 'Witness', 'Mentoring', 'CPD', 'Rule Development', 'Other'])
                    priority = c2.selectbox('Priority', ['High', 'Medium', 'Low'], index=1)
                    scope = c3.selectbox('Competency Scope', SCOPES)
                    objective = st.text_area('Development Objective', placeholder='What capability should this activity develop?')
                    activity = st.text_area('Development Action', placeholder='Specific action, assignment, supervised activity or learning activity.')
                    success = st.text_area('Success Criteria', placeholder='How will completion be objectively demonstrated?')
                    c1, c2, c3 = st.columns(3)
                    month_no = c1.number_input('Programme Month', 1, 36, 1)
                    target = c2.date_input('Target Date', today_value + timedelta(days=30))
                    review = c3.date_input('Review Date', today_value + timedelta(days=14))
                    evidence_required = st.text_input('Evidence Required', placeholder='Certificate, witness record, assessment, report, etc.')
                    source_gap = st.text_input('Source / Gap Reference', placeholder='Optional competency gap, review or requirement reference')
                    comments = st.text_area('Initial Owner Comments')
                    submitted = st.form_submit_button('Create Development Plan Item', type='primary', use_container_width=True)
                if submitted:
                    plan_id = uid('PLAN')
                    owner_id, owner_name = ('', '')
                    if owner and ' — ' in owner:
                        owner_name, owner_id = owner.split(' — ', 1)
                    else:
                        owner_id = str(default_owner or actor_uid)
                        owner_row = users[users['user_id'].astype(str) == owner_id]
                        owner_name = str(owner_row.iloc[0].get('name', actor_get(actor, 'name'))) if not owner_row.empty else actor_get(actor, 'name')
                    person_name, person_id = person.split(' — ', 1)
                    db_insert('development_plans', {'plan_id': plan_id, 'plan_group_id': f'DP-{person_id}', 'plan_title': plan_title.strip(), 'objective': objective.strip(), 'development_type': development_type, 'priority': priority, 'owner_id': owner_id, 'owner_name': owner_name, 'progress_percent': 0, 'evidence_required': evidence_required.strip(), 'evidence_status': 'Not Started' if evidence_required.strip() else 'Not Required', 'review_date': str(review), 'completed_on': '', 'source_gap': source_gap.strip(), 'success_criteria': success.strip(), 'updated_by': actor_uid, 'user_id': person_id, 'name': person_name, 'trainee_path': str(row.get('trainee_path', '')), 'mentor_id': str(row.get('tutor_id', '')), 'mentor_name': str(row.get('tutor_name', '')), 'competency_scope': scope, 'month_no': int(month_no), 'activity': activity.strip(), 'target_date': str(target), 'status': 'Active', 'mentor_comments': comments.strip(), 'created_on': now(), 'updated_on': now()})
                    audit('Development Plan Created', f'Development plan item {plan_id} created for {person_name}', actor=actor, entity_type='development_plan', entity_id=plan_id, reason='New development-plan item', after_value=json.dumps({'employee': person_id, 'title': plan_title, 'type': development_type, 'target_date': str(target)}, default=str))
                    st.success(f'Development plan item {plan_id} created.')
    with tabs[2]:
        st.subheader('Review / Update Plan Item')
        editable = plans.copy()
        if editable.empty:
            st.info('No development-plan items are available for update.')
        elif not can_manage:
            st.info('Only the assigned development owner or an authorized management role can update plan items.')
        else:
            labels = [f"{r.get('plan_id', '')} — {r.get('name', '')} — {r.get('plan_title', '') or r.get('activity', '')}" for _, r in editable.iterrows()]
            selected_label = st.selectbox('Select plan item', labels, key='dev_edit_select')
            selected_id = selected_label.split(' — ', 1)[0]
            selected = editable[editable['plan_id'].astype(str) == selected_id].iloc[0]
            current_progress = int(float(selected.get('progress_percent', 0) or 0))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Current Status', str(selected.get('status', 'Active')))
            c2.metric('Progress', f'{current_progress}%')
            c3.metric('Priority', str(selected.get('priority', 'Medium')))
            c4.metric('Due', str(selected.get('target_date', '—')))
            with st.form('development_plan_update'):
                progress = st.slider('Progress', 0, 100, current_progress, 5)
                status = st.selectbox('Status', ['Draft', 'Active', 'At Risk', 'On Hold', 'Completed', 'Cancelled'], index=['Draft', 'Active', 'At Risk', 'On Hold', 'Completed', 'Cancelled'].index(str(selected.get('status', 'Active'))) if str(selected.get('status', 'Active')) in ['Draft', 'Active', 'At Risk', 'On Hold', 'Completed', 'Cancelled'] else 1)
                evidence_status = st.selectbox('Evidence Status', ['Not Required', 'Not Started', 'In Progress', 'Complete', 'Rejected'], index=['Not Required', 'Not Started', 'In Progress', 'Complete', 'Rejected'].index(str(selected.get('evidence_status', 'Not Required'))) if str(selected.get('evidence_status', 'Not Required')) in ['Not Required', 'Not Started', 'In Progress', 'Complete', 'Rejected'] else 0)
                target_default = _date(selected.get('target_date', '')) or today_value + timedelta(days=30)
                review_default = _date(selected.get('review_date', '')) or today_value + timedelta(days=14)
                c1, c2 = st.columns(2)
                target_update = c1.date_input('Target Date', target_default)
                review_update = c2.date_input('Review Date', review_default)
                comments = st.text_area('Owner / Reviewer Comments', value=str(selected.get('mentor_comments', '')))
                success = st.text_area('Success Criteria', value=str(selected.get('success_criteria', '')))
                evidence = st.text_input('Evidence Required', value=str(selected.get('evidence_required', '')))
                reason = st.text_input('Reason for Update', placeholder='Required for governance/audit')
                save = st.form_submit_button('Save Update', type='primary', use_container_width=True)
            if save:
                owner_id = str(selected.get('owner_id', '') or actor_uid)
                if not owner_id:
                    owner_id = actor_uid
                before = {k: selected.get(k, '') for k in ['status', 'progress_percent', 'evidence_status', 'target_date', 'review_date']}
                completed_on = today() if status == 'Completed' and str(selected.get('status', '')) != 'Completed' else str(selected.get('completed_on', ''))
                db_update('development_plans', 'plan_id', selected_id, {'progress_percent': int(progress), 'status': status, 'evidence_status': evidence_status, 'target_date': str(target_update), 'review_date': str(review_update), 'mentor_comments': comments.strip(), 'success_criteria': success.strip(), 'evidence_required': evidence.strip(), 'completed_on': completed_on, 'updated_by': actor_uid, 'updated_on': now()})
                audit('Development Plan Updated', f'Development plan item {selected_id} updated', actor=actor, entity_type='development_plan', entity_id=selected_id, reason=reason or 'Plan progress/status update', before_value=json.dumps(before, default=str), after_value=json.dumps({'status': status, 'progress_percent': int(progress), 'evidence_status': evidence_status, 'target_date': str(target_update), 'review_date': str(review_update)}, default=str))
                st.success('Development plan updated and audited.')
    st.divider()
    st.caption('Design rule: a Development Plan records development actions and evidence requirements. It does not duplicate training completion, competency decisions, witness assessments or authorization approvals.')

def succession_planning_page(actor):
    """Succession and talent pipeline governance.

    Succession answers: which critical role needs continuity, who are the
    potential successors, how ready are they, what risks exist, and what
    development programme is linked to the candidate? Development actions
    remain authoritative in Development Plans rather than being duplicated.
    """
    st.header('Succession Planning')
    st.caption('Build a controlled succession pipeline for critical roles without duplicating employee, competency or development records.')
    role = actor_get(actor, 'role')
    can_manage = can_action(actor, 'Succession Planning', 'Manage', 'Organization-wide') or can_action(actor, 'Succession Planning', 'Edit', 'Organization-wide')
    if not can_manage:
        st.info('Succession Planning is restricted to Management and Admin.')
        return
    users = restrict_user_frame(db_all('users'), actor)
    plans = db_all('succession_plans')
    dev = db_all('development_plans')
    defaults = {'current_role_name': '', 'current_department': '', 'target_role': '', 'target_position': '', 'target_department': '', 'successor_for': '', 'criticality': 'High', 'readiness_level': 'Long-term Potential', 'readiness_date': '', 'potential_rating': 'Medium', 'risk_status': 'Monitor', 'sponsor_id': '', 'sponsor': '', 'linked_development_plan_id': '', 'status': 'Active', 'last_reviewed_on': '', 'review_notes': '', 'created_on': '', 'updated_on': ''}
    for col, default in defaults.items():
        if col not in plans.columns:
            plans[col] = default
    if plans.empty:
        for col in defaults:
            if col not in plans.columns:
                plans[col] = defaults[col]

    def _d(value):
        try:
            return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
        except Exception:
            return None
    active = plans[plans['status'].astype(str).isin(['Active', 'On Hold', 'At Risk'])] if not plans.empty else plans
    ready_now = len(plans[plans['readiness_level'].astype(str) == 'Ready Now']) if not plans.empty else 0
    ready_6m = len(plans[plans['readiness_level'].astype(str) == 'Ready in 6 Months']) if not plans.empty else 0
    critical = len(plans[plans['criticality'].astype(str) == 'Critical']) if not plans.empty else 0
    at_risk = len(plans[plans['risk_status'].astype(str).isin(['High Risk', 'At Risk'])]) if not plans.empty else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Active Pipelines', len(active))
    c2.metric('Critical Roles', critical)
    c3.metric('Ready Now', ready_now)
    c4.metric('Ready in 6 Months', ready_6m)
    c5.metric('At Risk', at_risk)
    tabs = st.tabs(['Succession Register', 'Create Plan', 'Review / Update', 'Talent View'])
    with tabs[0]:
        st.subheader('Succession Register')
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        search = f1.text_input('Search', placeholder='Candidate, target position, department or plan ID', key='succ_search')
        status_filter = f2.selectbox('Status', ['All', 'Active', 'At Risk', 'On Hold', 'Completed', 'Withdrawn'], key='succ_status')
        critical_filter = f3.selectbox('Criticality', ['All', 'Critical', 'High', 'Medium', 'Low'], key='succ_critical')
        readiness_filter = f4.selectbox('Readiness', ['All', 'Ready Now', 'Ready in 6 Months', 'Ready in 1 Year', 'Ready in 2 Years', 'Long-term Potential'], key='succ_ready')
        shown = plans.copy()
        if search.strip():
            q = search.strip().lower()
            mask = False
            for col in ['succession_id', 'name', 'target_role', 'target_position', 'target_department', 'successor_for', 'sponsor']:
                if col in shown.columns:
                    mask = mask | shown[col].astype(str).str.lower().str.contains(q, na=False)
            shown = shown[mask]
        if status_filter != 'All':
            shown = shown[shown['status'].astype(str) == status_filter]
        if critical_filter != 'All':
            shown = shown[shown['criticality'].astype(str) == critical_filter]
        if readiness_filter != 'All':
            shown = shown[shown['readiness_level'].astype(str) == readiness_filter]
        display_cols = [c for c in ['succession_id', 'name', 'target_position', 'target_department', 'criticality', 'readiness_level', 'potential_rating', 'risk_status', 'readiness_date', 'status'] if c in shown.columns]
        table(shown[display_cols] if display_cols else shown)
    with tabs[1]:
        st.subheader('Create Succession Plan')
        st.caption('Create the succession relationship and readiness assessment. Development actions must be maintained in Development Plans.')
        if users.empty:
            st.warning('No users are available.')
        else:
            names = users['name'].fillna('').astype(str).tolist() if 'name' in users.columns else []
            with st.form('succession_create', clear_on_submit=True):
                candidate_label = st.selectbox('Potential Successor', names)
                candidate_rows = users[users['name'].astype(str) == str(candidate_label)]
                candidate = candidate_rows.iloc[0].to_dict() if not candidate_rows.empty else {}
                candidate_uid = str(candidate.get('user_id', ''))
                current_role = str(candidate.get('role', ''))
                current_department = str(candidate.get('primary_department', candidate.get('department', '')))
                st.caption(f"Current role: **{current_role or '—'}**  |  Primary department: **{current_department or '—'}**")
                c1, c2 = st.columns(2)
                with c1:
                    target_position = st.text_input('Target Position', placeholder='e.g. Department Manager — Survey Inservice')
                    target_role = st.selectbox('Target Role', ROLES)
                    target_department = st.selectbox('Target Department', DEPARTMENTS)
                    successor_for = st.text_input('Position / Role Holder to Succeed', placeholder='Named role or current position holder')
                with c2:
                    criticality = st.selectbox('Role Criticality', ['Critical', 'High', 'Medium', 'Low'], index=1)
                    readiness = st.selectbox('Readiness', ['Ready Now', 'Ready in 6 Months', 'Ready in 1 Year', 'Ready in 2 Years', 'Long-term Potential'])
                    readiness_date = st.date_input('Expected Ready Date', date.today() + timedelta(days=365))
                    potential = st.selectbox('Potential Rating', ['High', 'Medium', 'Low'])
                risk = st.selectbox('Succession Risk', ['Low Risk', 'Monitor', 'At Risk', 'High Risk'])
                sponsor_names = users['name'].fillna('').astype(str).tolist() if 'name' in users.columns else []
                sponsor = st.selectbox('Sponsor / Accountable Manager', sponsor_names if sponsor_names else [actor_get(actor, 'name')])
                sponsor_row = users[users['name'].astype(str) == str(sponsor)] if sponsor_names else pd.DataFrame()
                sponsor_id = str(sponsor_row.iloc[0].get('user_id', '')) if not sponsor_row.empty else actor_get(actor, 'user_id')
                candidate_dev = dev[dev['user_id'].astype(str) == candidate_uid] if not dev.empty and 'user_id' in dev.columns else pd.DataFrame()
                dev_options = ['— No linked plan —']
                if not candidate_dev.empty:
                    for _, r in candidate_dev.iterrows():
                        dev_options.append(f"{r.get('plan_id', '')} — {r.get('plan_title', 'Development Plan')} — {r.get('status', '')}")
                linked_label = st.selectbox('Linked Development Plan', dev_options)
                linked_plan_id = linked_label.split(' — ')[0] if linked_label != '— No linked plan —' else ''
                review_notes = st.text_area('Initial Succession Review Notes', placeholder='Why this person is being considered, key risk, and review focus.')
                if st.form_submit_button('Create Succession Plan', type='primary'):
                    if not candidate_uid or not target_position.strip():
                        st.error('Potential successor and Target Position are required.')
                    else:
                        sid = uid('SUC')
                        db_insert('succession_plans', {'succession_id': sid, 'user_id': candidate_uid, 'name': candidate_label, 'current_role_name': current_role, 'current_department': current_department, 'target_role': target_role, 'target_position': target_position.strip(), 'target_department': target_department, 'successor_for': successor_for.strip(), 'criticality': criticality, 'readiness_level': readiness, 'expected_ready_date': str(readiness_date), 'readiness_date': str(readiness_date), 'potential_rating': potential, 'risk_status': risk, 'sponsor_id': sponsor_id, 'sponsor': sponsor, 'linked_development_plan_id': linked_plan_id, 'development_actions': '', 'status': 'Active', 'last_reviewed_on': today(), 'review_notes': review_notes.strip(), 'created_on': now(), 'updated_on': now()})
                        audit('Succession Plan Created', f'Succession {sid} created for {candidate_label} toward {target_position.strip()}', actor=actor, entity_type='succession_plans', entity_id=sid, after_value=json.dumps({'candidate': candidate_label, 'target_position': target_position.strip(), 'readiness': readiness, 'criticality': criticality}, default=str))
                        st.success('Succession plan created.')
    with tabs[2]:
        st.subheader('Review / Update')
        if plans.empty:
            st.info('No succession plans available.')
        else:
            labels = [f"{r.get('succession_id', '')} — {r.get('name', '')} — {r.get('target_position', r.get('target_role', ''))}" for _, r in plans.iterrows()]
            selected_label = st.selectbox('Succession Plan', labels, key='succ_review_select')
            sid = selected_label.split(' — ')[0]
            current = plans[plans['succession_id'].astype(str) == sid].iloc[0].to_dict()
            current_risk = str(current.get('risk_status', 'Monitor'))
            current_readiness = str(current.get('readiness_level', 'Long-term Potential'))
            linked_plan_id = str(current.get('linked_development_plan_id', ''))
            c1, c2, c3 = st.columns(3)
            c1.metric('Candidate', str(current.get('name', '—')))
            c2.metric('Readiness', current_readiness)
            c3.metric('Risk', current_risk)
            st.caption(f"Target: **{current.get('target_position', current.get('target_role', '—'))}** | Department: **{current.get('target_department', '—')}**")
            with st.form('succession_review'):
                r1, r2 = st.columns(2)
                with r1:
                    readiness = st.selectbox('Readiness', ['Ready Now', 'Ready in 6 Months', 'Ready in 1 Year', 'Ready in 2 Years', 'Long-term Potential'], index=max(0, ['Ready Now', 'Ready in 6 Months', 'Ready in 1 Year', 'Ready in 2 Years', 'Long-term Potential'].index(current_readiness) if current_readiness in ['Ready Now', 'Ready in 6 Months', 'Ready in 1 Year', 'Ready in 2 Years', 'Long-term Potential'] else 4))
                    risk = st.selectbox('Risk', ['Low Risk', 'Monitor', 'At Risk', 'High Risk'], index=max(0, ['Low Risk', 'Monitor', 'At Risk', 'High Risk'].index(current_risk) if current_risk in ['Low Risk', 'Monitor', 'At Risk', 'High Risk'] else 1))
                    potential = st.selectbox('Potential Rating', ['High', 'Medium', 'Low'], index=max(0, ['High', 'Medium', 'Low'].index(str(current.get('potential_rating', 'Medium')))))
                with r2:
                    status = st.selectbox('Plan Status', ['Active', 'At Risk', 'On Hold', 'Completed', 'Withdrawn'], index=max(0, ['Active', 'At Risk', 'On Hold', 'Completed', 'Withdrawn'].index(str(current.get('status', 'Active')))))
                    review_date = st.date_input('Expected Ready Date', _d(current.get('readiness_date', current.get('expected_ready_date', ''))) or date.today() + timedelta(days=365))
                    linked_plan_options = ['— No linked plan —']
                    candidate_dev = dev[dev['user_id'].astype(str) == str(current.get('user_id', ''))] if not dev.empty and 'user_id' in dev.columns else pd.DataFrame()
                    for _, r in candidate_dev.iterrows():
                        linked_plan_options.append(f"{r.get('plan_id', '')} — {r.get('plan_title', 'Development Plan')} — {r.get('status', '')}")
                    current_link = next((x for x in linked_plan_options if x.startswith(linked_plan_id + ' —')), '— No linked plan —') if linked_plan_id else '— No linked plan —'
                    linked_label = st.selectbox('Linked Development Plan', linked_plan_options, index=linked_plan_options.index(current_link) if current_link in linked_plan_options else 0)
                notes = st.text_area('Review Notes', value=str(current.get('review_notes', '')))
                if st.form_submit_button('Save Review', type='primary'):
                    new_linked = linked_label.split(' — ')[0] if linked_label != '— No linked plan —' else ''
                    before = {k: current.get(k, '') for k in ['readiness_level', 'risk_status', 'potential_rating', 'status', 'readiness_date', 'linked_development_plan_id']}
                    after = {'readiness_level': readiness, 'risk_status': risk, 'potential_rating': potential, 'status': status, 'readiness_date': str(review_date), 'linked_development_plan_id': new_linked}
                    db_update('succession_plans', 'succession_id', sid, {'readiness_level': readiness, 'risk_status': risk, 'potential_rating': potential, 'status': status, 'expected_ready_date': str(review_date), 'readiness_date': str(review_date), 'linked_development_plan_id': new_linked, 'review_notes': notes.strip(), 'last_reviewed_on': today(), 'updated_on': now()})
                    audit('Succession Plan Reviewed', f'Succession {sid} reviewed', actor=actor, entity_type='succession_plans', entity_id=sid, before_value=json.dumps(before, default=str), after_value=json.dumps(after, default=str), reason=notes.strip())
                    st.success('Succession review saved.')
            if linked_plan_id:
                st.markdown('#### Linked Development Plan')
                linked = dev[dev['plan_id'].astype(str) == linked_plan_id] if not dev.empty and 'plan_id' in dev.columns else pd.DataFrame()
                if not linked.empty:
                    rr = linked.iloc[0]
                    metrics([('Plan Status', rr.get('status', '—')), ('Progress', f"{int(float(rr.get('progress_percent', 0) or 0))}%"), ('Target Date', rr.get('target_date', '—')), ('Owner', rr.get('owner_name', '—'))])
                else:
                    st.info('The linked Development Plan could not be found. Create a new plan from Development Plans and then link it here.')
    with tabs[3]:
        st.subheader('Talent View')
        st.caption('A decision-support view. It summarizes existing employee, development and succession information without changing those authoritative records.')
        if plans.empty:
            st.info('No succession candidates have been recorded yet.')
        else:
            talent = plans[[c for c in ['name', 'current_role_name', 'target_position', 'target_department', 'criticality', 'readiness_level', 'potential_rating', 'risk_status', 'status'] if c in plans.columns]].copy()
            table(talent, max_rows=500)

def workforce_planning_page(actor):
    """Capacity and demand planning sourced from existing people, competency and authorization data."""
    role = actor_get(actor, 'role')
    if not can_action(actor, 'Workforce Planning', 'View', 'Organization-wide') and (not can_action(actor, 'Workforce Planning', 'Edit', 'Department')) and (not can_action(actor, 'Workforce Planning', 'Manage', 'Organization-wide')):
        st.error('You do not have permission to manage workforce forecasts. You may view workforce information through your authorized dashboards.')
        return
    st.header('Workforce Planning')
    st.caption('Plan capacity and future demand without creating duplicate employee, competency or authorization records.')
    users = db_all('users')
    auths = db_all('authorization_requests')
    competency = db_all('competency_matrix')
    forecasts = db_all('workforce_forecasts')
    succession = db_all('succession_plans')
    active_users = users[users.get('status', pd.Series(dtype=str)).astype(str).str.lower().eq('active')] if not users.empty and 'status' in users.columns else users.iloc[0:0]
    available_users = active_users[active_users.get('availability', pd.Series(dtype=str)).astype(str).eq('Available')] if not active_users.empty and 'availability' in active_users.columns else active_users.iloc[0:0]
    leave_users = active_users[active_users.get('availability', pd.Series(dtype=str)).astype(str).isin(['On Leave', 'Unavailable'])] if not active_users.empty and 'availability' in active_users.columns else active_users.iloc[0:0]
    valid_auth = auths[auths.get('status', pd.Series(dtype=str)).astype(str).str.contains('Approved', case=False, na=False)] if not auths.empty and 'status' in auths.columns else auths.iloc[0:0]
    expiring_auth = valid_auth[valid_auth.get('expiry_date', pd.Series(dtype=str)).apply(days_until).between(-1, 180)] if not valid_auth.empty and 'expiry_date' in valid_auth.columns else valid_auth.iloc[0:0]
    expired_auth = valid_auth[valid_auth.get('expiry_date', pd.Series(dtype=str)).apply(days_until).lt(0)] if not valid_auth.empty and 'expiry_date' in valid_auth.columns else valid_auth.iloc[0:0]
    ready_comp = competency[competency.get('status', pd.Series(dtype=str)).astype(str).str.contains('Ready|Competent|Approved', case=False, regex=True, na=False)] if not competency.empty and 'status' in competency.columns else competency.iloc[0:0]
    recent_forecasts = forecasts.sort_values('created_on', ascending=False).head(10) if not forecasts.empty and 'created_on' in forecasts.columns else forecasts
    open_gaps = forecasts[forecasts.get('gap', pd.Series(dtype=float)).fillna(0).astype(float) > 0] if not forecasts.empty and 'gap' in forecasts.columns else forecasts.iloc[0:0]
    metrics([('Active Workforce', len(active_users)), ('Available Now', len(available_users)), ('Competency Ready', len(ready_comp)), ('Authorizations Expiring ≤180d', len(expiring_auth)), ('On Leave / Unavailable', len(leave_users)), ('Expired Authorizations', len(expired_auth)), ('Open Capacity Gaps', len(open_gaps)), ('Succession Plans', len(succession) if not succession.empty else 0)])
    tabs = st.tabs(['Capacity Overview', 'Demand Forecast', 'Department Capacity', 'Gaps & Actions'])
    with tabs[0]:
        st.subheader('Current Capacity')
        if active_users.empty:
            st.info('No active workforce records are available.')
        else:
            dept_rows = []
            for _, u in active_users.iterrows():
                depts = split_list(str(u.get('department', ''))) or split_list(str(u.get('primary_department', ''))) or ['Unassigned']
                for dept in depts:
                    dept_rows.append({'Department': dept, 'Employee': u.get('name', ''), 'Role': u.get('role', ''), 'Availability': u.get('availability', ''), 'Competency': u.get('competency_level', '')})
            capacity_df = pd.DataFrame(dept_rows)
            if not capacity_df.empty:
                summary = capacity_df.groupby('Department', as_index=False).agg(Active_Staff=('Employee', 'count'), Available=('Availability', lambda s: int((s == 'Available').sum())), Unavailable=('Availability', lambda s: int(s.isin(['On Leave', 'Unavailable']).sum())))
                table(summary.sort_values('Department'), max_rows=100)
            if not expiring_auth.empty:
                st.warning(f'{len(expiring_auth)} approved authorization(s) expire within 180 days. Use Authorization → Revalidation/Annual Review for action.')
    with tabs[1]:
        st.subheader('Create / Update Demand Forecast')
        st.caption('Forecasts represent future demand. Employee, competency and authorization values are calculated from their authoritative records.')
        departments = ['Organization-wide'] + [d for d in DEPARTMENTS]
        roles = ['All Roles'] + [r for r in ROLES if r not in ['Admin', 'Management']]
        forecast_period = st.text_input('Forecast Period (YYYY-MM)', datetime.now().strftime('%Y-%m'), key='wf_period')
        c1, c2, c3 = st.columns(3)
        with c1:
            forecast_department = st.selectbox('Department', departments, key='wf_dept')
        with c2:
            forecast_role = st.selectbox('Role', roles, key='wf_role')
        with c3:
            required = st.number_input('Required Headcount', min_value=0, max_value=5000, value=0, step=1, key='wf_required')
        c4, c5 = st.columns(2)
        with c4:
            demand_basis = st.selectbox('Demand Basis', ['Management Plan', 'Jobs Pipeline', 'Expected Growth', 'Replacement', 'Regulatory Requirement', 'Other'], key='wf_basis')
        with c5:
            priority = st.selectbox('Priority', ['Normal', 'Important', 'Critical'], key='wf_priority')
        mitigation = st.text_area('Mitigation / Hiring / Development Plan', key='wf_mitigation', placeholder='Describe how any capacity gap will be addressed.')
        notes = st.text_area('Forecast Notes', key='wf_notes')

        def scoped_count(df, dept, role_name):
            if df is None or df.empty:
                return 0
            mask = pd.Series(True, index=df.index)
            if dept != 'Organization-wide':
                dept_series = df.get('department', pd.Series('', index=df.index)).astype(str)
                primary_series = df.get('primary_department', pd.Series('', index=df.index)).astype(str)
                mask = dept_series.str.contains(re.escape(dept), case=False, na=False) | primary_series.str.contains(re.escape(dept), case=False, na=False)
            if role_name != 'All Roles':
                mask = mask & df.get('role', pd.Series('', index=df.index)).astype(str).eq(role_name)
            return int(mask.sum())
        active_scoped = scoped_count(active_users, forecast_department, forecast_role)
        available_scoped = scoped_count(available_users, forecast_department, forecast_role)
        leave_scoped = scoped_count(leave_users, forecast_department, forecast_role)
        auth_scoped = scoped_count(valid_auth, forecast_department, forecast_role)
        gap = max(int(required) - available_scoped, 0)
        risk = 'Critical' if priority == 'Critical' and gap > 0 else 'High' if gap > 0 else 'Monitor' if len(expiring_auth) > 0 else 'Low'
        st.info(f'Current available capacity for this scope: **{available_scoped}** | Proposed requirement: **{int(required)}** | Capacity gap: **{gap}**')
        if st.button('Save Demand Forecast', type='primary', key='wf_save'):
            if not re.match('^\\\\d{4}-\\\\d{2}$', forecast_period.strip()):
                st.error('Forecast Period must use YYYY-MM format, for example 2026-09.')
            else:
                fid = uid('WF')
                db_insert('workforce_forecasts', {'forecast_id': fid, 'forecast_period': forecast_period.strip(), 'department': forecast_department, 'role': forecast_role, 'demand_basis': demand_basis, 'priority': priority, 'required_headcount': int(required), 'available_headcount': available_scoped, 'authorized_headcount': auth_scoped, 'expiring_authorizations': int(len(expiring_auth)), 'leave_or_unavailable': leave_scoped, 'gap': int(gap), 'risk_status': risk, 'mitigation_plan': mitigation.strip(), 'notes': notes.strip(), 'created_by': actor_get(actor, 'user_id'), 'created_by_name': actor_get(actor, 'name'), 'created_on': now(), 'updated_on': now()})
                audit('Workforce Forecast Created', f'Forecast {fid} created for {forecast_department} / {forecast_role} for {forecast_period.strip()}', actor=actor, entity_type='workforce_forecasts', entity_id=fid, after_value=json.dumps({'required_headcount': int(required), 'gap': int(gap), 'risk': risk}, default=str))
                st.success('Workforce demand forecast saved.')
                st.rerun()
        st.markdown('#### Recent Forecasts')
        display_cols = [c for c in ['forecast_id', 'forecast_period', 'department', 'role', 'demand_basis', 'required_headcount', 'available_headcount', 'authorized_headcount', 'gap', 'risk_status', 'priority', 'created_on'] if c in recent_forecasts.columns]
        table(recent_forecasts[display_cols] if display_cols else recent_forecasts, max_rows=100)
    with tabs[2]:
        st.subheader('Department Capacity')
        selected_department = st.selectbox('Department', DEPARTMENTS, key='wf_capacity_dept')
        if active_users.empty:
            st.info('No active users available.')
        else:
            scoped = active_users[active_users.apply(lambda r: selected_department.lower() in ' '.join([str(r.get('department', '')), str(r.get('primary_department', ''))]).lower(), axis=1)]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Active', len(scoped))
            c2.metric('Available', int((scoped.get('availability', pd.Series(dtype=str)) == 'Available').sum()) if not scoped.empty else 0)
            c3.metric('On Leave / Unavailable', int(scoped.get('availability', pd.Series(dtype=str)).isin(['On Leave', 'Unavailable']).sum()) if not scoped.empty else 0)
            c4.metric('Primary Department', int(scoped.get('primary_department', pd.Series(dtype=str)).eq(selected_department).sum()) if not scoped.empty else 0)
            if not scoped.empty:
                role_mix = scoped.groupby('role', dropna=False).size().reset_index(name='headcount').sort_values('headcount', ascending=False)
                st.markdown('#### Role Mix')
                table(role_mix, max_rows=100)
                forecast_view = forecasts[forecasts.get('department', pd.Series(dtype=str)).astype(str).eq(selected_department)] if not forecasts.empty and 'department' in forecasts.columns else pd.DataFrame()
                if not forecast_view.empty:
                    st.markdown('#### Demand vs Capacity')
                    fv = forecast_view[[c for c in ['forecast_period', 'role', 'required_headcount', 'available_headcount', 'gap', 'risk_status'] if c in forecast_view.columns]].copy()
                    table(fv.sort_values('forecast_period', ascending=False), max_rows=100)
    with tabs[3]:
        st.subheader('Capacity Gaps & Mitigation')
        if open_gaps.empty:
            st.success('No open workforce capacity gaps recorded in current forecasts.')
        else:
            gap_cols = [c for c in ['forecast_id', 'forecast_period', 'department', 'role', 'required_headcount', 'available_headcount', 'gap', 'risk_status', 'priority', 'mitigation_plan', 'created_by_name'] if c in open_gaps.columns]
            table(open_gaps[gap_cols].sort_values(['risk_status', 'forecast_period'], ascending=[True, False]) if gap_cols else open_gaps, max_rows=200)
            st.caption('Mitigation should use existing workflows: recruit/assign staff through Administration, develop current staff through Development Plans, qualify through Training & Competency, and protect coverage through Authorization/Revalidation.')
