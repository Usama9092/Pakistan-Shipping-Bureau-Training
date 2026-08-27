from psb_app.common import (
    ADMIN_ACCOUNT_STATUSES,
    APP_TITLE,
    AUTH_MODE,
    AVAILABILITY_STATUSES,
    DEPARTMENTS,
    LOGIN_BLOCK_MINUTES,
    MAX_LOGIN_ATTEMPTS,
    PERMISSION_ACTIONS,
    PERMISSION_SCOPES,
    RATE_LIMITER,
    ROLES,
    SUPABASE_AUTH_PROVIDER,
    SUPABASE_BUCKET,
    SUPABASE_URL,
    TRAINEE_PATHS,
    actor_get,
    audit,
    database_is_persistent,
    date,
    datetime,
    db_all,
    db_insert,
    db_update,
    db_where,
    department_options,
    join_list,
    now,
    os,
    pd,
    phase2_health_snapshot,
    phash,
    random,
    re,
    scheduler_health_summary,
    split_list,
    st,
    storage_is_persistent,
    table,
    table_exists,
    temp_password,
    timedelta,
    today,
    uid,
    validate_email,
)
from core.security import password_errors as _password_errors
from psb_app.legacy_runtime import _effective_permission_rows, _permission_rows_for_role
from psb_app.services.admin_service import (
    _admin_only,
    _backup_export_tables,
    _build_backup_payload,
    _save_setting,
    _setting_bool,
    _setting_value,
)
from psb_app.services.ui_helpers import _parse_user_label, _user_label_series

def metrics(items):
    cols = st.columns(4)
    for index, (label, value) in enumerate(items):
        cols[index % 4].metric(label, value)

def users_roles_page(actor):
    """Professional identity/account administration.

    This page owns identity, organizational placement, assignments and account
    lifecycle. Competency, training and business approvals remain in their
    respective modules.
    """
    st.header('Users & Roles')
    if not _admin_only(actor):
        return
    users = db_all('users')
    active_count = len(users[users['account_status'].fillna(users.get('status', '')) == 'Active']) if not users.empty else 0
    suspended_count = len(users[users['account_status'].fillna(users.get('status', '')) == 'Suspended']) if not users.empty else 0
    dept_count = len(department_options())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Total Users', len(users))
    c2.metric('Active Accounts', active_count)
    c3.metric('Suspended', suspended_count)
    c4.metric('Departments', dept_count)
    with st.expander('Create User', expanded=False):
        with st.form('create_user_professional'):
            st.markdown('#### 1 · Identity')
            c1, c2 = st.columns(2)
            employee_id = c1.text_input('Employee ID *', help='Unique organizational employee identifier.')
            name = c2.text_input('Full Name *')
            email = c1.text_input('Email *')
            phone = c2.text_input('Phone')
            joining = c1.date_input('Date of Joining', value=date.today())
            st.markdown('#### 2 · Account')
            c1, c2 = st.columns(2)
            role = c1.selectbox('Role', ROLES)
            login = c2.text_input('Login ID', help='Leave blank to generate from the employee name.')
            password = c1.text_input('Temporary Password', type='password', help='Leave blank to generate one. It is displayed once and only its hash is stored.')
            account_status = c2.selectbox('Account Status', ADMIN_ACCOUNT_STATUSES, index=1)
            st.markdown('#### 3 · Organization')
            c1, c2 = st.columns(2)
            dept_options = department_options()
            primary_department = c1.selectbox('Primary Department', dept_options)
            additional_departments = c2.multiselect('Additional Departments', [d for d in dept_options if d != primary_department])
            c1.caption('User classification is determined by Role: On Probation, Trainee, technical staff (Surveyor / Industrial Surveyor / Plan Appraiser), Management/GM, or quality/rule/admin roles.')
            duty = c2.text_input('Assigned Duty / Scope')
            path = ''
            st.info('Qualification Path is assigned only by the responsible Trainer in Qualification Workspace. Role controls portal access. Authorized technical status is derived only from an approved authorization case and a valid Digital Certificate of Authorization—not from an Admin toggle.')
            st.markdown('#### 4 · Responsibilities')
            current_users = users[users['account_status'].fillna(users.get('status', '')) == 'Active'] if not users.empty else users
            options = [''] + (current_users['name'].astype(str) + ' — ' + current_users['user_id'].astype(str)).tolist() if not current_users.empty else ['']
            c1, c2 = st.columns(2)
            assigner = c1.selectbox('Assigner', options, help='Administrative assignment responsibility where applicable.')
            trainer = c2.selectbox('Trainer', options, help='Owns qualification-path training, mentoring and development support for the learner.')
            st.markdown('#### 5 · Professional Profile')
            c1, c2 = st.columns(2)
            location = c1.text_input('Current Location', 'Karachi')
            availability = c2.selectbox('Availability', AVAILABILITY_STATUSES)
            st.info('Role determines baseline access. User-specific overrides are exceptional, reasoned and audited on the Permissions page.')
            st.markdown('#### 6 · Review')
            st.caption('Competency level is controlled by the Competency workflow and is not manually assigned here.')
            submit = st.form_submit_button('Create User', type='primary', use_container_width=True)
        if submit:
            if not name or not email or (not employee_id):
                st.error('Employee ID, Full Name and Email are required.')
            elif not validate_email(email):
                st.error('Invalid email address.')
            else:
                try:
                    if not RATE_LIMITER.allowed('create_user', actor_get(actor, 'user_id') or 'anon', 5, 60):
                        st.error('Rate limit exceeded. Try again later.')
                        return
                except Exception:
                    pass
                duplicate = users[users.get('employee_id', pd.Series(dtype=str)).astype(str) == employee_id] if not users.empty and 'employee_id' in users.columns else pd.DataFrame()
                if not duplicate.empty:
                    st.error('Employee ID already exists.')
                else:
                    if password:
                        pwd_errors = _password_errors(password)
                        if pwd_errors:
                            st.error(' '.join(pwd_errors))
                            return
                    login_id = login.strip() or (re.sub('[^a-z0-9]', '', name.lower().replace(' ', '.')) or f'user{random.randint(100, 999)}')
                    existing_login = users[users['login_id'].astype(str).str.lower() == login_id.lower()] if not users.empty else pd.DataFrame()
                    if not existing_login.empty:
                        st.error('Login ID already exists.')
                    else:
                        temp = password or temp_password()
                        assigner_name, assigner_id = _parse_user_label(assigner)
                        trainer_name, trainer_id = _parse_user_label(trainer)
                        tutor_name, tutor_id = trainer_name, trainer_id
                        user_id = uid('USR')
                        if role == 'Department Manager' and primary_department not in ['Survey NSC','Survey Inservice','Plan Appraisal']:
                            st.error('Department Manager must be assigned to Survey NSC, Survey Inservice or Plan Appraisal.')
                            return
                        departments = [primary_department] + additional_departments
                        db_insert('users', {'user_id': user_id, 'auth_user_id': '', 'employee_id': employee_id, 'phone': phone, 'date_joined': str(joining), 'name': name, 'role': role, 'trainee_path': path, 'department': join_list(departments), 'primary_department': primary_department, 'assigned_duty': duty, 'email': email, 'login_id': login_id, 'password_hash': phash(temp), 'status': account_status, 'account_status': account_status, 'force_password_change': 'Yes', 'availability': availability, 'current_location': location, 'mentor_id': tutor_id, 'mentor_name': tutor_name, 'tutor_id': tutor_id, 'tutor_name': tutor_name, 'trainer_id': trainer_id, 'trainer_name': trainer_name, 'assigner_id': assigner_id, 'assigner_name': assigner_name, 'competency_level': 'Level 0 - Trainee', 'created_on': str(joining), 'created_by': actor_get(actor, 'user_id'), 'last_login': ''})
                        for dep in departments:
                            db_insert('user_departments', {'user_department_id': uid('UDEP'), 'user_id': user_id, 'department': dep, 'is_primary': 'Yes' if dep == primary_department else 'No', 'effective_from': today(), 'effective_to': '', 'status': 'Active', 'created_on': today()})
                        for assignment_type, assigned_id, assigned_name in [('Assigner', assigner_id, assigner_name), ('Trainer', trainer_id, trainer_name)]:
                            if assigned_id:
                                db_insert('user_assignments', {'assignment_id': uid('UASN'), 'user_id': user_id, 'assignment_type': assignment_type, 'assigned_user_id': assigned_id, 'assigned_user_name': assigned_name, 'effective_from': today(), 'effective_to': '', 'status': 'Active', 'created_by': actor_get(actor, 'user_id'), 'created_on': now()})
                        audit('User Created', f'{name} created with role={role}; primary={primary_department}; departments={join_list(departments)}; assigner={assigner_name}; trainer={trainer_name}', actor=actor, entity_type='User', entity_id=user_id, reason='New user account created')
                        st.success(f'User created. Login: {login_id}')
                        st.warning(f'Temporary password (display once): {temp}')
    st.divider()
    st.subheader('User Directory')
    if users.empty:
        st.info('No users found.')
        return
    c1, c2, c3, c4 = st.columns(4)
    search = c1.text_input('Search employee, name, email or login', key='admin_user_search')
    dep_filter = c2.selectbox('Department', ['All'] + department_options())
    role_filter = c3.selectbox('Role', ['All'] + ROLES)
    status_filter = c4.selectbox('Account Status', ['All'] + ADMIN_ACCOUNT_STATUSES)
    shown = users.copy()
    if search:
        mask = shown.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        shown = shown[mask]
    if dep_filter != 'All':
        shown = shown[shown['department'].astype(str).apply(lambda x: dep_filter in split_list(x))]
    if role_filter != 'All':
        shown = shown[shown['role'] == role_filter]
    if status_filter != 'All':
        col = 'account_status' if 'account_status' in shown.columns else 'status'
        shown = shown[shown[col].fillna(shown.get('status', '')).astype(str) == status_filter]
    cols = [c for c in ['employee_id', 'name', 'role', 'primary_department', 'department', 'account_status', 'availability', 'last_login'] if c in shown.columns]
    table(shown[cols], max_rows=500)
    labels = shown['name'].astype(str) + ' — ' + shown['user_id'].astype(str) if not shown.empty else pd.Series(dtype=str)
    if shown.empty:
        st.info('No users match the selected filters.')
        return
    selected = st.selectbox('Open User Profile', labels.tolist(), key='admin_selected_user')
    uidv = selected.split(' — ', 1)[-1]
    user = shown[shown['user_id'] == uidv].iloc[0]
    status_now = user.get('account_status') or user.get('status') or 'Active'
    st.markdown(f"### {user.get('name', '')}")
    st.caption(f"{user.get('employee_id', '')}  ·  {user.get('role', '')}  ·  {user.get('primary_department', '')}  ·  {status_now}")
    tabs = st.tabs(['Overview', 'Organization', 'Assignments', 'Access', 'Account & Security', 'History'])
    with tabs[0]:
        a, b, c, d = st.columns(4)
        a.metric('Role', user.get('role', '—'))
        b.metric('Primary Department', user.get('primary_department', '—'))
        c.metric('Competency', user.get('competency_level', '—'))
        d.metric('Availability', user.get('availability', '—'))
        st.markdown('#### Identity')
        table(pd.DataFrame([{'Employee ID': user.get('employee_id', ''), 'Name': user.get('name', ''), 'Email': user.get('email', ''), 'Phone': user.get('phone', ''), 'Joined': user.get('date_joined', ''), 'Login ID': user.get('login_id', ''), 'Location': user.get('current_location', ''), 'Duty / Scope': user.get('assigned_duty', '')}]))
    with tabs[1]:
        st.markdown('#### Organizational placement')
        existing_deps = split_list(user.get('department', '')) or ([user.get('primary_department')] if user.get('primary_department') else [])
        all_deps = department_options()
        current_primary = user.get('primary_department') if user.get('primary_department') in all_deps else existing_deps[0] if existing_deps else all_deps[0]
        with st.form(f'organization_{uidv}'):
            c1, c2 = st.columns(2)
            new_primary = c1.selectbox('Primary Department', all_deps, index=all_deps.index(current_primary) if current_primary in all_deps else 0)
            new_additional = c2.multiselect('Additional Departments', [d for d in all_deps if d != new_primary], default=[d for d in existing_deps if d != new_primary and d in all_deps])
            c1, c2 = st.columns(2)
            new_role = c1.selectbox('Role', ROLES, index=ROLES.index(user.get('role')) if user.get('role') in ROLES else 0)
            c2.text_input('Qualification Path (Trainer controlled)', value=user.get('trainee_path',''), disabled=True)
            new_path = user.get('trainee_path','')
            new_duty = st.text_input('Assigned Duty / Scope', value=user.get('assigned_duty', ''))
            reason = st.text_area('Reason for organizational change', help='Required for auditable changes to role, department or professional path.')
            save_org = st.form_submit_button('Save Organization & Role', type='primary')
        if save_org:
            if not reason.strip():
                st.error('Please provide a reason for the change.')
            else:
                new_departments = [new_primary] + [d for d in new_additional if d != new_primary]
                old = f"role={user.get('role', '')}; primary={user.get('primary_department', '')}; departments={user.get('department', '')}; path={user.get('trainee_path', '')}; duty={user.get('assigned_duty', '')}"
                db_update('users', 'user_id', uidv, {'role': new_role, 'trainee_path': new_path, 'assigned_duty': new_duty, 'primary_department': new_primary, 'department': join_list(new_departments)})
                old_rows = db_where('user_departments', 'user_id = :uid', (('uid', uidv),))
                for _, r in old_rows.iterrows() if not old_rows.empty else []:
                    db_update('user_departments', 'user_department_id', str(r.get('user_department_id')), {'is_primary': 'No', 'status': 'Historical', 'effective_to': today()}) if 'effective_to' in old_rows.columns else None
                for dep in new_departments:
                    db_insert('user_departments', {'user_department_id': uid('UDEP'), 'user_id': uidv, 'department': dep, 'is_primary': 'Yes' if dep == new_primary else 'No', 'created_on': today()})
                new = f'role={new_role}; primary={new_primary}; departments={join_list(new_departments)}; path={new_path}; duty={new_duty}'
                audit('User Organization Updated', f'{old} -> {new}', actor=actor, entity_type='User', entity_id=uidv, reason=reason, before_value=old, after_value=new)
                st.success('Organization and role updated.')
                st.rerun()
    with tabs[2]:
        assignments = db_where('user_assignments', 'user_id = :uid', (('uid', uidv),))
        st.markdown('#### Current responsibilities')
        current_assignments = assignments[assignments['status'].fillna('') == 'Active'] if not assignments.empty and 'status' in assignments.columns else assignments
        table(current_assignments[[c for c in ['assignment_type', 'assigned_user_name', 'effective_from', 'effective_to', 'status'] if c in current_assignments.columns]] if not current_assignments.empty else current_assignments)
        active = users[users['account_status'].fillna(users.get('status', '')) == 'Active'] if not users.empty else users
        active = active[active['user_id'] != uidv] if not active.empty else active
        opts = [''] + (active['name'].astype(str) + ' — ' + active['user_id'].astype(str)).tolist() if not active.empty else ['']

        def current_value(kind):
            if current_assignments is None or current_assignments.empty:
                return ''
            x = current_assignments[current_assignments['assignment_type'] == kind]
            return f"{x.iloc[0].get('assigned_user_name', '')} — {x.iloc[0].get('assigned_user_id', '')}" if not x.empty else ''
        with st.form(f'assignment_{uidv}'):
            c1, c2 = st.columns(2)
            a = c1.selectbox('Assigner', opts, index=opts.index(current_value('Assigner')) if current_value('Assigner') in opts else 0)
            t = c2.selectbox('Trainer', opts, index=opts.index(current_value('Trainer')) if current_value('Trainer') in opts else 0, help='The Trainer also owns mentoring and development support for the assigned learner.')
            effective_from = st.date_input('Effective From', value=date.today())
            reason = st.text_area('Reason for assignment change')
            update = st.form_submit_button('Save Responsibilities', type='primary')
        if update:
            if not reason.strip():
                st.error('Please provide a reason for the assignment change.')
            else:
                values = [('Assigner', *_parse_user_label(a)), ('Trainer', *_parse_user_label(t))]
                old = '; '.join([f'{typ}={current_value(typ)}' for typ, _, _ in values])
                for typ, ident, nm in values:
                    old_active = assignments[(assignments['assignment_type'] == typ) & (assignments['status'].fillna('') == 'Active')] if not assignments.empty and 'status' in assignments.columns else pd.DataFrame()
                    for _, r in old_active.iterrows():
                        db_update('user_assignments', 'assignment_id', str(r.get('assignment_id')), {'status': 'Historical', 'effective_to': str(effective_from)})
                    if ident:
                        db_insert('user_assignments', {'assignment_id': uid('UASN'), 'user_id': uidv, 'assignment_type': typ, 'assigned_user_id': ident, 'assigned_user_name': nm, 'effective_from': str(effective_from), 'effective_to': '', 'status': 'Active', 'created_by': actor_get(actor, 'user_id'), 'created_on': now()})
                an, ai = _parse_user_label(a)
                tn, ti = _parse_user_label(t)
                db_update('users', 'user_id', uidv, {'assigner_id': ai, 'assigner_name': an, 'tutor_id': ti, 'tutor_name': tn, 'mentor_id': ti, 'mentor_name': tn, 'trainer_id': ti, 'trainer_name': tn})
                new = f'Assigner={an}; Trainer={tn}'
                audit('User Assignments Updated', f'{old} -> {new}', actor=actor, entity_type='User', entity_id=uidv, reason=reason, before_value=old, after_value=new)
                st.success('Responsibilities updated and previous assignments closed in history.')
                st.rerun()
        st.markdown('#### Assignment history')
        table(assignments.sort_values('effective_from', ascending=False) if not assignments.empty else assignments, max_rows=200)
    with tabs[3]:
        overrides = db_where('user_permission_overrides', 'user_id = :uid', (('uid', uidv),))
        st.markdown('#### Access summary')
        st.info(f"Baseline access comes from role: **{user.get('role', '—')}**. User-specific overrides should be exceptional, time-bounded and reasoned.")
        table(overrides.sort_values('effective_from', ascending=False) if not overrides.empty else overrides)
        st.caption('Manage role permissions and controlled user overrides from the Permissions page. This profile intentionally does not duplicate that workflow.')
    with tabs[4]:
        st.markdown('#### Account lifecycle')
        c1, c2 = st.columns(2)
        new_status = c1.selectbox('Account Status', ADMIN_ACCOUNT_STATUSES, index=ADMIN_ACCOUNT_STATUSES.index(status_now) if status_now in ADMIN_ACCOUNT_STATUSES else 1, key=f'status_{uidv}')
        new_availability = c2.selectbox('Availability', AVAILABILITY_STATUSES, index=AVAILABILITY_STATUSES.index(user.get('availability')) if user.get('availability') in AVAILABILITY_STATUSES else 0, key=f'avail_{uidv}')
        reason = st.text_area('Reason for account/status change', key=f'status_reason_{uidv}')
        if st.button('Save Account Status', key=f'save_status_{uidv}', type='primary'):
            if not reason.strip():
                st.error('A reason is required for account-status changes.')
            else:
                old_status = status_now
                patch = {'account_status': new_status, 'status': new_status, 'availability': new_availability}
                if new_status == 'Deactivated':
                    patch.update({'deactivated_on': now(), 'deactivation_reason': reason})
                db_update('users', 'user_id', uidv, patch)
                audit('User Account Status Changed', f"{user.get('name', '')} {old_status} -> {new_status}; availability={new_availability}", actor=actor, entity_type='User', entity_id=uidv, reason=reason, before_value=old_status, after_value=new_status)
                st.success('Account status saved.')
                st.rerun()
        st.markdown('#### Security')
        st.caption('Passwords are never displayed or stored in plaintext. A reset generates a new temporary password and requires a password change at next sign-in.')
        reset_reason = st.text_input('Reason for password reset', key=f'reset_reason_{uidv}')
        if st.button('Generate New Temporary Password', key=f'reset_pw_{uidv}'):
            if not reset_reason.strip():
                st.error('Please provide a reason for the password reset.')
            else:
                new_temp = temp_password()
                db_update('users', 'user_id', uidv, {'password_hash': phash(new_temp), 'force_password_change': 'Yes'})
                audit('User Password Reset', f"Temporary password generated for {user.get('name', '')}", actor=actor, entity_type='User', entity_id=uidv, reason=reset_reason)
                st.success('Temporary password generated. Display it once and provide it securely to the user.')
                st.code(new_temp)
    with tabs[5]:
        history = db_where('audit_trail', "entity_type = 'User' and entity_id = :uid", (('uid', uidv),))
        st.caption('User History is a filtered, read-only view of the organization-wide Audit Trail; it is not a second audit system.')
        table(history.sort_values('date_time', ascending=False) if not history.empty else history, max_rows=300)

def departments_page(actor):
    """Professional department master-data administration."""
    st.header('Departments')
    if not _admin_only(actor):
        return
    # Department schema is migration-owned; no page-level DDL.
    try:
        deps = db_all('departments')
    except Exception:
        deps = pd.DataFrame()
    if deps.empty:
        for d in DEPARTMENTS:
            try:
                db_insert('departments', {'department_id': uid('DEP'), 'department_name': d, 'description': '', 'head_user_id': '', 'deputy_user_id': '', 'status': 'Active', 'created_on': today(), 'updated_on': now()})
            except Exception:
                pass
        deps = db_all('departments')
    for col, default in [('description', ''), ('head_user_id', ''), ('deputy_user_id', ''), ('status', 'Active')]:
        if col not in deps.columns:
            deps[col] = default
    users = db_all('users')
    active_users = users[users['status'].astype(str) == 'Active'] if not users.empty and 'status' in users.columns else users

    def member_frame(dept: str) -> pd.DataFrame:
        if users.empty or 'department' not in users.columns:
            return pd.DataFrame()
        return users[users['department'].astype(str).apply(lambda x: dept in split_list(x))].copy()

    def head_name(user_id: str) -> str:
        if not users.empty and user_id and ('user_id' in users.columns) and (user_id in users['user_id'].values):
            return str(users[users['user_id'] == user_id].iloc[0].get('name', '—'))
        return '—'
    active_departments = deps[deps['status'].astype(str) == 'Active'] if not deps.empty else deps
    inactive_departments = deps[deps['status'].astype(str) != 'Active'] if not deps.empty else deps
    in_use = sum((1 for d in deps['department_name'].astype(str) if len(member_frame(d)) > 0)) if not deps.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Active Departments', len(active_departments))
    c2.metric('Inactive Departments', len(inactive_departments))
    c3.metric('Active Employees', len(active_users))
    c4.metric('Departments in Use', in_use)
    st.subheader('Department Directory')
    f1, f2 = st.columns([2, 1])
    search = f1.text_input('Search departments', placeholder='Department name or description')
    status_filter = f2.selectbox('Status', ['All', 'Active', 'Inactive'])
    shown = deps.copy()
    if search.strip():
        q = search.strip().lower()
        shown = shown[shown['department_name'].astype(str).str.lower().str.contains(q, na=False) | shown['description'].astype(str).str.lower().str.contains(q, na=False)]
    if status_filter != 'All':
        shown = shown[shown['status'].astype(str) == status_filter]
    if not shown.empty:
        directory = []
        for _, r in shown.sort_values('department_name').iterrows():
            members = member_frame(str(r['department_name']))
            primary = int(members['primary_department'].astype(str).eq(str(r['department_name'])).sum()) if not members.empty and 'primary_department' in members.columns else 0
            directory.append({'Department': r['department_name'], 'Status': r.get('status', 'Active'), 'Primary Members': primary, 'Total Members': len(members), 'Head': head_name(str(r.get('head_user_id', '')))})
        table(pd.DataFrame(directory), max_rows=100)
    else:
        st.info('No departments match the current filter.')
    st.subheader('Department Actions')
    action = st.radio('Action', ['View / Edit', 'Add Department'], horizontal=True, label_visibility='collapsed')
    if action == 'Add Department':
        with st.form('add_department_professional'):
            st.markdown('#### Create Department')
            a, b = st.columns(2)
            name = a.text_input('Department Name *')
            status = b.selectbox('Status', ['Active', 'Inactive'])
            description = st.text_area('Description', placeholder='Purpose, responsibilities and scope')
            labels = [''] + (_user_label_series(users) if not users.empty else [])
            head = st.selectbox('Department Head', labels)
            deputy = st.selectbox('Deputy / Alternate', labels)
            confirmed = st.checkbox('I confirm this is a new organizational unit.')
            submit = st.form_submit_button('Create Department', type='primary')
        if submit:
            clean = name.strip()
            names = deps['department_name'].astype(str).str.casefold().tolist() if not deps.empty else []
            if not confirmed:
                st.error('Please confirm that this is a new organizational unit.')
            elif not clean:
                st.error('Department name is required.')
            elif clean.casefold() in names:
                st.error('A department with this name already exists.')
            else:
                _, hid = _parse_user_label(head)
                _, did = _parse_user_label(deputy)
                if hid and hid == did:
                    st.error('Department Head and Deputy / Alternate must be different people.')
                else:
                    dep_id = uid('DEP')
                    db_insert('departments', {'department_id': dep_id, 'department_name': clean, 'description': description.strip(), 'head_user_id': hid, 'deputy_user_id': did, 'status': status, 'created_on': today(), 'updated_on': now()})
                    audit('Department Created', clean, actor=actor, entity_type='Department', entity_id=dep_id, reason='New department master record created')
                    st.success(f"Department '{clean}' created.")
                    st.rerun()
        return
    if deps.empty:
        st.info('No department records are available.')
        return
    selected = st.selectbox('Select Department', deps['department_name'].astype(str).sort_values().tolist())
    row = deps[deps['department_name'].astype(str) == selected].iloc[0]
    members = member_frame(selected)
    primary_members = members[members['primary_department'].astype(str) == selected] if not members.empty and 'primary_department' in members.columns else pd.DataFrame()
    additional_members = members[members['primary_department'].astype(str) != selected] if not members.empty and 'primary_department' in members.columns else pd.DataFrame()
    st.markdown(f'### {selected}')
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Total Members', len(members))
    m2.metric('Primary Members', len(primary_members))
    m3.metric('Additional Members', len(additional_members))
    m4.metric('Status', str(row.get('status', 'Active')))
    st.caption(f"Head: {head_name(str(row.get('head_user_id', '')))}  ·  Deputy/Alternate: {head_name(str(row.get('deputy_user_id', '')))}")
    tabs = st.tabs(['Profile', 'Members', 'Roles', 'Governance'])
    with tabs[0]:
        labels = [''] + (_user_label_series(users) if not users.empty else [])
        current_head = next((x for x in labels if x.endswith(f" — {row.get('head_user_id', '')}")), '')
        current_deputy = next((x for x in labels if x.endswith(f" — {row.get('deputy_user_id', '')}")), '')
        with st.form('edit_department_professional'):
            a, b = st.columns(2)
            desc = a.text_area('Description', str(row.get('description', '')))
            status = b.selectbox('Status', ['Active', 'Inactive'], index=0 if row.get('status') == 'Active' else 1)
            head = st.selectbox('Department Head', labels, index=labels.index(current_head) if current_head in labels else 0)
            deputy = st.selectbox('Deputy / Alternate', labels, index=labels.index(current_deputy) if current_deputy in labels else 0)
            reason = st.text_area('Reason for change *', placeholder='Required for auditable department changes')
            save = st.form_submit_button('Save Department', type='primary')
        if save:
            _, hid = _parse_user_label(head)
            _, did = _parse_user_label(deputy)
            changing_status = str(status) != str(row.get('status', 'Active'))
            if not reason.strip():
                st.error('A reason is required for department changes.')
            elif changing_status and status == 'Inactive' and (len(members) > 0):
                st.error('This department cannot be deactivated while users are assigned to it. Reassign memberships first so history remains intact.')
            elif hid and hid == did:
                st.error('Department Head and Deputy / Alternate must be different people.')
            else:
                old = f"status={row.get('status', '')}; head={row.get('head_user_id', '')}; deputy={row.get('deputy_user_id', '')}"
                db_update('departments', 'department_id', row['department_id'], {'description': desc.strip(), 'head_user_id': hid, 'deputy_user_id': did, 'status': status, 'updated_on': now()})
                audit('Department Updated', selected, actor=actor, entity_type='Department', entity_id=str(row['department_id']), reason=reason.strip(), before_value=old, after_value=f'status={status}; head={hid}; deputy={did}')
                st.success('Department updated.')
                st.rerun()
    with tabs[1]:
        st.caption('Department membership is maintained from Users & Roles. This page is read-only for membership to prevent duplicate assignment workflows.')
        cols = [c for c in ['employee_id', 'name', 'role', 'primary_department', 'department', 'account_status', 'availability'] if c in members.columns]
        table(members[cols].sort_values('name') if not members.empty else members)
    with tabs[2]:
        if members.empty or 'role' not in members.columns:
            st.info('No members to summarize.')
        else:
            summary = members.groupby('role').size().reset_index(name='Users').sort_values('Users', ascending=False)
            table(summary)
    with tabs[3]:
        st.markdown('**Department governance**')
        st.write('Departments define organizational membership and visibility. Roles and permissions determine authority. Department membership alone never grants approval rights.')
        st.write(f'Primary members: **{len(primary_members)}**')
        st.write(f'Additional members: **{len(additional_members)}**')
        st.write(f"Department head: **{head_name(str(row.get('head_user_id', '')))}**")
        st.write(f"Deputy / alternate: **{head_name(str(row.get('deputy_user_id', '')))}**")
        if str(row.get('status', 'Active')) == 'Inactive':
            st.warning('Inactive departments are not available for new users or new assignments. Historical membership remains available for audit and reporting.')

def permissions_page(actor):
    st.header('Permissions')
    if not _admin_only(actor):
        return
    roles = db_all('roles')
    perms = db_all('permissions')
    users = db_all('users')
    if roles.empty or perms.empty:
        st.warning('Permission master data is not initialized. Restart the application after database initialization.')
        return
    active_roles = roles[roles.get('status', 'Active') == 'Active'] if 'status' in roles.columns else roles
    role_names = active_roles['role_name'].astype(str).tolist()
    all_enabled = db_all('role_permissions')
    overrides_all = db_all('user_permission_overrides')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Roles', len(role_names))
    c2.metric('Permission Definitions', len(perms))
    c3.metric('Role Grants', int((all_enabled['enabled'] == 'Yes').sum()) if not all_enabled.empty and 'enabled' in all_enabled.columns else 0)
    c4.metric('User Overrides', len(overrides_all))
    tabs = st.tabs(['Role Profiles', 'Permission Matrix', 'User Overrides', 'Effective Access'])
    with tabs[0]:
        st.subheader('Role Profiles')
        selected_role = st.selectbox('Role', role_names, key='perm_role_profile')
        rr = active_roles[active_roles['role_name'] == selected_role].iloc[0]
        with st.form('role_profile_form'):
            desc = st.text_area('Role Description', value=str(rr.get('description', '')), height=90)
            status = st.selectbox('Status', ['Active', 'Inactive'], index=0 if str(rr.get('status', 'Active')) == 'Active' else 1)
            save_role = st.form_submit_button('Save Role Profile', type='primary')
        if save_role:
            reason = st.text_input('Reason for change *', key='role_reason')
            if not reason.strip():
                st.error('A reason is required for role profile changes.')
            else:
                old = f"status={rr.get('status', '')}; description={rr.get('description', '')}"
                db_update('roles', 'role_id', rr['role_id'], {'description': desc.strip(), 'status': status, 'updated_on': now()})
                audit('Role Profile Updated', selected_role, actor=actor, entity_type='Role', entity_id=str(rr['role_id']), reason=reason.strip(), before_value=old, after_value=f'status={status}; description={desc.strip()}')
                st.success('Role profile updated.')
                st.rerun()
    with tabs[1]:
        st.subheader('Permission Matrix')
        selected_role = st.selectbox('Role Profile', role_names, key='perm_matrix_role')
        f1, f2, f3 = st.columns(3)
        module = f1.selectbox('Module', ['All'] + sorted(perms['module_name'].dropna().unique().tolist()), key='perm_matrix_module')
        scope = f2.selectbox('Scope', ['All'] + PERMISSION_SCOPES, key='perm_matrix_scope')
        action = f3.selectbox('Action', ['All'] + PERMISSION_ACTIONS, key='perm_matrix_action')
        shown = _permission_rows_for_role(selected_role)
        if module != 'All':
            shown = shown[shown['module_name'] == module]
        if scope != 'All':
            shown = shown[shown['scope'] == scope]
        if action != 'All':
            shown = shown[shown['action'] == action]
        st.caption(f'{len(shown)} permission definitions')
        changes = []
        for _, p in shown.sort_values(['module_name', 'action', 'scope']).head(300).iterrows():
            label = f"{p['module_name']}  ·  {p['action']}  ·  {p['scope']}"
            checked = bool(p['enabled'])
            current = st.checkbox(label, value=checked, key=f"pm_{selected_role}_{p['permission_id']}")
            if current != checked:
                changes.append((str(p['permission_id']), current))
        reason = st.text_input('Reason for permission changes *', key='perm_matrix_reason')
        if changes and st.button('Save Permission Changes', type='primary', key='save_perm_matrix'):
            if not reason.strip():
                st.error('A reason is required before permissions can be changed.')
            else:
                for pid, enable in changes:
                    existing = db_where('role_permissions', 'role_name = :role and permission_id = :pid', (('role', selected_role), ('pid', pid)))
                    payload = {'enabled': 'Yes' if enable else 'No', 'updated_on': now()}
                    if existing.empty:
                        payload.update({'role_permission_id': uid('RPERM'), 'role_name': selected_role, 'permission_id': pid, 'created_on': now()})
                        db_insert('role_permissions', payload)
                    else:
                        db_update('role_permissions', 'role_permission_id', existing.iloc[0]['role_permission_id'], payload)
                audit('Role Permissions Updated', selected_role, actor=actor, entity_type='Role', entity_id=selected_role, reason=reason.strip(), after_value=f'{len(changes)} permission changes')
                st.success(f'{len(changes)} permission change(s) saved.')
                st.rerun()
    with tabs[2]:
        st.subheader('User Overrides')
        if users.empty:
            st.info('No users are available.')
        else:
            user_options = [(str(r.get('name', '')), str(r.get('user_id', ''))) for _, r in users.iterrows()]
            labels = [f'{n} — {u}' for n, u in user_options]
            selected = st.selectbox('User', labels, key='override_user')
            uidv = selected.split(' — ', 1)[-1]
            urow = users[users['user_id'].astype(str) == uidv].iloc[0]
            st.info(f"Baseline role: **{urow.get('role', '')}** · Primary department: **{urow.get('primary_department', '')}**")
            overrides = db_where('user_permission_overrides', 'user_id = :uid', (('uid', uidv),))
            if not overrides.empty:
                disp = overrides.copy()
                if 'permission_id' in disp.columns:
                    lookup = perms.set_index('permission_id')[['module_name', 'action', 'scope']].to_dict('index')
                    disp['permission'] = disp['permission_id'].map(lambda x: f"{lookup.get(x, {}).get('module_name', '')} · {lookup.get(x, {}).get('action', '')} · {lookup.get(x, {}).get('scope', '')}")
                table(disp[[c for c in ['override_id', 'permission', 'enabled', 'reason', 'effective_from', 'effective_to', 'created_by', 'created_on'] if c in disp.columns]])
            else:
                st.info('No user-specific overrides.')
            with st.form('permission_override_form'):
                module_o = st.selectbox('Module', sorted(perms['module_name'].unique().tolist()))
                action_o = st.selectbox('Action', PERMISSION_ACTIONS)
                scope_o = st.selectbox('Scope', PERMISSION_SCOPES)
                enabled_o = st.selectbox('Override Result', ['Enable', 'Disable'])
                effective_from = st.date_input('Effective From', value=date.today())
                effective_to = st.date_input('Effective To', value=date.today() + timedelta(days=90))
                reason_o = st.text_area('Reason *')
                submit_o = st.form_submit_button('Save User Override', type='primary')
            if submit_o:
                if effective_to < effective_from:
                    st.error('Effective To cannot be earlier than Effective From.')
                elif not reason_o.strip():
                    st.error('A reason is required for every user override.')
                else:
                    matches = perms[(perms['module_name'] == module_o) & (perms['action'] == action_o) & (perms['scope'] == scope_o)]
                    if matches.empty:
                        st.error('That permission definition does not exist.')
                    else:
                        pid = matches.iloc[0]['permission_id']
                        db_insert('user_permission_overrides', {'override_id': uid('OVR'), 'user_id': uidv, 'permission_id': pid, 'enabled': 'Yes' if enabled_o == 'Enable' else 'No', 'reason': reason_o.strip(), 'effective_from': effective_from.isoformat(), 'effective_to': effective_to.isoformat(), 'created_by': actor_get(actor, 'user_id'), 'created_on': now()})
                        audit('User Permission Override', f'{selected}: {module_o}/{action_o}/{scope_o}={enabled_o}', actor=actor, entity_type='User', entity_id=uidv, reason=reason_o.strip(), after_value=f'effective {effective_from} to {effective_to}')
                        st.success('User override saved.')
                        st.rerun()
    with tabs[3]:
        st.subheader('Effective Access')
        if users.empty:
            st.info('No users are available.')
        else:
            selected_eff = st.selectbox('User', [f"{r.get('name', '')} — {r.get('user_id', '')}" for _, r in users.iterrows()], key='effective_user')
            uid_eff = selected_eff.split(' — ', 1)[-1]
            eff = _effective_permission_rows(uid_eff)
            search = st.text_input('Search effective permissions', key='effective_search')
            only_enabled = st.checkbox('Show enabled only', True, key='effective_enabled_only')
            if search.strip():
                mask = eff.apply(lambda r: search.lower() in f"{r.get('module_name', '')} {r.get('action', '')} {r.get('scope', '')}".lower(), axis=1)
                eff = eff[mask]
            if only_enabled:
                eff = eff[eff['enabled'] == True]
            table(eff[[c for c in ['module_name', 'action', 'scope', 'enabled', 'description'] if c in eff.columns]].sort_values(['module_name', 'action', 'scope']))

def system_settings_page(actor):
    st.header('System Settings')
    if not _admin_only(actor):
        return
    sched=scheduler_health_summary()
    st.subheader('Scheduler Health')
    metrics([('Last Status', sched['last_status']), ('Failed (24h)', str(sched['failed_24h'])), ('Last Run', sched['last_run'])])
    st.caption('Scheduler history is stored centrally. Use the live deployment test plan to validate retries and failure alerts.\n')
    settings = db_all('system_settings')
    if settings.empty:
        st.warning('System settings have not been initialized yet. Restart the application after the master seed runs.')
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Organization', _setting_value(settings, 'organization_name', APP_TITLE))
    c2.metric('Timezone', _setting_value(settings, 'timezone', 'Asia/Karachi'))
    c3.metric('Session', f"{_setting_value(settings, 'session_timeout_minutes', '60')} min")
    c4.metric('2FA', 'Enabled' if _setting_bool(settings, 'require_2fa') else 'Disabled')
    tabs = st.tabs(['General', 'Security', 'Notifications', 'Workflow', 'Documents & Storage', 'Scheduler', 'Email', 'System Defaults', 'Architecture Health'])
    with tabs[0]:
        st.subheader('General')
        with st.form('settings_general'):
            org_name = st.text_input('Organization Name', value=_setting_value(settings, 'organization_name', APP_TITLE))
            timezone = st.text_input('Time Zone', value=_setting_value(settings, 'timezone', 'Asia/Karachi'))
            date_format = st.selectbox('Date Format', ['DD-MMM-YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'], index=['DD-MMM-YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'].index(_setting_value(settings, 'date_format', 'DD-MMM-YYYY')) if _setting_value(settings, 'date_format', 'DD-MMM-YYYY') in ['DD-MMM-YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'] else 0)
            default_language = st.selectbox('Default Language', ['English'], index=0, help='Additional languages can be added later without changing the Administration workflow.')
            save = st.form_submit_button('Save General Settings', type='primary')
        if save:
            if not org_name.strip():
                st.error('Organization Name is required.')
            elif not timezone.strip():
                st.error('Time Zone is required.')
            else:
                for key, value in [('organization_name', org_name.strip()), ('timezone', timezone.strip()), ('date_format', date_format), ('default_language', default_language)]:
                    _save_setting(actor, key, value)
                st.success('General settings saved.')
                st.rerun()
    with tabs[1]:
        st.subheader('Security')
        with st.form('settings_security'):
            min_password = st.number_input('Minimum Password Length', min_value=8, max_value=128, value=int(_setting_value(settings, 'minimum_password_length', '12')), step=1)
            max_attempts = st.number_input('Maximum Login Attempts', min_value=3, max_value=20, value=int(_setting_value(settings, 'max_login_attempts', str(MAX_LOGIN_ATTEMPTS))), step=1)
            block_minutes = st.number_input('Account / Login Block Duration (minutes)', min_value=1, max_value=1440, value=int(_setting_value(settings, 'login_block_minutes', str(LOGIN_BLOCK_MINUTES))), step=1)
            session_minutes = st.number_input('Session Timeout (minutes)', min_value=5, max_value=1440, value=int(_setting_value(settings, 'session_timeout_minutes', '60')), step=5)
            password_expiry = st.number_input('Password Expiry (days)', min_value=0, max_value=3650, value=int(_setting_value(settings, 'password_expiry_days', '90')), step=1, help='0 disables forced password expiry.')
            require_2fa = st.toggle('Require two-factor authentication', value=_setting_bool(settings, 'require_2fa'))
            save = st.form_submit_button('Save Security Policy', type='primary')
        if save:
            for key, value in [('minimum_password_length', min_password), ('max_login_attempts', max_attempts), ('login_block_minutes', block_minutes), ('session_timeout_minutes', session_minutes), ('password_expiry_days', password_expiry), ('require_2fa', 'Yes' if require_2fa else 'No')]:
                _save_setting(actor, key, str(value))
            st.success('Security policy saved.')
            st.rerun()
    with tabs[2]:
        st.subheader('Notifications')
        with st.form('settings_notifications'):
            email_enabled = st.toggle('Email notifications', value=_setting_bool(settings, 'email_notifications_enabled', True))
            in_app_enabled = st.toggle('In-app notifications', value=_setting_bool(settings, 'in_app_notifications_enabled', True))
            training_enabled = st.toggle('Training reminders', value=_setting_bool(settings, 'training_notifications_enabled', True))
            authorization_enabled = st.toggle('Authorization expiry reminders', value=_setting_bool(settings, 'authorization_notifications_enabled', True))
            ncr_enabled = st.toggle('NCR due reminders', value=_setting_bool(settings, 'ncr_notifications_enabled', True))
            revalidation_enabled = st.toggle('Revalidation reminders', value=_setting_bool(settings, 'revalidation_notifications_enabled', True))
            save = st.form_submit_button('Save Notification Settings', type='primary')
        if save:
            for key, value in [('email_notifications_enabled', email_enabled), ('in_app_notifications_enabled', in_app_enabled), ('training_notifications_enabled', training_enabled), ('authorization_notifications_enabled', authorization_enabled), ('ncr_notifications_enabled', ncr_enabled), ('revalidation_notifications_enabled', revalidation_enabled)]:
                _save_setting(actor, key, 'Yes' if value else 'No')
            st.success('Notification settings saved.')
            st.rerun()
    with tabs[3]:
        st.subheader('Workflow')
        with st.form('settings_workflow'):
            training_days = st.number_input('Training reminder lead time (days)', min_value=0, max_value=365, value=int(_setting_value(settings, 'training_reminder_days', '30')), step=1)
            auth_days = st.number_input('Authorization expiry reminder lead time (days)', min_value=0, max_value=365, value=int(_setting_value(settings, 'authorization_reminder_days', '90')), step=1)
            reval_days = st.number_input('Revalidation reminder lead time (days)', min_value=0, max_value=365, value=int(_setting_value(settings, 'revalidation_reminder_days', '90')), step=1)
            ncr_days = st.number_input('NCR due reminder lead time (days)', min_value=0, max_value=180, value=int(_setting_value(settings, 'ncr_reminder_days', '7')), step=1)
            save = st.form_submit_button('Save Workflow Settings', type='primary')
        if save:
            for key, value in [('training_reminder_days', training_days), ('authorization_reminder_days', auth_days), ('revalidation_reminder_days', reval_days), ('ncr_reminder_days', ncr_days)]:
                _save_setting(actor, key, str(value))
            st.success('Workflow reminder settings saved.')
            st.rerun()
    with tabs[4]:
        st.subheader('Documents & Storage')
        c1, c2 = st.columns(2)
        c1.metric('Storage Provider', 'Supabase Storage' if storage_is_persistent() else 'Local / Not configured')
        c2.metric('Database', 'PostgreSQL / Supabase' if database_is_persistent() else 'SQLite / Local')
        st.info('File records are not managed here. Training materials, competency evidence, authorization documents and certificates remain attached to their respective modules.')
    with tabs[5]:
        st.subheader('Scheduler')
        scheduler_enabled = _setting_bool(settings, 'scheduler_enabled', True)
        last_tick = _setting_value(settings, 'scheduler_last_tick', 'Not recorded')
        next_tick = _setting_value(settings, 'scheduler_next_tick', 'Not recorded')
        c1, c2, c3 = st.columns(3)
        c1.metric('Scheduler', 'Enabled' if scheduler_enabled else 'Disabled')
        c2.metric('Last Tick', last_tick)
        c3.metric('Next Expected Tick', next_tick)
        with st.form('settings_scheduler'):
            enabled = st.toggle('Enable scheduler', value=scheduler_enabled)
            st.text_input('Health check', value='Configured / runtime-managed', disabled=True)
            save = st.form_submit_button('Save Scheduler Setting', type='primary')
        if save:
            _save_setting(actor, 'scheduler_enabled', 'Yes' if enabled else 'No')
            st.success('Scheduler setting saved.')
            st.rerun()
    with tabs[6]:
        st.subheader('Email')
    with tabs[7]:
        st.subheader('System Defaults')
        defaults = {'Organization': _setting_value(settings, 'organization_name', APP_TITLE), 'Timezone': _setting_value(settings, 'timezone', 'Asia/Karachi'), 'Date format': _setting_value(settings, 'date_format', 'DD-MMM-YYYY'), 'Default language': _setting_value(settings, 'default_language', 'English'), 'Default permission scopes': ', '.join(PERMISSION_SCOPES), 'Departments': ', '.join(DEPARTMENTS)}
        table(pd.DataFrame(list(defaults.items()), columns=['Setting', 'Value']))
    with tabs[8]:
        st.subheader('Architecture Health')
        health = phase2_health_snapshot()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Overall', str(health.get('status', 'unknown')).title())
        c2.metric('Database', 'Ready' if health.get('database_persistent') else 'Not Persistent')
        c3.metric('Storage', 'Ready' if health.get('storage_persistent') else 'Not Persistent')
        c4.metric('Schema Contract', 'OK' if health.get('schema_contract_ok') else 'Gap')
        if health.get('missing_schema_tables'):
            st.error(f"Schema contract gaps: {', '.join(health['missing_schema_tables'])}")
        st.markdown('**Performance instrumentation**')
        perf = health.get('performance', {})
        table(pd.DataFrame(list(perf.items()), columns=['Metric', 'Value']))
        st.info('RLS integration tests remain a staging/deployment responsibility because the exact Supabase Auth → PSB user mapping is environment-specific. The shipped RLS template intentionally defaults to denial for direct client access.')

def audit_trail_page(actor):
    st.header('Audit Trail')
    st.caption('Immutable business-level history of administrative and operational changes. Audit records are evidence and cannot be edited or deleted from the application.')
    if not _admin_only(actor):
        return
    audits = db_all('audit_trail')
    if audits.empty:
        st.info('No audit events found yet.')
        return
    audits = audits.copy()
    audits['_dt'] = pd.to_datetime(audits.get('date_time', ''), errors='coerce')
    audits['_dt_date'] = audits['_dt'].dt.date
    users = db_all('users')
    if not users.empty and 'user_id' in users.columns:
        dept_map = users.set_index('user_id').get('primary_department', pd.Series(dtype=str)).fillna('').to_dict()
        audits['actor_department'] = audits.get('actor_id', '').astype(str).map(dept_map).fillna('')
    else:
        audits['actor_department'] = ''
    min_dt = audits['_dt_date'].dropna().min()
    max_dt = audits['_dt_date'].dropna().max()
    if pd.isna(min_dt) or pd.isna(max_dt):
        min_dt = date.today() - timedelta(days=30)
        max_dt = date.today()
    st.markdown('### Audit Overview')
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Total Events', len(audits))
    m2.metric('Today', int((audits['_dt_date'] == date.today()).sum()))
    m3.metric('Successful', int((audits['result'].astype(str).str.lower() == 'success').sum()))
    m4.metric('Failed / Other', int((audits['result'].astype(str).str.lower() != 'success').sum()))
    st.markdown('### Filters')
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    start_date = r1c1.date_input('From', value=min_dt, min_value=min_dt, max_value=max_dt)
    end_date = r1c2.date_input('To', value=max_dt, min_value=min_dt, max_value=max_dt)
    actor_filter = r1c3.selectbox('Actor', ['All'] + sorted(audits['actor_name'].fillna('').astype(str).replace('nan', '').unique().tolist()))
    department_filter = r1c4.selectbox('Actor Department', ['All'] + sorted([x for x in audits['actor_department'].astype(str).unique().tolist() if x]))
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    entity_filter = r2c1.selectbox('Module / Entity', ['All'] + sorted(audits['entity_type'].fillna('').astype(str).replace('nan', '').unique().tolist()))
    action_filter = r2c2.selectbox('Action', ['All'] + sorted(audits['action'].fillna('').astype(str).replace('nan', '').unique().tolist()))
    result_filter = r2c3.selectbox('Result', ['All'] + sorted(audits['result'].fillna('').astype(str).replace('nan', '').unique().tolist()))
    search = r2c4.text_input('Search', placeholder='ID, details, reason, record...')
    shown = audits.copy()
    if start_date > end_date:
        st.error("The 'From' date cannot be later than the 'To' date.")
        return
    shown = shown[(shown['_dt_date'] >= start_date) & (shown['_dt_date'] <= end_date)]
    if actor_filter != 'All':
        shown = shown[shown['actor_name'].astype(str) == actor_filter]
    if department_filter != 'All':
        shown = shown[shown['actor_department'].astype(str) == department_filter]
    if entity_filter != 'All':
        shown = shown[shown['entity_type'].astype(str) == entity_filter]
    if action_filter != 'All':
        shown = shown[shown['action'].astype(str) == action_filter]
    if result_filter != 'All':
        shown = shown[shown['result'].astype(str) == result_filter]
    if search.strip():
        q = search.strip()
        mask = pd.Series(False, index=shown.index)
        for col in ['audit_id', 'details', 'entity_id', 'reason', 'before_value', 'after_value']:
            if col in shown.columns:
                mask = mask | shown[col].astype(str).str.contains(q, case=False, na=False)
        shown = shown[mask]
    shown = shown.sort_values('_dt', ascending=False)
    st.caption(f'Showing {len(shown)} of {len(audits)} audit events')
    display_cols = [c for c in ['date_time', 'actor_name', 'actor_role', 'actor_department', 'action', 'entity_type', 'entity_id', 'result'] if c in shown.columns]
    if not shown.empty:
        table(shown[display_cols], max_rows=1000)
        export_df = shown[[c for c in ['audit_id', 'date_time', 'actor_id', 'actor_name', 'actor_role', 'actor_department', 'action', 'details', 'result', 'entity_type', 'entity_id', 'reason', 'before_value', 'after_value', 'session_id'] if c in shown.columns]].copy()
        st.download_button('Export Filtered Audit Log (CSV)', export_df.to_csv(index=False).encode('utf-8'), file_name=f"psb_audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime='text/csv', key='audit_export_csv')
        st.markdown('### Event Details')
        event_options = shown['audit_id'].astype(str).tolist() if 'audit_id' in shown.columns else []
        if event_options:
            selected = st.selectbox('Select Audit Event', event_options, key='audit_event_selector')
            event = shown[shown['audit_id'].astype(str) == selected].iloc[0]
            a1, a2 = st.columns(2)
            with a1:
                st.markdown('**Event**')
                st.write(f"**ID:** {event.get('audit_id', '—')}")
                st.write(f"**Date/Time:** {event.get('date_time', '—')}")
                st.write(f"**Actor:** {event.get('actor_name', '—')} ({event.get('actor_role', '—')})")
                st.write(f"**Department:** {event.get('actor_department', '—') or '—'}")
                st.write(f"**Action:** {event.get('action', '—')}")
                st.write(f"**Result:** {event.get('result', '—')}")
            with a2:
                st.markdown('**Record & Change**')
                st.write(f"**Entity:** {event.get('entity_type', '—')}")
                st.write(f"**Record ID:** {event.get('entity_id', '—')}")
                st.write(f"**Reason:** {event.get('reason', '—') or '—'}")
                st.write(f"**Session:** {event.get('session_id', '—') or '—'}")
            with st.expander('Details'):
                st.write(event.get('details', '') or '—')
            b1, b2 = st.columns(2)
            with b1:
                st.markdown('**Before**')
                st.code(event.get('before_value', '') or '—', language='text')
            with b2:
                st.markdown('**After**')
                st.code(event.get('after_value', '') or '—', language='text')
    else:
        st.info('No audit events match the selected filters.')
    st.warning('Audit Trail is read-only. No edit or delete operation is provided for audit records.')

def backup_recovery_page(actor):
    st.header('Backup & Recovery')
    if not _admin_only(actor):
        return
    tables = _backup_export_tables()
    history = db_all('backup_records')
    requests = db_all('recovery_requests')
    st.subheader('Protection Status')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Database', 'Persistent' if database_is_persistent() else 'Local / Temporary')
    c2.metric('Storage', 'Supabase Storage' if storage_is_persistent() else 'Local / Not configured')
    c3.metric('Tables Covered', len(tables))
    last_backup = '—'
    if not history.empty and 'completed_on' in history.columns:
        ok = history[history['status'].astype(str).str.lower().eq('success')]
        if not ok.empty:
            last_backup = str(ok.sort_values('completed_on', ascending=False).iloc[0]['completed_on'])
    c4.metric('Last Recorded Export', last_backup)
    st.info('These exports are application-level data exports. Database and file-storage disaster recovery should also be configured at the Supabase/hosting level outside this application.')
    st.subheader('Create Application Backup')
    with st.form('create_application_backup'):
        backup_type = st.selectbox('Export Format', ['Application Data Export (JSON)', 'Application Data Export (Excel)'])
        notes = st.text_area('Notes', placeholder='Purpose, change window or other backup context')
        create_backup = st.form_submit_button('Generate Backup', type='primary')
    if create_backup:
        started = now()
        payload, mime, filename = _build_backup_payload(backup_type, tables)
        backup_id = uid('BKP')
        db_insert('backup_records', {'backup_id': backup_id, 'backup_type': backup_type, 'started_on': started, 'completed_on': now(), 'status': 'Success', 'file_name': filename, 'size_bytes': len(payload), 'created_by': actor_get(actor, 'user_id'), 'notes': notes})
        audit('Backup Export Created', filename, actor=actor, entity_type='Backup', entity_id=backup_id, reason=notes, after_value=f'{backup_type}; {len(tables)} tables; {len(payload)} bytes')
        st.session_state['psb_last_backup_payload'] = payload
        st.session_state['psb_last_backup_mime'] = mime
        st.session_state['psb_last_backup_filename'] = filename
        st.session_state['psb_last_backup_id'] = backup_id
        st.success(f'Backup {backup_id} generated successfully. Credentials and secret settings were excluded.')
    if st.session_state.get('psb_last_backup_payload'):
        c1, c2 = st.columns([2, 1])
        c1.download_button('Download Latest Backup', st.session_state['psb_last_backup_payload'], file_name=st.session_state['psb_last_backup_filename'], mime=st.session_state['psb_last_backup_mime'], use_container_width=True)
        c2.caption(f"Backup ID: {st.session_state.get('psb_last_backup_id', '—')}")
    st.subheader('Backup History')
    if not history.empty:
        h1, h2, h3 = st.columns(3)
        status_filter = h1.selectbox('Status', ['All'] + sorted(history['status'].dropna().astype(str).unique().tolist())) if 'status' in history.columns else 'All'
        type_filter = h2.selectbox('Format', ['All'] + sorted(history['backup_type'].dropna().astype(str).unique().tolist())) if 'backup_type' in history.columns else 'All'
        created_by_filter = h3.selectbox('Created By', ['All'] + sorted(history['created_by'].dropna().astype(str).unique().tolist())) if 'created_by' in history.columns else 'All'
        filtered = history.copy()
        if status_filter != 'All':
            filtered = filtered[filtered['status'].astype(str) == status_filter]
        if type_filter != 'All':
            filtered = filtered[filtered['backup_type'].astype(str) == type_filter]
        if created_by_filter != 'All':
            filtered = filtered[filtered['created_by'].astype(str) == created_by_filter]
        if 'completed_on' in filtered.columns:
            filtered = filtered.sort_values('completed_on', ascending=False)
        table(filtered)
    else:
        st.info('No application backups have been recorded yet.')
    st.subheader('Controlled Recovery Requests')
    st.warning('No production restore is performed from this page. Recovery is a controlled operational process and must be executed using the approved hosting/Supabase recovery procedure.')
    with st.form('recovery_request'):
        restore_point = st.text_input('Restore Point / Backup ID *')
        reason = st.text_area('Business Reason *')
        impact = st.text_area('Expected Impact / Scope', placeholder='What should be restored and why?')
        confirm = st.checkbox('I understand this is a recovery request and not an immediate restore')
        submit = st.form_submit_button('Submit Recovery Request', type='primary')
    if submit:
        if not restore_point or not reason or (not confirm):
            st.error('Restore point, business reason and confirmation are required.')
        else:
            rid = uid('REC')
            db_insert('recovery_requests', {'recovery_id': rid, 'restore_point': restore_point, 'reason': reason, 'requested_by': actor_get(actor, 'user_id'), 'requested_on': now(), 'status': 'Requested', 'approved_by': '', 'approved_on': '', 'completed_on': '', 'result': impact})
            audit('Recovery Requested', restore_point, actor=actor, entity_type='Recovery', entity_id=rid, reason=reason, after_value=impact)
            st.success(f'Recovery request {rid} submitted for controlled approval.')
    st.subheader('Recovery History')
    if not requests.empty:
        table(requests.sort_values('requested_on', ascending=False) if 'requested_on' in requests.columns else requests)
    else:
        st.info('No recovery requests have been submitted.')
    st.subheader('Restore Test Register')
    restore_tests=db_all('restore_tests') if table_exists('restore_tests') else pd.DataFrame()
    with st.expander('Record Controlled Restore Test', expanded=False):
        with st.form('record_restore_test'):
            rpoint=st.text_input('Restore Point / Backup ID')
            tested_on=st.date_input('Tested On', value=date.today())
            result=st.selectbox('Result',['Passed','Passed with Actions','Failed'])
            duration=st.number_input('Duration (minutes)', min_value=0, max_value=100000, value=0)
            findings=st.text_area('Findings')
            corrective=st.text_area('Corrective Action')
            save=st.form_submit_button('Record Restore Test', type='primary')
        if save:
            tid=uid('RST')
            db_insert('restore_tests',{'test_id':tid,'restore_point':rpoint,'tested_on':str(tested_on),'tested_by':actor_get(actor,'user_id'),'status':result,'duration_minutes':int(duration),'findings':findings,'corrective_action':corrective,'created_on':now()})
            audit('Restore Test Recorded',tid,actor=actor,entity_type='restore_tests',entity_id=tid,reason=findings or result)
            st.success('Restore test recorded.'); st.rerun()
    if not restore_tests.empty:
        table(restore_tests.sort_values('tested_on',ascending=False) if 'tested_on' in restore_tests.columns else restore_tests)
    else:
        st.info('No controlled restore tests recorded yet.')
    st.subheader('Governance Checks')
    g1, g2, g3, g4 = st.columns(4)
    g1.metric('Recorded Backups', int(len(history)))
    g2.metric('Recovery Requests', int(len(requests)))
    last_restore = restore_tests.sort_values('tested_on',ascending=False).iloc[0] if not restore_tests.empty and 'tested_on' in restore_tests.columns else None
    g3.metric('Restore Test', str(last_restore.get('status','Not recorded')) if last_restore is not None else 'Not recorded')
    g4.metric('RPO / RTO', '24h / 4h')
    st.caption('A backup is not considered dependable for disaster recovery until a controlled restore test has been performed and documented outside this export interface.')
