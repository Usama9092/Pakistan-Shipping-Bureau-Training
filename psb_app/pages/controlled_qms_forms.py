from __future__ import annotations

import base64

from psb_app.common import actor_get, audit, db_all, db_where, pd, st, table_exists, upload_file


_PATH_BY_ID = {
    'QP-NSC': 'NSC Surveyor',
    'QP-IS': 'In-Service Surveyor',
    'QP-IND': 'Industrial Surveyor',
    'QP-PA': 'Plan Appraiser',
}


def _uid(actor) -> str:
    return str(actor_get(actor, 'user_id', '') or '')


def _path_for_user(user_id: str) -> str:
    if table_exists('qualification_assignments'):
        qa = db_where('qualification_assignments', 'user_id = :uid AND status = :status', (('uid', user_id), ('status', 'Active')))
        if not qa.empty:
            return _PATH_BY_ID.get(str(qa.iloc[-1].get('path_id', '')), '')
    users = db_where('users', 'user_id = :uid', (('uid', user_id),)) if table_exists('users') else pd.DataFrame()
    if users.empty:
        return ''
    return str(users.iloc[-1].get('trainee_path') or '')


def _forms_for(path_name: str, stage: str):
    if not table_exists('controlled_qms_forms'):
        return pd.DataFrame()
    forms = db_all('controlled_qms_forms')
    if forms.empty:
        return forms
    path = str(path_name or '').strip().casefold()
    stage_cf = str(stage or '').strip().casefold()
    forms = forms[forms.get('active', pd.Series(dtype=str)).astype(str).str.casefold().isin(['yes', 'active', 'true', '1'])]
    stage_mask = forms.get('stages', pd.Series('', index=forms.index)).fillna('').astype(str).str.casefold().str.contains(stage_cf, regex=False)
    forms = forms[stage_mask]
    if forms.empty:
        return forms
    def applies(row) -> bool:
        key = str(row.get('path_key') or 'All').strip().casefold()
        if key in {'', 'all'}:
            return True
        if key == 'nsc surveyor':
            return ('nsc' in path) or ('new building' in path) or ('new construction' in path)
        if key == 'plan appraiser':
            return 'plan apprais' in path
        if key == 'in-service surveyor':
            return ('in-service' in path) or ('in service' in path) or ('existing ship' in path)
        return key == path
    return forms[forms.apply(applies, axis=1)]


def _form_bytes(row) -> bytes:
    raw = str(row.get('template_base64') or '').strip()
    if not raw:
        return b''
    try:
        return base64.b64decode(raw)
    except Exception:
        return b''


def _link_table(form_code: str) -> str:
    return 'qms_form_' + ''.join(ch.lower() if ch.isalnum() else '_' for ch in str(form_code)).strip('_')


def _record_key(user_id: str, path_name: str) -> str:
    return f"{str(user_id or '').strip()}::{str(path_name or '').strip()}"


def _existing_files(form_code: str, linked_id: str):
    if not table_exists('files'):
        return pd.DataFrame()
    return db_where('files', 'linked_table = :t AND linked_id = :id', (('t', _link_table(form_code)), ('id', linked_id)))


def _render_form(actor, row, linked_id: str, allow_upload: bool, key_prefix: str) -> bool:
    code = str(row.get('form_code', ''))
    existing = _existing_files(code, linked_id)
    with st.expander(f"{code} · {row.get('title','Controlled Form')}", expanded=True):
        st.caption(f"Applies to: {row.get('applies_to','')} · Controlled source: {row.get('procedure_ref','PSB QMS')}")
        st.write(str(row.get('purpose') or ''))
        template = _form_bytes(row)
        if template:
            st.download_button(
                'Download original blank controlled form',
                data=template,
                file_name=str(row.get('filename') or f'{code}.xlsx'),
                mime=str(row.get('mime_type') or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                key=f'{key_prefix}_blank_{code}',
                use_container_width=True,
            )
        else:
            st.info(f"Controlled master registered as: {row.get('filename','')}. The workflow slot is active; QMS can upload a completed/signed XLSX or PDF as evidence below.")
        if existing.empty:
            st.warning('Completed / signed form has not yet been linked to this controlled record.')
        else:
            st.success('Completed / signed controlled form evidence is on record.')
            cols = [c for c in ['file_name', 'category', 'review_status', 'information_classification', 'created_on'] if c in existing.columns]
            if cols:
                st.dataframe(existing[cols], use_container_width=True, hide_index=True)
        if allow_upload:
            st.markdown('**Upload completed / signed controlled form**')
            classification = st.selectbox(
                'Information Classification',
                ['Internal', 'Confidential', 'Restricted Technical', 'Public'],
                key=f'{key_prefix}_class_{code}',
            )
            uploads = st.file_uploader(
                'Upload completed form (XLSX/XLS/PDF)',
                type=['xlsx', 'xls', 'pdf'],
                accept_multiple_files=True,
                key=f'{key_prefix}_upload_{code}',
            )
            if st.button('Upload completed controlled form', key=f'{key_prefix}_upload_btn_{code}', use_container_width=True):
                if not uploads:
                    st.error('Select the completed/signed form first.')
                else:
                    count = 0
                    for f in uploads:
                        try:
                            upload_file(f, actor, _link_table(code), linked_id, str(row.get('category') or 'Other'), classification)
                            count += 1
                        except Exception as exc:
                            st.error(f'{f.name}: {exc}')
                    if count:
                        audit(
                            'Controlled QMS Form Uploaded',
                            f'{code} · {linked_id}',
                            actor=actor,
                            entity_type='files',
                            entity_id=linked_id,
                            reason=f'{count} completed controlled form file(s)',
                        )
                        st.success(f'{count} completed controlled form file(s) uploaded.')
                        st.rerun()
    return not existing.empty


def learner_controlled_forms_panel(actor) -> None:
    user_id = _uid(actor)
    path_name = _path_for_user(user_id)
    if not path_name:
        return
    training_forms = _forms_for(path_name, 'training')
    practical_forms = _forms_for(path_name, 'practical')
    authorization_forms = _forms_for(path_name, 'authorization')
    if training_forms.empty and practical_forms.empty and authorization_forms.empty:
        return
    st.markdown('### Controlled P20 / Authorization Forms')
    st.caption('Original PSB blank forms applicable to your qualification stages. Training, practical evidence and authorization decisions remain separate system records.')
    tabs = st.tabs(['Training Form', 'Practical / Status Form', 'Authorization Scope Form'])
    with tabs[0]:
        for _, row in training_forms.iterrows():
            _render_form(actor, row, 'GLOBAL', False, f'learner_training_{user_id}')
    with tabs[1]:
        if practical_forms.empty:
            st.info('No separate controlled practical/status sheet from the uploaded set applies to this path.')
        else:
            linked_id = _record_key(user_id, path_name)
            for _, row in practical_forms.iterrows():
                _render_form(actor, row, linked_id, False, f'learner_practical_{user_id}')
    with tabs[2]:
        if authorization_forms.empty:
            st.info('No separate controlled authorization-scope sheet from the uploaded set applies to this path.')
        else:
            linked_id = _record_key(user_id, path_name)
            for _, row in authorization_forms.iterrows():
                _render_form(actor, row, linked_id, False, f'learner_authorization_{user_id}')


def trainer_controlled_forms_panel(actor) -> None:
    if not table_exists('controlled_qms_forms'):
        return
    st.markdown('### Controlled P20 / OJTP Forms')
    st.caption('Use the official blank forms here. Completed/signed copies are stored as secure evidence and remain separate from the blank master template.')
    tabs = st.tabs(['Theoretical Training Control', 'Practical / Authorization Status'])
    with tabs[0]:
        rows = _forms_for('NSC Surveyor', 'training')
        for _, row in rows.iterrows():
            _render_form(actor, row, 'GLOBAL', True, 'trainer_training_global')
    with tabs[1]:
        path_name = st.selectbox('Qualification path for controlled form', ['NSC Surveyor', 'Plan Appraiser', 'In-Service Surveyor'], key='controlled_form_path')
        stage = 'authorization' if path_name == 'In-Service Surveyor' else 'practical'
        form_list = _forms_for(path_name, stage)
        if form_list.empty:
            st.info('No controlled form from the uploaded set applies to this path/stage.')
            return
        assignments = db_all('qualification_assignments') if table_exists('qualification_assignments') else pd.DataFrame()
        if not assignments.empty:
            pid = next((k for k, v in _PATH_BY_ID.items() if v == path_name), '')
            assignments = assignments[(assignments.get('path_id', pd.Series(dtype=str)).astype(str).eq(pid)) & (assignments.get('status', pd.Series(dtype=str)).astype(str).eq('Active'))]
        if assignments.empty:
            st.info('No active learner is assigned to this qualification path yet. The blank form is still available below.')
            for _, row in form_list.iterrows():
                _render_form(actor, row, f'UNASSIGNED::{path_name}', False, f'trainer_{path_name}_unassigned')
            return
        users = db_all('users') if table_exists('users') else pd.DataFrame()
        labels, mapping = [], {}
        for _, q in assignments.iterrows():
            uidv = str(q.get('user_id', ''))
            u = users[users.get('user_id', pd.Series(dtype=str)).astype(str).eq(uidv)] if not users.empty else pd.DataFrame()
            name = str(u.iloc[-1].get('name', uidv)) if not u.empty else uidv
            label = f'{name} — {uidv}'
            labels.append(label)
            mapping[label] = uidv
        choice = st.selectbox('Learner / staff member', labels, key=f'controlled_form_person_{path_name}')
        user_id = mapping[choice]
        linked_id = _record_key(user_id, path_name)
        for _, row in form_list.iterrows():
            _render_form(actor, row, linked_id, True, f'trainer_{path_name}_{user_id}')


def authorization_controlled_forms_panel(actor) -> None:
    if not table_exists('authorization_requests') or not table_exists('controlled_qms_forms'):
        return
    cases = db_where('authorization_requests', 'status = :status', (('status', 'CRB Recommended'),))
    if cases.empty:
        return
    st.markdown('### Mandatory Controlled Authorization Form')
    st.caption('Before final authorization, the applicable controlled PSB form should be completed/signed and linked to the same person and authorization scope.')
    labels, mapping = [], {}
    for _, r in cases.iterrows():
        aid = str(r.get('authorization_id', ''))
        label = f"{r.get('name','')} — {r.get('scope','')} — {aid}"
        labels.append(label)
        mapping[label] = r.to_dict()
    selected = st.selectbox('Authorization case for controlled form', labels, key='authorization_controlled_case')
    row = mapping[selected]
    path_name = str(row.get('scope') or row.get('trainee_path') or '')
    form_list = _forms_for(path_name, 'authorization')
    if form_list.empty:
        st.info('No uploaded controlled authorization form is mapped to this authorization path.')
        return
    linked_id = _record_key(str(row.get('user_id', '')), path_name)
    completed = 0
    for _, form in form_list.iterrows():
        completed += int(_render_form(actor, form, linked_id, True, f'authcase_{row.get("authorization_id","")}'))
    if completed < len(form_list):
        st.error('Required controlled authorization form evidence is still missing for this case. Complete/sign and upload it before the final authorization decision.')
    else:
        st.success('Required controlled authorization form evidence is linked and available for the final decision review.')
