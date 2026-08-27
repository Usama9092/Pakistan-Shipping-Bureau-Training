import hashlib
import random
from psb_app.common import (
    DEPARTMENTS,
    PUBLIC_URL,
    ROLES,
    STANDARDS,
    TRAINEE_PATHS,
    actor_get,
    audit,
    can_action,
    clean,
    create_notification,
    date,
    datetime,
    db_all,
    db_delete,
    db_insert,
    db_update,
    db_where,
    department_options,
    file_upload_panel, secure_file_url, secure_file_bytes,
    first_row,
    generate_mcqs,
    join_list,
    now,
    pd,
    re,
    split_list,
    st,
    table,
    timedelta,
    today,
    uid,
)

def metrics(items):
    cols = st.columns(min(4, max(1, len(items))))
    for index, (label, value) in enumerate(items):
        cols[index % len(cols)].metric(label, value)

def training_dashboard_page(actor):
    """Executive and operational training overview. Read-only summary; authoritative edits remain in Training/Matrix."""
    st.header('Training Dashboard')
    st.caption('Monitor training demand, progress, overdue work and completion. This page is read-only; course and assignment changes remain in the Training and Training Matrix workflows.')
    users = db_all('users')
    trainings = db_all('trainings')
    records = db_all('training_records')
    modules = db_all('training_modules')
    for frame, defaults in [(users, ['user_id', 'name', 'role', 'status', 'trainee_path']), (trainings, ['training_id', 'title', 'status', 'trainer_name', 'schedule_date']), (records, ['record_id', 'user_id', 'name', 'training_id', 'training_title', 'status', 'progress', 'score', 'due_date', 'test_status']), (modules, ['module_id', 'title', 'target_path', 'mandatory', 'refresher_required'])]:
        for col in defaults:
            if col not in frame.columns:
                frame[col] = ''
    active_users = users[users['status'].astype(str).eq('Active')] if not users.empty else users
    active_records = records.copy()
    if not active_records.empty:
        active_records['progress'] = pd.to_numeric(active_records['progress'], errors='coerce').fillna(0)
        active_records['due_dt'] = pd.to_datetime(active_records['due_date'], errors='coerce')
        active_records['status_norm'] = active_records['status'].astype(str).str.strip().str.lower()
        active_records['test_norm'] = active_records['test_status'].astype(str).str.strip().str.lower()
    today_dt = pd.Timestamp.today().normalize()
    if active_records.empty:
        assigned = completed = overdue = due30 = in_progress = 0
        avg_progress = 0
    else:
        assigned = len(active_records)
        completed_mask = (active_records['progress'] >= 100) | active_records['test_norm'].eq('passed') | active_records['status_norm'].eq('completed')
        completed = int(completed_mask.sum())
        overdue = int((active_records['due_dt'].notna() & (active_records['due_dt'] < today_dt) & ~completed_mask).sum())
        due30 = int((active_records['due_dt'].notna() & (active_records['due_dt'] >= today_dt) & (active_records['due_dt'] <= today_dt + pd.Timedelta(days=30)) & ~completed_mask).sum())
        in_progress = int(((active_records['progress'] > 0) & ~completed_mask).sum())
        avg_progress = int(round(active_records['progress'].mean())) if assigned else 0
    completion_rate = int(round(completed / assigned * 100)) if assigned else 0
    metrics([('Active Learners', len(active_users)), ('Training Assignments', assigned), ('Completed', completed), ('Completion Rate', f'{completion_rate}%'), ('In Progress', in_progress), ('Overdue', overdue), ('Due in 30 Days', due30), ('Average Progress', f'{avg_progress}%')])
    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    dept_filter = f1.selectbox('Department', ['All'] + department_options(), key='training_dash_department')
    path_options = sorted({clean(x) for x in users.get('trainee_path', pd.Series(dtype=str)).astype(str) if clean(x)}) if not users.empty else []
    path_filter = f2.selectbox('Training Path', ['All'] + path_options, key='training_dash_path')
    status_filter = f3.selectbox('Status', ['All', 'Completed', 'In Progress', 'Overdue', 'Due in 30 Days', 'Not Started'], key='training_dash_status')
    trainer_options = sorted({clean(x) for x in trainings.get('trainer_name', pd.Series(dtype=str)).astype(str) if clean(x)}) if not trainings.empty else []
    trainer_filter = f4.selectbox('Trainer', ['All'] + trainer_options, key='training_dash_trainer')
    filtered = active_records.copy()
    if not filtered.empty:
        if dept_filter != 'All' and (not users.empty) and ('user_id' in filtered.columns):
            user_dept = users[['user_id', 'department', 'departments']].copy() if 'department' in users.columns and 'departments' in users.columns else pd.DataFrame()
            if not user_dept.empty:
                user_dept['dept_text'] = user_dept['department'].fillna('').astype(str) + ' ' + user_dept['departments'].fillna('').astype(str)
                filtered = filtered.merge(user_dept[['user_id', 'dept_text']], on='user_id', how='left')
                filtered = filtered[filtered['dept_text'].str.contains(re.escape(dept_filter), case=False, na=False)]
        if path_filter != 'All' and (not users.empty) and ('user_id' in filtered.columns):
            path_map = users[['user_id', 'trainee_path']].copy()
            filtered = filtered.merge(path_map, on='user_id', how='left', suffixes=('', '_user'))
            filtered = filtered[filtered['trainee_path'].astype(str).eq(path_filter)]
        if trainer_filter != 'All' and (not trainings.empty) and ('training_id' in filtered.columns):
            trainer_map = trainings[['training_id', 'trainer_name']].copy()
            filtered = filtered.merge(trainer_map, on='training_id', how='left', suffixes=('', '_course'))
            filtered = filtered[filtered['trainer_name_course'].astype(str).eq(trainer_filter)]
        if status_filter != 'All':
            completed_mask = (filtered['progress'] >= 100) | filtered['test_norm'].eq('passed') | filtered['status_norm'].eq('completed')
            if status_filter == 'Completed':
                filtered = filtered[completed_mask]
            elif status_filter == 'In Progress':
                filtered = filtered[(filtered['progress'] > 0) & ~completed_mask]
            elif status_filter == 'Overdue':
                filtered = filtered[filtered['due_dt'].notna() & (filtered['due_dt'] < today_dt) & ~completed_mask]
            elif status_filter == 'Due in 30 Days':
                filtered = filtered[filtered['due_dt'].notna() & (filtered['due_dt'] >= today_dt) & (filtered['due_dt'] <= today_dt + pd.Timedelta(days=30)) & ~completed_mask]
            elif status_filter == 'Not Started':
                filtered = filtered[(filtered['progress'] <= 0) & ~completed_mask]
    st.subheader('Training Health')
    h1, h2 = st.columns(2)
    with h1:
        if not active_records.empty:
            status_counts = pd.DataFrame({'Status': ['Completed', 'In Progress', 'Overdue', 'Due in 30 Days', 'Not Started'], 'Count': [completed, in_progress, overdue, due30, max(assigned - completed - in_progress - overdue - due30, 0)]})
            st.bar_chart(status_counts.set_index('Status'))
        else:
            st.info('No training assignment data is available yet.')
    with h2:
        if not active_records.empty and (not trainings.empty) and ('training_id' in active_records.columns):
            joined = active_records.merge(trainings[['training_id', 'title']], on='training_id', how='left', suffixes=('', '_course'))
            by_course = joined.groupby('title')['progress'].agg(['count', 'mean']).sort_values('count', ascending=False).head(10).reset_index()
            by_course['mean'] = by_course['mean'].round(0)
            by_course.columns = ['Training', 'Assignments', 'Avg Progress %']
            st.dataframe(by_course, use_container_width=True, hide_index=True)
        else:
            st.info('Course-level training analytics will appear as assignments are created.')
    st.subheader('Attention Required')
    if not filtered.empty:
        display = filtered.copy()
        display['Display Status'] = 'In Progress'
        completed_mask = (display['progress'] >= 100) | display['test_norm'].eq('passed') | display['status_norm'].eq('completed')
        display.loc[completed_mask, 'Display Status'] = 'Completed'
        display.loc[display['due_dt'].notna() & (display['due_dt'] < today_dt) & ~completed_mask, 'Display Status'] = 'Overdue'
        display.loc[display['due_dt'].notna() & (display['due_dt'] >= today_dt) & (display['due_dt'] <= today_dt + pd.Timedelta(days=30)) & ~completed_mask, 'Display Status'] = 'Due in 30 Days'
        display.loc[(display['progress'] <= 0) & ~completed_mask, 'Display Status'] = 'Not Started'
        cols = [c for c in ['name', 'training_title', 'progress', 'due_date', 'Display Status', 'test_status'] if c in display.columns]
        table(display.sort_values(['Display Status', 'due_dt'], na_position='last')[cols].head(50))
    else:
        st.success('No training items match the current filters.')
    st.subheader('Training Operations')
    a, b, c = st.columns(3)
    if a.button('Open Training', key='training_dash_open_training', use_container_width=True):
        st.session_state['psb_current_page'] = 'Training'
        st.rerun()
    if b.button('Open Training Matrix', key='training_dash_open_matrix', use_container_width=True):
        st.session_state['psb_current_page'] = 'Training Matrix'
        st.rerun()
    if c.button('Open Knowledge Library', key='training_dash_open_library', use_container_width=True):
        st.session_state['psb_current_page'] = 'Knowledge Library'
        st.rerun()

def training_matrix_page(actor):
    """Authoritative training-requirement matrix.

    Training Matrix owns requirement rules; training_records own actual learner
    assignments/completion. The matrix never duplicates completion values.
    """
    st.header('Training Matrix')
    st.caption('Define what each person is required to complete. Actual attendance, assessment and completion remain authoritative in Training Records.')
    role = actor_get(actor, 'role')
    can_manage = can_action(actor, 'Training Matrix', 'Edit', 'Department') or can_action(actor, 'Training Matrix', 'Manage', 'Organization-wide')
    # Schema is owned by database migrations; no page-level DDL.
    modules = db_all('training_modules')
    users = db_all('users')
    reqs = db_all('training_requirements')
    if not modules.empty and reqs.empty:
        for _, m in modules.iterrows():
            db_insert('training_requirements', {'requirement_id': uid('REQ'), 'module_id': m.get('module_id', ''), 'requirement_name': m.get('title', ''), 'department': 'All', 'role': 'All', 'trainee_path': m.get('target_path', 'All') or 'All', 'requirement_type': 'Core' if m.get('mandatory') == 'Yes' else 'Recommended', 'mandatory': m.get('mandatory', 'No') or 'No', 'priority': 'High' if m.get('mandatory') == 'Yes' else 'Medium', 'prerequisite_module_ids': '', 'sequence_no': 0, 'validity_months': int(m.get('validity_months', 36) or 36), 'effective_from': str(m.get('created_on', today()) or today()), 'effective_to': '', 'active': 'Yes', 'notes': 'Migrated from training module target path.', 'created_by': m.get('added_by', 'System'), 'created_on': now(), 'updated_by': actor_get(actor, 'name'), 'updated_on': now()})
        reqs = db_all('training_requirements')
    if can_manage:
        tabs = st.tabs(['Matrix Overview', 'Requirement Rules', 'Coverage & Gaps'])
    else:
        tabs = st.tabs(['Matrix Overview', 'Coverage & Gaps'])
    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        active_reqs = reqs[reqs['active'].fillna('Yes') == 'Yes'] if not reqs.empty else reqs
        record_df = db_all('training_records')
        total_required = 0
        total_completed = 0
        total_overdue = 0
        learner_count = 0
        today_str = str(date.today())
        if not users.empty and (not active_reqs.empty):
            for _, u in users[users['status'].fillna('') == 'Active'].iterrows():
                matched = []
                u_depts = set(split_list(u.get('department', '')))
                for _, r in active_reqs.iterrows():
                    dept = clean(r.get('department', 'All')) or 'All'
                    role_match = clean(r.get('role', 'All')) in ['', 'All', clean(u.get('role', ''))]
                    path_match = clean(r.get('trainee_path', 'All')) in ['', 'All', clean(u.get('trainee_path', ''))]
                    dept_match = dept in ['', 'All'] or dept in u_depts or dept == clean(u.get('primary_department', ''))
                    if role_match and path_match and dept_match:
                        matched.append(r)
                if matched:
                    learner_count += 1
                total_required += sum((1 for r in matched if clean(r.get('mandatory', 'No')) == 'Yes'))
                uidv = clean(u.get('user_id', ''))
                recs_u = record_df[record_df['user_id'] == uidv] if not record_df.empty else pd.DataFrame()
                for r in matched:
                    if clean(r.get('mandatory', 'No')) != 'Yes':
                        continue
                    rid = clean(r.get('module_id', ''))
                    rr = recs_u[recs_u['training_id'] == rid] if not recs_u.empty else pd.DataFrame()
                    if not rr.empty:
                        status = clean(rr.iloc[-1].get('status', ''))
                        if status == 'Completed':
                            total_completed += 1
                        due = clean(rr.iloc[-1].get('due_date', ''))
                        if due and due < today_str and (status != 'Completed'):
                            total_overdue += 1
        completion_rate = total_completed / total_required * 100 if total_required else 0
        c1.metric('Active Requirements', int(len(active_reqs)))
        c2.metric('Learners in Matrix', learner_count)
        c3.metric('Mandatory Completion', f'{completion_rate:.0f}%')
        c4.metric('Overdue Requirements', total_overdue)
        f1, f2, f3, f4 = st.columns(4)
        dept_filter = f1.selectbox('Department', ['All'] + DEPARTMENTS, key='tm_dept')
        role_filter = f2.selectbox('Role', ['All'] + ROLES, key='tm_role')
        path_filter = f3.selectbox('Trainee Path', ['All'] + TRAINEE_PATHS, key='tm_path')
        status_filter = f4.selectbox('Requirement Status', ['All', 'Active', 'Inactive'], key='tm_req_status')
        search = st.text_input('Search requirement or employee', key='tm_search')
        rows = []
        active_user_df = users[users['status'].fillna('') == 'Active'] if not users.empty else pd.DataFrame()
        for _, u in active_user_df.iterrows():
            u_depts = set(split_list(u.get('department', '')))
            for _, r in active_reqs.iterrows():
                dept = clean(r.get('department', 'All')) or 'All'
                role_name = clean(r.get('role', 'All')) or 'All'
                path_name = clean(r.get('trainee_path', 'All')) or 'All'
                if dept_filter != 'All' and dept_filter != dept:
                    continue
                if role_filter != 'All' and role_filter != role_name:
                    continue
                if path_filter != 'All' and path_filter != path_name:
                    continue
                if status_filter != 'All' and clean(r.get('active', 'Yes')) != ('Yes' if status_filter == 'Active' else 'No'):
                    continue
                role_match = role_name in ['', 'All', clean(u.get('role', ''))]
                path_match = path_name in ['', 'All', clean(u.get('trainee_path', ''))]
                dept_match = dept in ['', 'All'] or dept in u_depts or dept == clean(u.get('primary_department', ''))
                if not (role_match and path_match and dept_match):
                    continue
                if search and search.lower() not in f"{u.get('name', '')} {r.get('requirement_name', '')}".lower():
                    continue
                recs = record_df[(record_df['user_id'] == u.get('user_id')) & (record_df['training_id'] == r.get('module_id'))] if not record_df.empty else pd.DataFrame()
                latest = recs.iloc[-1] if not recs.empty else None
                status = clean(latest.get('status', 'Not Assigned')) if latest is not None else 'Not Assigned'
                progress = int(latest.get('progress', 0) or 0) if latest is not None else 0
                due = clean(latest.get('due_date', '')) if latest is not None else ''
                if due and due < today_str and (status != 'Completed'):
                    status_display = 'Overdue'
                elif status == 'Completed':
                    status_display = 'Completed'
                elif status in ['In Progress', 'Scheduled']:
                    status_display = status
                else:
                    status_display = 'Required'
                rows.append({'Employee': u.get('name', ''), 'Employee ID': u.get('employee_id', ''), 'Department': u.get('primary_department', u.get('department', '')), 'Requirement': r.get('requirement_name', ''), 'Type': r.get('requirement_type', ''), 'Mandatory': r.get('mandatory', 'No'), 'Status': status_display, 'Progress': progress, 'Due': due, 'Requirement ID': r.get('requirement_id', ''), 'Module ID': r.get('module_id', '')})
        matrix_df = pd.DataFrame(rows)
        if matrix_df.empty:
            st.info('No matching matrix requirements found.')
        else:
            table(matrix_df.drop(columns=['Requirement ID', 'Module ID']))
            st.markdown('### Requirement actions')
            st.caption('The Matrix defines requirements; Training Records remain the authoritative completion records.')
            if can_manage:
                action_items = matrix_df.apply(lambda x: f"{x['Employee']} — {x['Requirement']} — {x['Requirement ID']}", axis=1).tolist()
                selected = st.selectbox('Select matrix item', action_items, key='tm_action_item') if action_items else ''
                if st.button('Create Missing Training Assignment', key='tm_assign_missing', use_container_width=True):
                    if not selected:
                        st.error('Select a matrix requirement first.')
                    else:
                        req_id = selected.split(' — ')[-1]
                        row = matrix_df[matrix_df['Requirement ID'] == req_id].iloc[0]
                        module_id = clean(row['Module ID'])
                        u = users[users['name'].astype(str) == str(row['Employee'])].iloc[0]
                        existing = record_df[(record_df['user_id'] == u['user_id']) & (record_df['training_id'] == module_id)] if not record_df.empty else pd.DataFrame()
                        if existing.empty:
                            tr = db_all('trainings')
                            matches = tr[tr['module_id'] == module_id] if not tr.empty else pd.DataFrame()
                            if matches.empty:
                                st.warning('No actual Training course exists for this matrix module yet. Create the course in Training first.')
                            else:
                                course = matches.iloc[0]
                                db_insert('training_records', {'record_id': uid('REC'), 'user_id': u['user_id'], 'name': u['name'], 'role': u['role'], 'trainee_path': u.get('trainee_path', ''), 'training_id': course['training_id'], 'training_title': course['title'], 'status': 'Assigned', 'slides_opened': 'No', 'video_opened': 'No', 'live_attendance': 'No', 'recording_opened': 'No', 'lms_completed': 'No', 'test_status': 'Pending', 'score': None, 'passing_marks': int(course.get('passing_marks', 75) or 75), 'certificate_status': 'Not Issued', 'certificate_link': '', 'due_date': str(date.today() + timedelta(days=30)), 'completed_on': '', 'progress': 0, 'remarks': 'Assignment generated from Training Matrix requirement.', 'updated_on': now()})
                                audit('Training Assignment Generated', f"{u['name']} — {course['title']}", actor=actor, entity_type='training_records', entity_id='matrix')
                                st.success('Training assignment created from the matrix.')
                                st.rerun()
                        else:
                            st.info('This employee already has a training record for the selected requirement; no duplicate was created.')
    tab_idx = 1 if can_manage else 1
    if can_manage:
        with tabs[1]:
            st.subheader('Requirement Rules')
            st.caption('Define applicability here. Do not enter learner completion here.')
            if not modules.empty:
                with st.form('training_requirement_add'):
                    c1, c2, c3 = st.columns(3)
                    module_sel = c1.selectbox('Training Module', modules['title'].astype(str) + ' — ' + modules['module_id'].astype(str))
                    dept = c2.selectbox('Department', ['All'] + DEPARTMENTS)
                    role_sel = c3.selectbox('Role', ['All'] + ROLES)
                    path_sel = c1.selectbox('Trainee Path', ['All'] + TRAINEE_PATHS)
                    req_type = c2.selectbox('Requirement Type', ['Core', 'Compliance', 'Refresher', 'Recommended'])
                    mandatory = c3.checkbox('Mandatory', True)
                    priority = c1.selectbox('Priority', ['Low', 'Medium', 'High', 'Critical'], index=2)
                    sequence_no = c2.number_input('Sequence', 0, 999, 0)
                    validity = c3.number_input('Validity (months)', 1, 120, 36)
                    notes = st.text_area('Notes')
                    submit = st.form_submit_button('Create Requirement', use_container_width=True)
                if submit:
                    title, module_id = module_sel.split(' — ')
                    db_insert('training_requirements', {'requirement_id': uid('REQ'), 'module_id': module_id, 'requirement_name': title, 'department': dept, 'role': role_sel, 'trainee_path': path_sel, 'requirement_type': req_type, 'mandatory': 'Yes' if mandatory else 'No', 'priority': priority, 'prerequisite_module_ids': '', 'sequence_no': int(sequence_no), 'validity_months': int(validity), 'effective_from': today(), 'effective_to': '', 'active': 'Yes', 'notes': notes, 'created_by': actor_get(actor, 'name'), 'created_on': now(), 'updated_by': actor_get(actor, 'name'), 'updated_on': now()})
                    audit('Training Requirement Created', title, actor=actor, entity_type='training_requirements', entity_id='new')
                    st.success('Requirement rule created.')
                    st.rerun()
            current = db_all('training_requirements')
            if not current.empty:
                show_cols = [c for c in ['requirement_id', 'requirement_name', 'department', 'role', 'trainee_path', 'requirement_type', 'mandatory', 'priority', 'sequence_no', 'active'] if c in current.columns]
                table(current[show_cols])
                selected_req = st.selectbox('Select requirement to manage', current['requirement_name'].astype(str) + ' — ' + current['requirement_id'].astype(str), key='tm_manage_req')
                req_id = selected_req.split(' — ')[-1]
                rr = current[current['requirement_id'] == req_id].iloc[0]
                if st.button('Toggle Active / Inactive', key='tm_toggle_req'):
                    new_active = 'No' if clean(rr.get('active', 'Yes')) == 'Yes' else 'Yes'
                    db_update('training_requirements', 'requirement_id', req_id, {'active': new_active, 'updated_by': actor_get(actor, 'name'), 'updated_on': now()})
                    audit('Training Requirement Status Changed', rr.get('requirement_name', ''), actor=actor, entity_type='training_requirements', entity_id=req_id)
                    st.success('Requirement status updated.')
                    st.rerun()
    with tabs[2] if can_manage else tabs[1]:
        st.subheader('Coverage & Gaps')
        st.caption('This view identifies requirements not yet completed. The remedy is assigned through Training, Development Plans or Competency—not by duplicating requirements here.')
        if not matrix_df.empty:
            gaps = matrix_df[matrix_df['Status'].isin(['Required', 'Overdue', 'In Progress', 'Assigned'])]
            if gaps.empty:
                st.success('No outstanding training requirements in the selected filter.')
            else:
                st.metric('Open Training Gaps', len(gaps))
                table(gaps.drop(columns=['Requirement ID', 'Module ID']))

def training_page(actor):
    """Professional training course and learner-record workflow.

    Training is the source of truth for course delivery and actual learner records.
    Requirement rules live in Training Matrix; Development/Competency/Authorization only
    consume the resulting training status.
    """
    st.header('Training')
    st.caption('Authoritative course-delivery workflow: catalogue → schedule → materials → assignment → attendance → assessment → completion/certificate.')
    role = actor_get(actor, 'role')
    adminish = can_action(actor, 'Training', 'Manage', 'Organization-wide') or can_action(actor, 'Training', 'Edit', 'Assigned')
    users = db_all('users')
    modules = db_all('training_modules')
    trainings = db_all('trainings')
    if adminish:
        tabs = st.tabs(['Course Catalogue', 'Create Course', 'Course Workspace'])
    else:
        tabs = st.tabs(['My Training', 'Course Workspace'])
    if adminish:
        with tabs[0]:
            c1, c2, c3, c4 = st.columns(4)
            active_courses = int(len(trainings[trainings.get('status', pd.Series(dtype=str)).isin(['Draft', 'Scheduled', 'In Progress'])]) if not trainings.empty else 0)
            scheduled = int(len(trainings[trainings.get('status', pd.Series(dtype=str)) == 'Scheduled']) if not trainings.empty else 0)
            completed_courses = int(len(trainings[trainings.get('status', pd.Series(dtype=str)) == 'Completed']) if not trainings.empty else 0)
            archived = int(len(trainings[trainings.get('status', pd.Series(dtype=str)) == 'Archived']) if not trainings.empty else 0)
            c1.metric('Active Courses', active_courses)
            c2.metric('Scheduled', scheduled)
            c3.metric('Completed', completed_courses)
            c4.metric('Archived', archived)
            q1, q2, q3 = st.columns(3)
            with q1:
                search = st.text_input('Search courses', key='training_course_search')
            with q2:
                status_filter = st.selectbox('Status', ['All', 'Draft', 'Scheduled', 'In Progress', 'Completed', 'Cancelled', 'Archived'], key='training_status_filter')
            with q3:
                trainer_filter = st.selectbox('Trainer', ['All'] + (sorted(trainings['trainer_name'].dropna().astype(str).unique().tolist()) if not trainings.empty and 'trainer_name' in trainings.columns else []), key='training_trainer_filter')
            view = trainings.copy()
            if not view.empty:
                if search:
                    mask = view.apply(lambda r: search.lower() in ' '.join(map(str, r.tolist())).lower(), axis=1)
                    view = view[mask]
                if status_filter != 'All' and 'status' in view.columns:
                    view = view[view['status'] == status_filter]
                if trainer_filter != 'All' and 'trainer_name' in view.columns:
                    view = view[view['trainer_name'] == trainer_filter]
                show_cols = [c for c in ['training_id', 'title', 'category', 'delivery_mode', 'schedule_date', 'trainer_name', 'status', 'capacity', 'course_version'] if c in view.columns]
                table(view[show_cols], max_rows=200)
            else:
                st.info('No courses are available yet. Create the first course from a training module.')
        with tabs[1]:
            st.subheader('Create Course')
            st.caption('Create a delivery instance from an approved Training Matrix/module requirement. Do not create requirement rules here.')
            if modules.empty:
                st.warning('No training modules are available. Configure the Training Matrix/module catalogue first.')
            else:
                trainers = users[(users.get('role', pd.Series(dtype=str)) == 'Trainer') & (users.get('status', pd.Series(dtype=str)) == 'Active')] if not users.empty else pd.DataFrame()
                with st.form('create_training_course_professional'):
                    c1, c2 = st.columns(2)
                    module_sel = c1.selectbox('Training Module *', modules['title'].astype(str) + ' — ' + modules['module_id'].astype(str))
                    title = c2.text_input('Course Title *')
                    category = c1.text_input('Category', value='Technical Training')
                    trainer = c2.selectbox('Trainer *', trainers['name'].astype(str) + ' — ' + trainers['user_id'].astype(str)) if not trainers.empty else ''
                    delivery_mode = c1.selectbox('Delivery Mode', ['Classroom', 'Online', 'Blended', 'Self-paced', 'Workshop', 'Field-based'])
                    duration = c2.number_input('Duration (hours)', min_value=0.0, max_value=500.0, value=8.0, step=0.5)
                    schedule_date = c1.date_input('Schedule Date', value=date.today() + timedelta(days=7))
                    schedule_time = c2.text_input('Schedule Time', value='10:00')
                    location = c1.text_input('Location / Platform', placeholder='Room, Teams, LMS, etc.')
                    capacity = c2.number_input('Capacity', min_value=0, max_value=5000, value=20, step=1)
                    version = c1.text_input('Course Version', value='1.0')
                    passing = c2.number_input('Passing Marks', min_value=1, max_value=100, value=75)
                    assessment_required = c1.selectbox('Assessment Required', ['Yes', 'No'])
                    certificate_required = c2.selectbox('Certificate Required', ['Yes', 'No'])
                    prerequisite = st.text_input('Prerequisite / Entry Condition')
                    target_roles = st.multiselect('Target Roles', ROLES, default=['Trainee'])
                    submit = st.form_submit_button('Create Course', type='primary', use_container_width=True)
                if submit:
                    if not title.strip() or not trainer:
                        st.error('Course title and Trainer are required.')
                    else:
                        module_title, module_id = module_sel.split(' — ')
                        trainer_name, trainer_id = trainer.split(' — ')
                        module = modules[modules['module_id'] == module_id].iloc[0]
                        tid = uid('TRN')
                        row = {'training_id': tid, 'module_id': module_id, 'title': title.strip(), 'category': category, 'standards': join_list(STANDARDS), 'target_roles': join_list(target_roles), 'target_paths': module.get('target_path', ''), 'trainer_id': trainer_id, 'trainer_name': trainer_name, 'slides_link': '', 'video_link': '', 'reference_link': '', 'scorm_package_link': '', 'lms_course_id': '', 'schedule_date': str(schedule_date), 'schedule_time': schedule_time, 'meeting_link': '', 'recording_link': '', 'passing_marks': passing, 'validity_months': int(module.get('validity_months') or 36), 'max_attempts': 3, 'retest_wait_days': 7, 'status': 'Draft', 'created_on': now(), 'updated_on': now(), 'delivery_mode': delivery_mode, 'duration_hours': duration, 'location_or_platform': location, 'capacity': capacity, 'enrollment_open': 'No', 'course_version': version, 'prerequisite_text': prerequisite, 'assessment_required': assessment_required, 'certificate_required': certificate_required}
                        db_insert('trainings', row)
                        audit('Training Course Created', f'{title} ({tid})', actor=actor, entity_type='trainings', entity_id=tid, reason='New course created')
                        st.success('Course created. Complete its materials and schedule in Course Workspace before opening enrollment.')
                        st.session_state['selected_training_id'] = tid
                        st.rerun()
        with tabs[2]:
            _training_course_workspace(actor, trainings, users, show_admin_controls=True)
    else:
        with tabs[0]:
            rec = db_all('training_records')
            mine = rec[rec['user_id'] == actor_get(actor, 'user_id')] if not rec.empty else pd.DataFrame()
            metrics([('Assigned', len(mine)), ('In Progress', len(mine[mine['status'] == 'In Progress']) if not mine.empty else 0), ('Completed', len(mine[mine['status'] == 'Completed']) if not mine.empty else 0), ('Overdue', len(mine[(mine['status'] != 'Completed') & (mine['due_date'].astype(str) < str(date.today()))]) if not mine.empty else 0)])
            if mine.empty:
                st.info('No training has been assigned to you.')
            else:
                table(mine[[c for c in ['record_id', 'training_title', 'status', 'progress', 'due_date', 'test_status', 'certificate_status'] if c in mine.columns]])
                options = mine['training_title'].astype(str) + ' — ' + mine['training_id'].astype(str)
                selected = st.selectbox('Open assigned training', options)
                st.session_state['selected_training_id'] = selected.split(' — ')[-1]
        with tabs[1]:
            _training_course_workspace(actor, trainings, users, show_admin_controls=False)

def _training_course_workspace(actor, trainings, users, show_admin_controls=False):
    role = actor_get(actor, 'role')
    if 'selected_training_id' in st.session_state and st.session_state.get('selected_training_id'):
        default_id = st.session_state.get('selected_training_id')
    else:
        default_id = ''
    available = trainings.copy() if isinstance(trainings, pd.DataFrame) else pd.DataFrame()
    if can_action(actor, 'Training', 'Edit', 'Assigned') and (not available.empty):
        available = available[available['trainer_id'] == actor_get(actor, 'user_id')]
    elif not can_action(actor, 'Training', 'View', 'Organization-wide') and (not can_action(actor, 'Training', 'View', 'Department')):
        rec = db_all('training_records')
        ids = rec[rec['user_id'] == actor_get(actor, 'user_id')]['training_id'].tolist() if not rec.empty else []
        available = available[available['training_id'].isin(ids)] if not available.empty else available
    if available.empty:
        st.info('No training course is available for this user.')
        return
    options = available['title'].astype(str) + ' — ' + available['training_id'].astype(str)
    matching = [i for i, opt in enumerate(options) if opt.split(' — ')[-1] == default_id]
    idx = matching[0] if matching else 0
    selected = st.selectbox('Course', options, index=idx, key='training_workspace_select')
    tid = selected.split(' — ')[-1]
    tr = available[available['training_id'] == tid].iloc[0]
    st.subheader(clean(tr.get('title')))
    st.caption(f"Module: {clean(tr.get('module_id')) or '—'} · Version {clean(tr.get('course_version')) or '—'} · {clean(tr.get('delivery_mode')) or '—'} · Trainer: {clean(tr.get('trainer_name')) or '—'}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Status', clean(tr.get('status')) or 'Draft')
    m2.metric('Schedule', clean(tr.get('schedule_date')) or 'Not set')
    m3.metric('Capacity', clean(tr.get('capacity')) or '—')
    m4.metric('Assessment', clean(tr.get('assessment_required')) or 'Yes')
    if show_admin_controls:
        t1, t2, t3, t4, t5 = st.tabs(['Overview', 'Materials', 'Assessment', 'Assignments', 'Attendance & Certificates'])
        with t1:
            with st.form(f'edit_training_{tid}'):
                c1, c2 = st.columns(2)
                title = c1.text_input('Course Title', tr.get('title', ''))
                category = c2.text_input('Category', tr.get('category', ''))
                trainer_options = list(users[(users.get('role', pd.Series(dtype=str)) == 'Trainer') & (users.get('status', pd.Series(dtype=str)) == 'Active')]['name'].astype(str) + ' — ' + users[(users.get('role', pd.Series(dtype=str)) == 'Trainer') & (users.get('status', pd.Series(dtype=str)) == 'Active')]['user_id'].astype(str)) if not users.empty else []
                current_trainer = f"{tr.get('trainer_name', '')} — {tr.get('trainer_id', '')}"
                if current_trainer not in trainer_options and current_trainer.strip(' —'):
                    trainer_options = [current_trainer] + trainer_options
                trainer_selected = c1.selectbox('Trainer', trainer_options or ['—'], index=0)
                status_options = ['Draft', 'Scheduled', 'In Progress', 'Completed', 'Cancelled', 'Archived']
                cur_status = clean(tr.get('status')) if clean(tr.get('status')) in status_options else 'Draft'
                status = c2.selectbox('Course Status', status_options, index=status_options.index(cur_status))
                delivery_mode = c1.selectbox('Delivery Mode', ['Classroom', 'Online', 'Blended', 'Self-paced', 'Workshop', 'Field-based'], index=['Classroom', 'Online', 'Blended', 'Self-paced', 'Workshop', 'Field-based'].index(clean(tr.get('delivery_mode'))) if clean(tr.get('delivery_mode')) in ['Classroom', 'Online', 'Blended', 'Self-paced', 'Workshop', 'Field-based'] else 0)
                duration = c2.number_input('Duration (hours)', 0.0, 500.0, float(tr.get('duration_hours') or 0), step=0.5)
                schedule_date = c1.date_input('Schedule Date', value=datetime.fromisoformat(clean(tr.get('schedule_date'))).date() if clean(tr.get('schedule_date')) else date.today())
                schedule_time = c2.text_input('Schedule Time', value=clean(tr.get('schedule_time')) or '10:00')
                location = c1.text_input('Location / Platform', value=clean(tr.get('location_or_platform')))
                capacity = c2.number_input('Capacity', 0, 5000, int(tr.get('capacity') or 0), 1)
                enrollment_open = c1.selectbox('Enrollment Open', ['No', 'Yes'], index=1 if clean(tr.get('enrollment_open')) == 'Yes' else 0)
                passing = c2.number_input('Passing Marks', 1, 100, int(tr.get('passing_marks') or 75))
                assessment_required = c1.selectbox('Assessment Required', ['Yes', 'No'], index=0 if clean(tr.get('assessment_required')) != 'No' else 1)
                certificate_required = c2.selectbox('Certificate Required', ['Yes', 'No'], index=0 if clean(tr.get('certificate_required')) != 'No' else 1)
                prerequisite = st.text_input('Prerequisite / Entry Condition', value=clean(tr.get('prerequisite_text')))
                save = st.form_submit_button('Save Course', type='primary')
            if save:
                tname, tidv = trainer_selected.split(' — ') if ' — ' in trainer_selected else (tr.get('trainer_name', ''), tr.get('trainer_id', ''))
                db_update('trainings', 'training_id', tid, {'title': title, 'category': category, 'trainer_id': tidv, 'trainer_name': tname, 'status': status, 'delivery_mode': delivery_mode, 'duration_hours': duration, 'schedule_date': str(schedule_date), 'schedule_time': schedule_time, 'location_or_platform': location, 'capacity': capacity, 'enrollment_open': enrollment_open, 'passing_marks': passing, 'assessment_required': assessment_required, 'certificate_required': certificate_required, 'prerequisite_text': prerequisite, 'updated_on': now()})
                audit('Training Course Updated', title, actor=actor, entity_type='trainings', entity_id=tid, reason='Course workspace update')
                st.success('Course saved.')
                st.rerun()
            if clean(tr.get('status')) != 'Archived':
                with st.expander('Archive Course', expanded=False):
                    reason = st.text_input('Archive reason', key=f'archive_reason_{tid}')
                    if st.button('Archive Course', key=f'archive_course_{tid}'):
                        if not reason.strip():
                            st.error('Archive reason is required.')
                        else:
                            db_update('trainings', 'training_id', tid, {'status': 'Archived', 'archived_on': now(), 'archived_by': actor_get(actor, 'name'), 'archive_reason': reason.strip(), 'updated_on': now()})
                            audit('Training Course Archived', tr.get('title', ''), actor=actor, entity_type='trainings', entity_id=tid, reason=reason.strip())
                            st.success('Course archived. Historical learner records remain intact.')
                            st.rerun()
        with t2:
            st.markdown('### Course materials')
            file_upload_panel(actor, 'trainings', tid, 'Training Material')
            f = db_where('files', 'linked_table = :linked_table and linked_id = :linked_id', (('linked_table', 'trainings'), ('linked_id', tid)))
            if not f.empty:
                table(f[[c for c in ['file_id', 'file_name', 'category', 'review_status', 'created_on'] if c in f.columns]])
            c1, c2 = st.columns(2)
            with c1:
                slides = st.text_input('Slides URL', value=clean(tr.get('slides_link')))
                video = st.text_input('Video URL', value=clean(tr.get('video_link')))
            with c2:
                reference = st.text_input('Reference URL', value=clean(tr.get('reference_link')))
                scorm = st.text_input('LMS/SCORM URL', value=clean(tr.get('scorm_package_link')))
            if st.button('Save Materials & Links', key=f'save_materials_{tid}'):
                db_update('trainings', 'training_id', tid, {'slides_link': slides, 'video_link': video, 'reference_link': reference, 'scorm_package_link': scorm, 'updated_on': now()})
                audit('Training Materials Updated', tr.get('title', ''), actor=actor, entity_type='trainings', entity_id=tid)
                st.success('Materials saved.')
        with t3:
            st.markdown('### Assessment')
            st.caption('Assessment content stays attached to this course. Completion is controlled by the configured assessment requirement.')
            extracted = ''
            f = db_where('files', 'linked_table = :linked_table and linked_id = :linked_id', (('linked_table', 'trainings'), ('linked_id', tid)))
            if not f.empty and 'extracted_text' in f.columns:
                extracted = '\n'.join(f['extracted_text'].fillna('').astype(str).tolist())
            content = st.text_area('Assessment source text', value=extracted, height=180)
            count = st.slider('MCQ count', 5, 50, 10)
            if st.button('Generate / Refresh MCQs', key=f'gen_mcq_{tid}'):
                qs = generate_mcqs(tid, content, count)
                if qs.empty:
                    st.error('Assessment questions could not be generated. Provide clearer source text.')
                else:
                    old_q = db_where('question_bank', 'training_id = :tid', (('tid', tid),))
                    for _, old_row in old_q.iterrows():
                        db_delete('question_bank', 'question_id', str(old_row.get('question_id', '')))
                    for _, q in qs.iterrows():
                        db_insert('question_bank', q.to_dict())
                    audit('Training Assessment Refreshed', tr.get('title', ''), actor=actor, entity_type='trainings', entity_id=tid)
                    st.success(f'{len(qs)} assessment questions are ready.')
            q = db_where('question_bank', 'training_id = :training_id', (('training_id', tid),))
            if q.empty:
                st.info('No assessment questions yet.')
            else:
                table(q[[c for c in ['question_id', 'question', 'marks'] if c in q.columns]])
                st.metric('Questions', len(q))
                with st.expander('Assessment rules'):
                    st.write(f"Passing marks: {tr.get('passing_marks', 75)}")
                    st.write(f"Maximum attempts: {tr.get('max_attempts', 3)}")
                    st.write(f"Retest wait: {tr.get('retest_wait_days', 7)} day(s)")
        with t4:
            st.markdown('### Learner assignments')
            rec = db_all('training_records')
            assigned = rec[rec['training_id'] == tid] if not rec.empty else pd.DataFrame()
            if not assigned.empty:
                table(assigned[[c for c in ['record_id', 'name', 'role', 'status', 'progress', 'due_date', 'test_status', 'certificate_status'] if c in assigned.columns]])
            active_users = users[users.get('status', pd.Series(dtype=str)) == 'Active'] if not users.empty else pd.DataFrame()
            target_roles = set(split_list(tr.get('target_roles')))
            if target_roles and (not active_users.empty) and ('role' in active_users.columns):
                eligible = active_users[active_users['role'].isin(target_roles)]
            else:
                eligible = active_users
            already = set(assigned['user_id'].astype(str).tolist()) if not assigned.empty else set()
            eligible = eligible[~eligible['user_id'].astype(str).isin(already)] if not eligible.empty else eligible
            st.caption('Assignments are unique per person/course. Existing records are never duplicated.')
            selected_users = st.multiselect('Select learners', eligible['name'].astype(str) + ' — ' + eligible['user_id'].astype(str) if not eligible.empty else [], key=f'assign_learners_{tid}')
            due = st.date_input('Due date', date.today() + timedelta(days=30), key=f'due_{tid}')
            if st.button('Assign Selected Learners', key=f'assign_training_{tid}', type='primary'):
                recs = db_all('training_records')
                added = 0
                for item in selected_users:
                    name, uidv = item.split(' — ')
                    existing = recs[(recs['user_id'] == uidv) & (recs['training_id'] == tid)] if not recs.empty else pd.DataFrame()
                    if not existing.empty:
                        continue
                    u = users[users['user_id'] == uidv].iloc[0]
                    db_insert('training_records', {'record_id': uid('REC'), 'user_id': uidv, 'name': name, 'role': u.get('role', ''), 'trainee_path': u.get('trainee_path', ''), 'training_id': tid, 'training_title': tr.get('title', ''), 'status': 'Pending', 'slides_opened': 'No', 'video_opened': 'No', 'live_attendance': 'Not Marked', 'recording_opened': 'No', 'lms_completed': 'No', 'test_status': 'Not Attempted', 'score': None, 'passing_marks': int(tr.get('passing_marks') or 75), 'certificate_status': 'Not Issued', 'certificate_link': '', 'due_date': str(due), 'completed_on': '', 'progress': 0, 'remarks': 'Assigned', 'updated_on': now(), 'assigned_on': now(), 'assigned_by': actor_get(actor, 'name'), 'assessment_attempts': 0, 'last_assessment_on': '', 'certificate_id': '', 'certificate_issued_on': '', 'certificate_issued_by': ''})
                    create_notification(uidv, f"Training Assigned: {tr.get('title', '')}", f"You have been assigned {tr.get('title', '')}. Due date: {due}.", 'Training')
                    added += 1
                audit('Training Learners Assigned', f"{added} learner(s) assigned to {tr.get('title', '')}", actor=actor, entity_type='trainings', entity_id=tid)
                st.success(f'{added} learner(s) assigned.')
                st.rerun()
        with t5:
            rec = db_all('training_records')
            assigned = rec[rec['training_id'] == tid] if not rec.empty else pd.DataFrame()
            st.markdown('### Attendance')
            if assigned.empty:
                st.info('No learners assigned.')
            else:
                person = st.selectbox('Learner', assigned['name'].astype(str) + ' — ' + assigned['user_id'].astype(str), key=f'attendee_{tid}')
                uidv = person.split(' — ')[-1]
                rr = assigned[assigned['user_id'] == uidv].iloc[0]
                att = st.selectbox('Attendance', ['Present', 'Absent', 'Recording Viewed'], index=['Present', 'Absent', 'Recording Viewed'].index(clean(rr.get('live_attendance')) if clean(rr.get('live_attendance')) in ['Present', 'Absent', 'Recording Viewed'] else 'Present'))
                if st.button('Save Attendance', key=f'save_att_{tid}'):
                    db_update('training_records', 'record_id', rr['record_id'], {'live_attendance': att, 'attendance_marked_on': now(), 'updated_on': now()})
                    update_training_progress(rr['record_id'])
                    audit('Training Attendance Updated', f"{rr.get('name', '')} — {tr.get('title', '')}", actor=actor, entity_type='training_records', entity_id=rr['record_id'], reason=f'Attendance: {att}')
                    st.success('Attendance saved.')
                    st.rerun()
            st.markdown('### Certificate')
            if not assigned.empty:
                eligible = assigned[assigned['test_status'] == 'Passed'] if 'test_status' in assigned.columns else pd.DataFrame()
                if eligible.empty:
                    st.info('Certificates can be issued only after the required assessment is passed.')
                else:
                    cert_person = st.selectbox('Eligible learner', eligible['name'].astype(str) + ' — ' + eligible['user_id'].astype(str), key=f'cert_{tid}')
                    cert_uid = cert_person.split(' — ')[-1]
                    cert_row = eligible[eligible['user_id'] == cert_uid].iloc[0]
                    cert_id = st.text_input('Certificate ID', value=clean(cert_row.get('certificate_id')) or f'PSB-TRN-{tid}-{cert_uid}')
                    if st.button('Issue Certificate', key=f'issue_cert_{tid}', type='primary'):
                        db_update('training_records', 'record_id', cert_row['record_id'], {'certificate_status': 'Issued', 'certificate_id': cert_id, 'certificate_issued_on': now(), 'certificate_issued_by': actor_get(actor, 'name'), 'updated_on': now()})
                        audit('Training Certificate Issued', f"{cert_id} — {cert_row.get('name', '')}", actor=actor, entity_type='training_records', entity_id=cert_row['record_id'], reason='Assessment passed')
                        st.success('Certificate issued and audit-recorded.')
                        st.rerun()
    else:
        trainee_training(actor, tid)

def _assessment_window_open(conf):
    now_dt = datetime.now()
    def parse(v):
        text = clean(v)
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace('Z','+00:00')).replace(tzinfo=None)
        except Exception:
            try:
                return datetime.strptime(text[:19], '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    return datetime.strptime(text[:10], '%Y-%m-%d')
                except Exception:
                    return None
    start=parse(conf.get('available_from')); end=parse(conf.get('available_until'))
    if start and now_dt < start:
        return False, f"Assessment opens on {start.strftime('%Y-%m-%d %H:%M')}"
    if end and now_dt > end:
        return False, f"Assessment closed on {end.strftime('%Y-%m-%d %H:%M')}"
    return True, ''

def _stable_question_rows(qs, session_id, randomize_questions='Yes'):
    rows=[r.to_dict() for _,r in qs.iterrows()]
    if str(randomize_questions)=='Yes':
        seed=int(hashlib.sha256(f"{session_id}:questions".encode()).hexdigest()[:16],16)
        random.Random(seed).shuffle(rows)
    return rows

def _stable_options(q, session_id, randomize_answers='Yes'):
    opts=[q.get('option_a'),q.get('option_b'),q.get('option_c'),q.get('option_d')]
    if str(randomize_answers)=='Yes':
        seed=int(hashlib.sha256(f"{session_id}:{q.get('question_id')}:answers".encode()).hexdigest()[:16],16)
        random.Random(seed).shuffle(opts)
    return opts

def _mark_training_item_complete(user_id, training_id, item_type, item_id):
    if not table_exists('training_resource_progress'):
        return
    existing=db_where('training_resource_progress','user_id = :uid AND training_id = :tid AND item_type = :it AND item_id = :iid',(('uid',user_id),('tid',training_id),('it',item_type),('iid',item_id)))
    patch={'status':'Completed','completed_on':now(),'updated_on':now()}
    if existing.empty:
        db_insert('training_resource_progress',{'resource_progress_id':uid('TRP'),'user_id':user_id,'training_id':training_id,'item_type':item_type,'item_id':item_id,**patch})
    else:
        db_update('training_resource_progress','resource_progress_id',str(existing.iloc[-1].get('resource_progress_id')),patch)

def trainee_training(actor, tid):
    """Read-only trainee view.
    Trainees can see assigned training schedule and materials, but cannot edit course data.
    Opening/confirming material updates only their own training record.
    """
    uidv = actor_get(actor, 'user_id')
    rr = db_where('training_records', 'user_id = :user_id and training_id = :training_id', (('user_id', uidv), ('training_id', tid)))
    if rr.empty:
        st.warning('Training not assigned.')
        return
    tr = db_where('trainings', 'training_id = :training_id', (('training_id', tid),))
    if tr.empty:
        st.warning('Training details not found.')
        return
    row = rr.iloc[0]
    tr_row = tr.iloc[0]
    record_id = row['record_id']
    is_absent = clean(row.get('live_attendance')) == 'Absent'
    st.subheader(clean(tr_row['title']))
    metrics([('Progress', f"{row['progress']}%"), ('Attendance', clean(row.get('live_attendance', 'Not Marked'))), ('LMS', row['lms_completed']), ('Test', row['test_status'])])
    st.info(f"Schedule: {clean(tr_row.get('schedule_date')) or 'Not scheduled'} at {clean(tr_row.get('schedule_time')) or 'Not specified'} | Trainer: {clean(tr_row.get('trainer_name')) or 'Not assigned'} | Due: {clean(row.get('due_date'))}")
    st.markdown('### Live Session')
    meeting_link = clean(tr_row.get('meeting_link'))
    if meeting_link:
        st.link_button('Join / Open Meeting Link', meeting_link)
    else:
        st.caption('Meeting link is not available yet.')
    st.markdown('### Training Material (Read Only)')
    c1, c2, c3, c4 = st.columns(4)
    slides_link = clean(tr_row.get('slides_link'))
    video_link = clean(tr_row.get('video_link'))
    reference_link = clean(tr_row.get('reference_link'))
    scorm_link = clean(tr_row.get('scorm_package_link'))
    if slides_link:
        c1.link_button('Open Slides', slides_link)
        if c1.button('Confirm Slides Completed', key=f'slides_done_{record_id}'):
            db_update('training_records', 'record_id', record_id, {'slides_opened': 'Yes', 'updated_on': now()})
            update_training_progress(record_id)
            st.rerun()
    else:
        c1.caption('Slides not uploaded.')
    if video_link:
        c2.link_button('Open Video', video_link)
        if c2.button('Confirm Video Completed', key=f'video_done_{record_id}'):
            db_update('training_records', 'record_id', record_id, {'video_opened': 'Yes', 'updated_on': now()})
            update_training_progress(record_id)
            st.rerun()
    else:
        c2.caption('Video not uploaded.')
    if reference_link:
        c3.link_button('Open Reference', reference_link)
    else:
        c3.caption('Reference link not uploaded.')
    if scorm_link:
        c4.link_button('Open LMS/SCORM', scorm_link)
        if c4.button('Confirm LMS Completed', key=f'lms_done_{record_id}'):
            db_update('training_records', 'record_id', record_id, {'lms_completed': 'Yes', 'updated_on': now()})
            update_training_progress(record_id)
            st.rerun()
    else:
        c4.caption('LMS/SCORM link not uploaded.')
    linked_files = db_where('files', 'linked_table = :linked_table and linked_id = :linked_id', (('linked_table', 'trainings'), ('linked_id', tid)))
    if not linked_files.empty:
        st.markdown('#### Uploaded Documents / Files')
        for _, f in linked_files.iterrows():
            file_url = secure_file_url(f.to_dict())
            file_bytes = secure_file_bytes(f.to_dict()) if not file_url else None
            file_name = clean(f.get('file_name'))
            file_id = clean(f.get('file_id')) or file_name
            c1,c2=st.columns([4,1])
            if file_url:
                c1.link_button(f'Open {file_name}', file_url, key=f'file_open_{record_id}_{file_id}')
            elif file_bytes is not None:
                c1.download_button(f'Download {file_name}', data=file_bytes, file_name=file_name, key=f'file_open_{record_id}_{file_id}')
            else:
                c1.caption(file_name + ' (secure file unavailable)')
            prog=db_where('training_resource_progress','user_id = :uid AND training_id = :tid AND item_type = :it AND item_id = :iid',(('uid',uidv),('tid',tid),('it','File'),('iid',file_id))) if table_exists('training_resource_progress') else pd.DataFrame()
            if not prog.empty: c2.success('Completed')
            elif c2.button('Mark read',key=f'file_done_{record_id}_{file_id}'):
                _mark_training_item_complete(uidv,tid,'File',file_id); st.rerun()
    resources = db_where('training_resources','training_id = :tid AND active = :active',(('tid',tid),('active','Yes'))) if table_exists('training_resources') else pd.DataFrame()
    if not resources.empty:
        st.markdown('#### Videos, Rules & References')
        for _, r in resources.iterrows():
            rid=clean(r.get('resource_id')); title=f"{clean(r.get('resource_type'))}: {clean(r.get('title'))}"; url=clean(r.get('url'))
            c1,c2=st.columns([4,1])
            if url: c1.link_button(title,url,key=f'resource_open_{record_id}_{rid}')
            else: c1.write(title)
            if clean(r.get('rule_reference')): c1.caption(clean(r.get('rule_reference')))
            prog=db_where('training_resource_progress','user_id = :uid AND training_id = :tid AND item_type = :it AND item_id = :iid',(('uid',uidv),('tid',tid),('it','Resource'),('iid',rid))) if table_exists('training_resource_progress') else pd.DataFrame()
            if not prog.empty: c2.success('Completed')
            elif c2.button('Mark reviewed',key=f'resource_done_{record_id}_{rid}'):
                _mark_training_item_complete(uidv,tid,'Resource',rid); st.rerun()
    live_sessions=db_where('training_live_sessions','training_id = :tid',(('tid',tid),)) if table_exists('training_live_sessions') else pd.DataFrame()
    if not live_sessions.empty:
        st.markdown('#### Live Session Attendance')
        for _,ss in live_sessions.iterrows():
            sid=clean(ss.get('session_id')); attendance=db_where('training_session_attendance','session_id = :sid AND user_id = :uid',(('sid',sid),('uid',uidv))) if table_exists('training_session_attendance') else pd.DataFrame()
            status=clean(attendance.iloc[-1].get('attendance_status')) if not attendance.empty else 'Not Marked'
            st.write(f"**{clean(ss.get('session_title'))}** · {clean(ss.get('session_date'))} {clean(ss.get('start_time'))} · Attendance: **{status}**")
    st.markdown('### Recording for Absent / Revision')
    recording_link = clean(tr_row.get('recording_link'))
    if recording_link:
        st.link_button('Open Recording', recording_link)
        if st.button('Confirm Recording Viewed', key=f'recording_done_{record_id}'):
            patch = {'recording_opened': 'Yes', 'video_opened': 'Yes', 'updated_on': now()}
            if is_absent or clean(row.get('live_attendance')) in ['Not Marked', '']:
                patch['live_attendance'] = 'Recording Viewed'
            db_update('training_records', 'record_id', record_id, patch)
            update_training_progress(record_id)
            st.rerun()
    elif is_absent:
        st.warning('You were marked absent. Recording will appear here after the trainer uploads/pastes the recording link.')
    else:
        st.caption('Recording link is not available yet.')
    st.markdown('### Timed MCQ Assessment')
    qs = db_where('question_bank', 'training_id = :training_id', (('training_id', tid),))
    if qs.empty:
        st.warning('MCQs not generated yet by the Trainer.')
        return
    if row['test_status'] == 'Passed':
        st.success(f"Assessment passed. Score: {row.get('score', 0)}%")
        return
    history = db_where('assessment_history', 'user_id = :user_id and training_id = :training_id', (('user_id', uidv), ('training_id', tid)))
    attempts = len(history) if not history.empty else 0
    cfg = db_where('training_assessment_configs','training_id = :tid AND active = :active',(('tid',tid),('active','Yes'))) if table_exists('training_assessment_configs') else pd.DataFrame()
    conf = cfg.iloc[-1].to_dict() if not cfg.empty else {'duration_minutes':30,'passing_score':int(tr_row.get('passing_marks') or 70),'max_attempts':int(tr_row.get('max_attempts') or 2),'show_result_immediately':'Yes'}
    duration_minutes=int(conf.get('duration_minutes') or 30); max_attempts=int(conf.get('max_attempts') or 2); pass_mark=int(conf.get('passing_score') or tr_row.get('passing_marks') or 70)
    if attempts >= max_attempts:
        st.error('Maximum assessment attempts have been used. Contact your Trainer for a controlled reassessment decision.')
        return
    window_ok, window_message = _assessment_window_open(conf)
    sessions=db_where('training_assessment_sessions','user_id = :uid AND training_id = :tid AND status = :status',(('uid',uidv),('tid',tid),('status','In Progress'))) if table_exists('training_assessment_sessions') else pd.DataFrame()
    if sessions.empty and not window_ok:
        st.info(window_message)
        return
    session=sessions.iloc[-1].to_dict() if not sessions.empty else {}
    if not session:
        st.info(f"Questions: {len(qs)} · Duration: {duration_minutes} minutes · Passing score: {pass_mark}% · Attempts remaining: {max_attempts-attempts}")
        st.caption('The timer is controlled by the server. Once started, the expiry time cannot be paused or reset by refreshing the browser.')
        if st.button('Start Timed Assessment',key=f'start_timed_{tid}_{uidv}',type='primary'):
            started=datetime.now(); expires=started+timedelta(minutes=duration_minutes); sid=uid('TAS')
            db_insert('training_assessment_sessions',{'assessment_session_id':sid,'user_id':uidv,'training_id':tid,'attempt_no':attempts+1,'started_at':started.strftime('%Y-%m-%d %H:%M:%S'),'expires_at':expires.strftime('%Y-%m-%d %H:%M:%S'),'submitted_at':'','status':'In Progress','score':0,'result':'','correct_count':0,'question_count':len(qs),'created_on':now(),'updated_on':now()})
            audit('Timed Training Assessment Started',tr_row.get('title',''),actor=actor,entity_type='training_assessment_sessions',entity_id=sid,reason=f'{duration_minutes} minute server-timed assessment')
            st.rerun()
        return
    expires=datetime.strptime(str(session.get('expires_at')),'%Y-%m-%d %H:%M:%S'); remaining=max(0,int((expires-datetime.now()).total_seconds()))
    if remaining<=0:
        db_update('training_assessment_sessions','assessment_session_id',session['assessment_session_id'],{'submitted_at':now(),'status':'Submitted','score':0,'result':'Failed','correct_count':0,'question_count':len(qs),'updated_on':now()})
        db_insert('assessment_history', {'assessment_id': uid('ASM'), 'user_id': uidv, 'name': actor_get(actor, 'name'), 'training_id': tid, 'training_title': tr_row['title'], 'attempt_no':int(session.get('attempt_no') or attempts+1), 'score':0, 'result':'Failed', 'attempted_on':now(), 'next_retest_allowed':'', 'remarks':'Assessment auto-submitted because the server-side timer expired.'})
        db_update('training_records','record_id',record_id,{'score':0,'test_status':'Failed','remarks':'Timed assessment expired before submission','updated_on':now()})
        audit('Timed Training Assessment Expired',tr_row.get('title',''),actor=actor,entity_type='training_assessment_sessions',entity_id=session['assessment_session_id'],reason='Server-side assessment timer expired')
        st.error('Time expired. The assessment was automatically submitted and recorded as failed.'); st.rerun()
    mins,secs=divmod(remaining,60)
    st.warning(f'⏱ Time Remaining: {mins:02d}:{secs:02d}')
    st.caption(f"Attempt {session.get('attempt_no')} of {max_attempts}. Server expiry: {session.get('expires_at')}")
    question_rows=_stable_question_rows(qs,str(session.get('assessment_session_id')),conf.get('randomize_questions','Yes'))
    with st.form(f'assessment_{tid}_{uidv}_{session.get("assessment_session_id")}'):
        answers = {}
        for i, q in enumerate(question_rows, 1):
            st.markdown(f"**Q{i}. {q['question']}**")
            opts = _stable_options(q,str(session.get('assessment_session_id')),conf.get('randomize_answers','Yes'))
            answers[q['question_id']] = st.radio('Select', opts, key=f"{session.get('assessment_session_id')}_{q['question_id']}", label_visibility='collapsed')
        submit = st.form_submit_button('Submit Assessment')
    if submit:
        # Re-check server time on submit; browser-side timing is never authoritative.
        if datetime.now() > expires:
            db_update('training_assessment_sessions','assessment_session_id',session['assessment_session_id'],{'submitted_at':now(),'status':'Submitted','score':0,'result':'Failed','updated_on':now()}); st.error('The timer expired before the submission reached the server.'); st.rerun()
        correct = sum(1 for q in question_rows if answers.get(q['question_id']) == q['correct_answer'])
        score = round(correct / len(question_rows) * 100, 2); result = 'Passed' if score >= pass_mark else 'Failed'
        db_update('training_assessment_sessions','assessment_session_id',session['assessment_session_id'],{'submitted_at':now(),'status':'Submitted','score':score,'result':result,'correct_count':correct,'question_count':len(qs),'updated_on':now()})
        db_insert('assessment_history', {'assessment_id': uid('ASM'), 'user_id': uidv, 'name': actor_get(actor, 'name'), 'training_id': tid, 'training_title': tr_row['title'], 'attempt_no':int(session.get('attempt_no') or attempts+1), 'score':score, 'result':result, 'attempted_on':now(), 'next_retest_allowed':'', 'remarks': f'Correct {correct}/{len(question_rows)} · server-timed · randomized according to assessment rules'})
        db_update('training_records', 'record_id', record_id, {'score': score, 'test_status': result, 'certificate_status': 'Issued' if result == 'Passed' else 'Not Issued', 'certificate_link': f'{PUBLIC_URL}/training-certificates/{uidv}/{tid}' if result == 'Passed' else '', 'remarks': f'Correct {correct}/{len(question_rows)}', 'updated_on': now()})
        update_training_progress(record_id)
        audit('Timed Training Assessment Submitted',tr_row.get('title',''),actor=actor,entity_type='training_assessment_sessions',entity_id=session['assessment_session_id'],reason=f'{result} {score}%')
        if str(conf.get('show_result_immediately','Yes'))=='Yes': st.success(f'{result}: {score}%') if result=='Passed' else st.error(f'{result}: {score}%')
        else: st.info('Assessment submitted. The result is recorded according to the course result-release rule.')
        st.rerun()

def cpd_page(actor):
    """Professional CPD lifecycle. CPD is evidence of continuing development;
    it feeds Development Plans, Annual Review and Revalidation but does not
    duplicate Training or Competency records."""
    st.header('CPD & Continuing Professional Development')
    st.caption('Record, verify and evidence continuing development. Training remains the authoritative source for courses; CPD captures broader professional-development activity.')
    users = db_all('users')
    cpd = db_all('cpd_records')
    role = actor_get(actor, 'role')
    can_manage = can_action(actor, 'CPD', 'Manage', 'Organization-wide') or can_action(actor, 'CPD', 'Edit', 'Assigned')
    can_verify = can_action(actor, 'CPD', 'Review', 'Assigned') or can_action(actor, 'CPD', 'Review', 'Organization-wide')
    for col, default in [('activity_date', ''), ('description', ''), ('learning_outcome', ''), ('evidence_status', 'Missing'), ('verified_by', ''), ('verified_on', ''), ('verification_notes', ''), ('development_plan_id', ''), ('source_type', 'Self-recorded'), ('status', 'Completed')]:
        if col not in cpd.columns:
            cpd[col] = default
    valid = cpd.copy()
    if not can_manage:
        valid = valid[valid['user_id'].astype(str) == actor_get(actor, 'user_id')] if not valid.empty else valid
    completed_hours = float(pd.to_numeric(valid.get('hours', pd.Series(dtype=float)), errors='coerce').fillna(0).sum()) if not valid.empty else 0.0
    verified_hours = float(pd.to_numeric(valid.loc[valid['evidence_status'].astype(str).eq('Verified'), 'hours'], errors='coerce').fillna(0).sum()) if not valid.empty else 0.0
    pending = int(valid['evidence_status'].astype(str).eq('Submitted').sum()) if not valid.empty else 0
    missing = int(valid['evidence_status'].astype(str).isin(['Missing', 'Required']).sum()) if not valid.empty else 0
    metrics([('CPD Records', len(valid)), ('Total Hours', round(completed_hours, 1)), ('Verified Hours', round(verified_hours, 1)), ('Evidence Pending', pending + missing)])
    tabs = st.tabs(['CPD Register', 'Add CPD', 'Verification'] if can_verify else ['CPD Register', 'Add CPD'])
    with tabs[0]:
        f1, f2, f3, f4 = st.columns(4)
        search = f1.text_input('Search', placeholder='Title, provider, employee…')
        cat = f2.selectbox('Category', ['All'] + sorted([str(x) for x in valid['category'].dropna().unique()])) if not valid.empty else 'All'
        status = f3.selectbox('Evidence', ['All', 'Missing', 'Submitted', 'Verified', 'Rejected'])
        src = f4.selectbox('Source', ['All', 'Self-recorded', 'Training', 'Seminar', 'Conference', 'Technical Update', 'Other'])
        view = valid.copy()
        if search:
            mask = view.astype(str).apply(lambda c: c.str.contains(search, case=False, na=False)).any(axis=1)
            view = view[mask]
        if cat != 'All':
            view = view[view['category'].astype(str) == cat]
        if status != 'All':
            view = view[view['evidence_status'].astype(str) == status]
        if src != 'All':
            view = view[view['source_type'].astype(str).eq(src)]
        cols = [c for c in ['cpd_id', 'name', 'title', 'category', 'hours', 'completion_date', 'provider', 'source_type', 'evidence_status', 'verified_by', 'status'] if c in view.columns]
        table(view[cols] if cols else view)
        if not view.empty and can_manage:
            selected = st.selectbox('Open CPD record', view['cpd_id'].astype(str).tolist(), key='cpd_open')
            row = first_row(view[view['cpd_id'].astype(str) == str(selected)])
            if row:
                with st.expander('Update CPD record', expanded=False):
                    with st.form(f'edit_cpd_{selected}'):
                        title = st.text_input('Title', row.get('title', ''))
                        category = st.selectbox('Category', ['Seminar', 'Workshop', 'Webinar', 'Technical Update', 'Refresher Training', 'Conference', 'Technical Reading', 'Rule Review', 'On-the-Job Learning', 'Other'], index=max(0, ['Seminar', 'Workshop', 'Webinar', 'Technical Update', 'Refresher Training', 'Conference', 'Technical Reading', 'Rule Review', 'On-the-Job Learning', 'Other'].index(str(row.get('category', 'Other'))) if str(row.get('category', 'Other')) in ['Seminar', 'Workshop', 'Webinar', 'Technical Update', 'Refresher Training', 'Conference', 'Technical Reading', 'Rule Review', 'On-the-Job Learning', 'Other'] else 9))
                        hours = st.number_input('Hours', 0.0, 500.0, float(row.get('hours') or 0))
                        provider = st.text_input('Provider', row.get('provider', ''))
                        desc = st.text_area('Activity Description', row.get('description', ''))
                        outcome = st.text_area('Learning / Development Outcome', row.get('learning_outcome', ''))
                        evidence_status = st.selectbox('Evidence Status', ['Missing', 'Submitted', 'Verified', 'Rejected'], index=['Missing', 'Submitted', 'Verified', 'Rejected'].index(str(row.get('evidence_status', 'Missing'))) if str(row.get('evidence_status', 'Missing')) in ['Missing', 'Submitted', 'Verified', 'Rejected'] else 0)
                        reason = st.text_area('Reason for update')
                        save = st.form_submit_button('Save CPD Update')
                    if save:
                        db_update('cpd_records', 'cpd_id', selected, {'title': title, 'category': category, 'hours': hours, 'provider': provider, 'description': desc, 'learning_outcome': outcome, 'evidence_status': evidence_status})
                        audit('CPD Updated', f'CPD {selected} updated', actor=actor, entity_type='cpd_records', entity_id=selected, reason=reason, before_value=str(row), after_value=str({'title': title, 'category': category, 'hours': hours, 'provider': provider, 'evidence_status': evidence_status}))
                        st.success('CPD record updated.')
                        st.rerun()
    with tabs[1]:
        with st.form('cpd_add'):
            if can_manage:
                person = st.selectbox('Employee', users['name'].astype(str) + ' — ' + users['user_id'].astype(str)) if not users.empty else ''
            else:
                person = f"{actor_get(actor, 'name')} — {actor_get(actor, 'user_id')}"
                st.text_input('Employee', actor_get(actor, 'name'), disabled=True)
            title = st.text_input('CPD Activity / Event Title')
            category = st.selectbox('Category', ['Seminar', 'Workshop', 'Webinar', 'Technical Update', 'Refresher Training', 'Conference', 'Technical Reading', 'Rule Review', 'On-the-Job Learning', 'Other'])
            source = st.selectbox('Source', ['Self-recorded', 'Training', 'Seminar', 'Conference', 'Technical Update', 'Other'])
            hours = st.number_input('CPD Hours', 0.0, 500.0, 2.0, step=0.5)
            provider = st.text_input('Provider / Organizer')
            completion = st.date_input('Activity Date')
            description = st.text_area('Activity Description')
            outcome = st.text_area('Learning / Development Outcome')
            plan_id = st.text_input('Linked Development Plan ID (optional)')
            evidence_note = st.text_input('Evidence Reference / Description')
            submit = st.form_submit_button('Add CPD Record')
        if submit and person and title:
            name, uidv = person.split(' — ')
            cpd_id = uid('CPD')
            row = {'cpd_id': cpd_id, 'user_id': uidv, 'name': name, 'title': title, 'category': category, 'hours': hours, 'provider': provider, 'completion_date': str(completion), 'activity_date': str(completion), 'description': description, 'learning_outcome': outcome, 'evidence_file_id': '', 'evidence_status': 'Submitted' if evidence_note else 'Missing', 'verified_by': '', 'verified_on': '', 'verification_notes': evidence_note, 'development_plan_id': plan_id, 'source_type': source, 'status': 'Completed', 'created_on': now()}
            db_insert('cpd_records', row)
            audit('CPD Created', f'CPD {cpd_id} created for {name}', actor=actor, entity_type='cpd_records', entity_id=cpd_id, after_value=str(row))
            st.success('CPD record created.')
            st.rerun()
        st.info('Attach evidence from the selected CPD record in the Evidence/Verification workflow. CPD does not replace Training records or Competency evidence.')
    if can_verify:
        with tabs[2]:
            pending_df = valid[valid['evidence_status'].astype(str).isin(['Submitted', 'Missing'])].copy()
            if pending_df.empty:
                st.success('No CPD evidence currently requires verification.')
            else:
                selected = st.selectbox('CPD Record', pending_df['cpd_id'].astype(str).tolist(), key='cpd_verify')
                row = first_row(pending_df[pending_df['cpd_id'].astype(str) == str(selected)])
                if row:
                    st.write(f"**{row.get('name', '')} — {row.get('title', '')}**")
                    st.write(f"Hours: **{row.get('hours', 0)}** | Provider: **{row.get('provider', '—')}** | Evidence: **{row.get('evidence_status', 'Missing')}**")
                    st.caption('Verification confirms the evidence and CPD claim; it does not create a new training or competency record.')
                    with st.form(f'verify_cpd_{selected}'):
                        decision = st.selectbox('Verification Decision', ['Verified', 'Rejected'])
                        notes = st.text_area('Verification Notes')
                        submit = st.form_submit_button('Record Verification')
                    if submit:
                        db_update('cpd_records', 'cpd_id', selected, {'evidence_status': decision, 'verified_by': actor_get(actor, 'name'), 'verified_on': now(), 'verification_notes': notes})
                        audit('CPD Verification', f'CPD {selected} marked {decision}', actor=actor, entity_type='cpd_records', entity_id=selected, reason=notes, after_value=decision)
                        st.success(f'CPD marked {decision}.')
                        st.rerun()

def knowledge_page(actor):
    """State-of-the-art technical knowledge and controlled publication library.

    Knowledge Library is a governed reference service. It owns knowledge items,
    versions, publication state and acknowledgements; it does not duplicate
    Training, QMS NCR, Rule Development or document workflows.
    """
    st.header('Knowledge Library')
    st.caption('Controlled technical reference library. Training, QMS and Rule Development remain authoritative for their own workflows.')
    role = actor_get(actor, 'role', '')
    can_manage = can_action(actor, 'Knowledge Library', 'Create', 'Department') or can_action(actor, 'Knowledge Library', 'Manage', 'Organization-wide')
    can_approve = can_action(actor, 'Knowledge Library', 'Approve', 'Organization-wide') or can_action(actor, 'Knowledge Library', 'Review', 'Department')
    lib = db_all('knowledge_library')
    if lib.empty:
        lib = pd.DataFrame(columns=['knowledge_id', 'title', 'category', 'summary', 'standard', 'revision', 'issue_date', 'effective_from', 'review_due_date', 'status', 'audience', 'mandatory_ack', 'uploaded_by', 'owner_name', 'approved_by', 'approved_on', 'supersedes_id', 'keywords', 'created_on', 'updated_on'])
    status_s = lib.get('status', pd.Series(dtype=str)).astype(str) if not lib.empty else pd.Series(dtype=str)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Published', int((status_s == 'Published').sum()))
    m2.metric('Draft / Review', int(status_s.isin(['Draft', 'Under Review']).sum()))
    m3.metric('Mandatory', int((lib.get('mandatory_ack', pd.Series(dtype=str)).astype(str) == 'Yes').sum()) if not lib.empty else 0)
    m4.metric('Acknowledgements', len(db_all('knowledge_acknowledgements')))
    tabs = st.tabs(['Library', 'Create / Edit', 'Versions', 'Acknowledgements'])
    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        search = c1.text_input('Search', placeholder='Title, keyword, standard, revision...')
        cats = sorted([x for x in lib.get('category', pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x]) if not lib.empty else []
        cat = c2.selectbox('Category', ['All'] + cats)
        sts = sorted([x for x in lib.get('status', pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x]) if not lib.empty else []
        stf = c3.selectbox('Status', ['All'] + sts)
        auds = sorted([x for x in lib.get('audience', pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x]) if not lib.empty else []
        aud = c4.selectbox('Audience', ['All'] + auds)
        view = lib.copy()
        if not view.empty:
            if search:
                mask = pd.Series(False, index=view.index)
                for col in ['title', 'summary', 'standard', 'revision', 'keywords', 'category']:
                    if col in view.columns:
                        mask = mask | view[col].astype(str).str.contains(search, case=False, na=False)
                view = view[mask]
            if cat != 'All' and 'category' in view.columns:
                view = view[view['category'].astype(str) == cat]
            if stf != 'All' and 'status' in view.columns:
                view = view[view['status'].astype(str) == stf]
            if aud != 'All' and 'audience' in view.columns:
                view = view[view['audience'].astype(str) == aud]
            cols = [c for c in ['knowledge_id', 'title', 'category', 'revision', 'status', 'audience', 'mandatory_ack', 'effective_from', 'review_due_date'] if c in view.columns]
            table(view[cols].sort_values('title') if cols else view)
            selected = st.selectbox('Open Knowledge Item', [f'{r.title} — {r.knowledge_id}' for r in view.itertuples()] or ['No items'])
            if selected != 'No items':
                kid = selected.split(' — ')[-1]
                item_df = view[view['knowledge_id'].astype(str) == kid]
                item = first_row(item_df)
                if item:
                    st.markdown(f"### {item.get('title', 'Untitled')}")
                    st.caption(f"Status: {item.get('status', '')} • Revision: {item.get('revision', '')} • Category: {item.get('category', '')}")
                    a, b, c = st.columns(3)
                    a.metric('Mandatory', 'Yes' if str(item.get('mandatory_ack', 'No')) == 'Yes' else 'No')
                    b.metric('Effective', str(item.get('effective_from', '—')))
                    c.metric('Review Due', str(item.get('review_due_date', '—')))
                    if item.get('summary'):
                        st.write(item.get('summary'))
                    info = {k: item.get(k, '') for k in ['standard', 'keywords', 'audience', 'owner_name', 'approved_by', 'approved_on', 'supersedes_id']}
                    st.json(info)
                    file_upload_panel(actor, 'knowledge_library', kid, 'Knowledge Bulletin')
                    ack = db_all('knowledge_acknowledgements')
                    already = False
                    if not ack.empty and 'knowledge_id' in ack.columns and ('user_id' in ack.columns):
                        already = not ack[(ack['knowledge_id'].astype(str) == kid) & (ack['user_id'].astype(str) == str(actor_get(actor, 'user_id')))].empty
                    if str(item.get('mandatory_ack', 'No')) == 'Yes' and item.get('status') == 'Published' and (not already):
                        if st.button('Acknowledge Published Item', key=f'ack_{kid}'):
                            db_insert('knowledge_acknowledgements', {'ack_id': uid('ACK'), 'knowledge_id': kid, 'user_id': actor_get(actor, 'user_id'), 'name': actor_get(actor, 'name'), 'acknowledged_on': now(), 'status': 'Acknowledged'})
                            audit('Knowledge Acknowledged', f'Knowledge {kid} acknowledged', actor=actor, entity_type='knowledge_library', entity_id=kid)
                            st.success('Acknowledgement recorded.')
                            st.rerun()
                    elif already:
                        st.success('You have already acknowledged this item.')
    with tabs[1]:
        if not can_manage:
            st.info('Knowledge creation and governance are restricted to authorized technical/training/QMS roles.')
        else:
            with st.form('knowledge_create_edit'):
                existing = ['New Item'] + ([f'{r.title} — {r.knowledge_id}' for r in lib.itertuples()] if not lib.empty else [])
                pick = st.selectbox('Knowledge Item', existing)
                if pick != 'New Item':
                    ekid = pick.split(' — ')[-1]
                    rec = first_row(lib[lib['knowledge_id'].astype(str) == ekid]) or {}
                else:
                    ekid, rec = ('', {})
                title = st.text_input('Title', rec.get('title', ''))
                c1, c2 = st.columns(2)
                category = c1.selectbox('Category', ['Rule', 'Circular', 'Technical Bulletin', 'IMO Update', 'IACS Update', 'Interpretation', 'Lesson Learned', 'Guidance', 'Procedure'], index=0 if not rec.get('category') else max(0, ['Rule', 'Circular', 'Technical Bulletin', 'IMO Update', 'IACS Update', 'Interpretation', 'Lesson Learned', 'Guidance', 'Procedure'].index(str(rec.get('category'))) if str(rec.get('category')) in ['Rule', 'Circular', 'Technical Bulletin', 'IMO Update', 'IACS Update', 'Interpretation', 'Lesson Learned', 'Guidance', 'Procedure'] else 0))
                status = c2.selectbox('Status', ['Draft', 'Under Review', 'Published', 'Superseded', 'Archived'], index=['Draft', 'Under Review', 'Published', 'Superseded', 'Archived'].index(str(rec.get('status'))) if str(rec.get('status')) in ['Draft', 'Under Review', 'Published', 'Superseded', 'Archived'] else 0)
                summary = st.text_area('Summary / Abstract', rec.get('summary', ''))
                c1, c2, c3 = st.columns(3)
                standard = c1.text_input('Standard / Reference', rec.get('standard', ''))
                revision = c2.text_input('Revision', rec.get('revision', ''))
                audience = c3.text_input('Audience', rec.get('audience', 'All technical staff'))
                c1, c2, c3 = st.columns(3)
                effective_from = c1.date_input('Effective From', value=pd.to_datetime(rec.get('effective_from')).date() if rec.get('effective_from') else date.today())
                review_due = c2.date_input('Review Due', value=pd.to_datetime(rec.get('review_due_date')).date() if rec.get('review_due_date') else date.today() + timedelta(days=365))
                mandatory = c3.checkbox('Mandatory Acknowledgement', str(rec.get('mandatory_ack', 'Yes')) == 'Yes')
                keywords = st.text_input('Keywords (comma separated)', rec.get('keywords', ''))
                supersedes = st.text_input('Supersedes Knowledge ID (optional)', rec.get('supersedes_id', ''))
                notes = st.text_area('Governance Notes', '')
                save = st.form_submit_button('Save Knowledge Item', use_container_width=True)
            if save and title.strip():
                kid = ekid or uid('KNOW')
                payload = {'knowledge_id': kid, 'title': title.strip(), 'category': category, 'summary': summary, 'standard': standard, 'revision': revision, 'issue_date': rec.get('issue_date', today()), 'effective_from': str(effective_from), 'review_due_date': str(review_due), 'status': status, 'audience': audience, 'mandatory_ack': 'Yes' if mandatory else 'No', 'uploaded_by': rec.get('uploaded_by', actor_get(actor, 'name')), 'owner_name': rec.get('owner_name', actor_get(actor, 'name')), 'approved_by': rec.get('approved_by', ''), 'approved_on': rec.get('approved_on', ''), 'supersedes_id': supersedes, 'keywords': keywords, 'created_on': rec.get('created_on', now()), 'updated_on': now()}
                if ekid:
                    previous_revision = str(rec.get('revision', ''))
                    db_update('knowledge_library', 'knowledge_id', kid, payload)
                    db_insert('knowledge_versions', {'version_id': uid('KVER'), 'knowledge_id': kid, 'version_no': revision or previous_revision or '1', 'revision_date': str(effective_from), 'change_summary': notes or 'Knowledge item updated', 'file_link': rec.get('file_id', ''), 'uploaded_by': actor_get(actor, 'name'), 'approved_by': actor_get(actor, 'name') if status == 'Published' else '', 'status': status, 'created_on': now()})
                    audit('Knowledge Updated', f'Knowledge {kid} updated', actor=actor, entity_type='knowledge_library', entity_id=kid, reason=notes)
                else:
                    db_insert('knowledge_library', payload)
                    db_insert('knowledge_versions', {'version_id': uid('KVER'), 'knowledge_id': kid, 'version_no': revision or '1', 'revision_date': str(effective_from), 'change_summary': 'Initial publication record', 'file_link': '', 'uploaded_by': actor_get(actor, 'name'), 'approved_by': actor_get(actor, 'name') if status == 'Published' else '', 'status': status, 'created_on': now()})
                    audit('Knowledge Created', f'Knowledge {kid} created', actor=actor, entity_type='knowledge_library', entity_id=kid, reason=notes)
                st.success('Knowledge item saved.')
                st.rerun()
            if not lib.empty and can_approve:
                st.subheader('Publication Control')
                published = lib[lib.get('status', pd.Series(dtype=str)).astype(str).isin(['Draft', 'Under Review'])] if 'status' in lib.columns else pd.DataFrame()
                if not published.empty:
                    item = st.selectbox('Item for publication review', [f'{r.title} — {r.knowledge_id}' for r in published.itertuples()])
                    kid = item.split(' — ')[-1]
                    c1, c2 = st.columns(2)
                    if c1.button('Approve & Publish', key=f'publish_{kid}', use_container_width=True):
                        db_update('knowledge_library', 'knowledge_id', kid, {'status': 'Published', 'approved_by': actor_get(actor, 'name'), 'approved_on': now(), 'updated_on': now()})
                        audit('Knowledge Published', f'Knowledge {kid} published', actor=actor, entity_type='knowledge_library', entity_id=kid, reason='Approved for controlled publication', after_value='Published')
                        st.success('Published.')
                        st.rerun()
                    if c2.button('Return to Draft', key=f'draft_{kid}', use_container_width=True):
                        db_update('knowledge_library', 'knowledge_id', kid, {'status': 'Draft', 'updated_on': now()})
                        audit('Knowledge Returned to Draft', f'Knowledge {kid} returned to draft', actor=actor, entity_type='knowledge_library', entity_id=kid, reason='Publication review not approved', after_value='Draft')
                        st.success('Returned to Draft.')
                        st.rerun()
    with tabs[2]:
        st.subheader('Knowledge Version History')
        versions = db_all('knowledge_versions')
        if versions.empty:
            st.info('No version history recorded yet. Future revision changes will be tracked here.')
        else:
            table(versions.sort_values('created_on', ascending=False) if 'created_on' in versions.columns else versions)
    with tabs[3]:
        acks = db_all('knowledge_acknowledgements')
        table(acks.sort_values('acknowledged_on', ascending=False) if not acks.empty and 'acknowledged_on' in acks.columns else acks)
