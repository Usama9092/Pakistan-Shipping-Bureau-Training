"""Administrative recognition of already-authorized technical staff.

This is deliberately separate from the normal qualification/CRB workflow.
It is for controlled migration/recognition of a person whom PSB Admin confirms
was already trained and authorized before the digital platform record existed.
The action creates auditable training completions, one PSB-PTQ20-F03 attestation
per linked course, complete module progress, and the PSB-PTQ20-F02 authorization
certificate. It never fabricates an MCQ score or online attendance event.
"""
from __future__ import annotations

import json

from psb_app.common import (
    PUBLIC_URL,
    actor_get,
    audit,
    can_action,
    clean,
    create_notification,
    db_all,
    db_insert,
    db_update,
    db_where,
    now,
    pd,
    st,
    table_exists,
    today,
    uid,
)

PATHS = {
    'NSC Surveyor': {'id': 'QP-NSC', 'job_type': 'New Building Survey'},
    'In-Service Surveyor': {'id': 'QP-IS', 'job_type': 'In-Service Survey'},
    'Industrial Surveyor': {'id': 'QP-IND', 'job_type': 'Industrial Survey'},
    'Plan Appraiser': {'id': 'QP-PA', 'job_type': 'Plan Appraisal'},
}


def _allowed(actor: dict) -> bool:
    role = clean(actor_get(actor, 'role'))
    return role == 'Admin' or (
        role == 'GM' and can_action(actor, 'Administration', 'Manage', 'Organization-wide')
    )


def _row(table: str, where: str, params: tuple[tuple[str, str], ...]) -> dict:
    if not table_exists(table):
        return {}
    rows = db_where(table, where, params)
    return rows.iloc[-1].to_dict() if not rows.empty else {}


def _active_path_version(path_id: str) -> dict:
    if not table_exists('qualification_path_versions'):
        return {}
    rows = db_where(
        'qualification_path_versions',
        'path_id = :pid AND status = :status',
        (('pid', path_id), ('status', 'Active')),
    )
    if rows.empty:
        rows = db_where('qualification_path_versions', 'path_id = :pid', (('pid', path_id),))
    return rows.iloc[-1].to_dict() if not rows.empty else {}


def _path_modules(path_id: str) -> pd.DataFrame:
    if not all(table_exists(t) for t in ('qualification_path_versions', 'qualification_path_levels', 'qualification_level_modules', 'qualification_modules')):
        return pd.DataFrame()
    version = _active_path_version(path_id)
    vid = clean(version.get('path_version_id'))
    if not vid:
        return pd.DataFrame()
    levels = db_where('qualification_path_levels', 'path_version_id = :vid AND active = :a', (('vid', vid), ('a', 'Yes')))
    if levels.empty:
        levels = db_where('qualification_path_levels', 'path_version_id = :vid', (('vid', vid),))
    if levels.empty:
        return pd.DataFrame()
    level_ids = set(levels['level_id'].astype(str).tolist())
    lm = db_all('qualification_level_modules')
    if lm.empty:
        return pd.DataFrame()
    lm = lm[lm['level_id'].astype(str).isin(level_ids)]
    if 'active' in lm.columns:
        lm = lm[lm['active'].fillna('Yes').astype(str).eq('Yes')]
    qmods = db_all('qualification_modules')
    if qmods.empty:
        return lm
    cols = [c for c in ['module_id', 'module_code', 'module_name', 'module_type'] if c in qmods.columns]
    return lm.merge(qmods[cols], on='module_id', how='left')


def _path_training_rows(path_id: str, modules: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if table_exists('qualification_path_training'):
        pt = db_where('qualification_path_training', 'path_id = :pid AND active = :a', (('pid', path_id), ('a', 'Yes')))
        if not pt.empty:
            pt = pt.copy()
            pt['source'] = 'Path'
            frames.append(pt[[c for c in ['training_id', 'mandatory', 'sequence_no', 'source'] if c in pt.columns]])
    if table_exists('qualification_module_training') and not modules.empty:
        mt = db_all('qualification_module_training')
        if not mt.empty:
            mt = mt[mt['module_id'].astype(str).isin(set(modules['module_id'].astype(str).tolist()))]
            if 'active' in mt.columns:
                mt = mt[mt['active'].fillna('Yes').astype(str).eq('Yes')]
            if not mt.empty:
                mt = mt.copy()
                mt['source'] = 'Module'
                frames.append(mt[[c for c in ['module_id', 'training_id', 'mandatory', 'sequence_no', 'source'] if c in mt.columns]])
    if not frames:
        return pd.DataFrame(columns=['training_id'])
    out = pd.concat(frames, ignore_index=True, sort=False)
    out = out[out.get('training_id', pd.Series(dtype=str)).astype(str).str.len() > 0]
    return out.drop_duplicates(subset=['training_id'], keep='last')


def _module_for_training(training_id: str, modules: pd.DataFrame) -> tuple[str, str]:
    if table_exists('qualification_module_training') and not modules.empty:
        mt = db_where('qualification_module_training', 'training_id = :tid AND active = :a', (('tid', training_id), ('a', 'Yes')))
        if not mt.empty:
            mid = clean(mt.iloc[-1].get('module_id'))
            mm = modules[modules['module_id'].astype(str).eq(mid)] if 'module_id' in modules.columns else pd.DataFrame()
            if not mm.empty:
                return clean(mm.iloc[-1].get('module_code')), clean(mm.iloc[-1].get('module_name'))
    return '', ''


def _ensure_assignment(user: dict, path_name: str, path_id: str, trainer_id: str, trainer_name: str, actor: dict) -> str:
    user_id = clean(user.get('user_id'))
    existing = db_where('qualification_assignments', 'user_id = :uid AND status = :s', (('uid', user_id), ('s', 'Active'))) if table_exists('qualification_assignments') else pd.DataFrame()
    if not existing.empty:
        aid = clean(existing.iloc[-1].get('qualification_assignment_id'))
        db_update('qualification_assignments', 'qualification_assignment_id', aid, {
            'path_id': path_id, 'trainer_id': trainer_id, 'status': 'Active', 'updated_on': now()
        })
    else:
        aid = uid('QASG')
        db_insert('qualification_assignments', {
            'qualification_assignment_id': aid,
            'user_id': user_id,
            'path_id': path_id,
            'trainer_id': trainer_id,
            'tutor_id': trainer_id,
            'status': 'Active',
            'assigned_by': actor_get(actor, 'user_id', ''),
            'assigned_on': now(),
            'updated_on': now(),
        })
    db_update('users', 'user_id', user_id, {
        'trainee_path': path_name,
        'trainer_id': trainer_id,
        'trainer_name': trainer_name,
        'tutor_id': trainer_id,
        'tutor_name': trainer_name,
    })
    return aid


def _complete_training(user: dict, path_name: str, training_id: str, recognition_id: str, effective_date: str, trainer_id: str, trainer_name: str, actor: dict, modules: pd.DataFrame) -> str:
    user_id = clean(user.get('user_id'))
    course = _row('trainings', 'training_id = :tid', (('tid', training_id),))
    title = clean(course.get('title')) or training_id
    recs = db_where('training_records', 'user_id = :uid AND training_id = :tid', (('uid', user_id), ('tid', training_id))) if table_exists('training_records') else pd.DataFrame()
    if recs.empty:
        record_id = uid('TREC')
        db_insert('training_records', {
            'record_id': record_id,
            'user_id': user_id,
            'name': clean(user.get('name')),
            'role': clean(user.get('role')),
            'trainee_path': path_name,
            'training_id': training_id,
            'training_title': title,
            'status': 'Completed',
            'slides_opened': 'No',
            'video_opened': 'No',
            'reference_opened': 'No',
            'live_attendance': 'Administratively Recognized',
            'recording_opened': 'No',
            'lms_completed': 'No',
            'test_status': 'Administratively Recognized',
            'score': None,
            'passing_marks': int(course.get('passing_marks') or 70),
            'certificate_status': 'Not Issued',
            'certificate_link': '',
            'due_date': '',
            'completed_on': effective_date,
            'progress': 100,
            'remarks': 'Historical qualification completion recognized by PSB Admin; no online MCQ score or attendance event was fabricated.',
            'updated_on': now(),
            'assigned_on': effective_date,
            'assigned_by': actor_get(actor, 'name', ''),
            'assessment_attempts': 0,
            'last_assessment_on': '',
            'certificate_id': '',
            'certificate_issued_on': '',
            'certificate_issued_by': '',
            'completion_snapshot_json': json.dumps({'complete': True, 'completion_percent': 100, 'basis': 'Administrative recognition of prior completed training'}),
            'administrative_recognition': 'Yes',
            'recognition_id': recognition_id,
            'recognition_basis': 'PSB Admin confirmed prior completion for existing authorization',
        })
    else:
        record_id = clean(recs.iloc[-1].get('record_id'))
        db_update('training_records', 'record_id', record_id, {
            'status': 'Completed',
            'progress': 100,
            'completed_on': effective_date,
            'test_status': 'Administratively Recognized',
            'remarks': 'Historical qualification completion recognized by PSB Admin; no online MCQ score or attendance event was fabricated.',
            'completion_snapshot_json': json.dumps({'complete': True, 'completion_percent': 100, 'basis': 'Administrative recognition of prior completed training'}),
            'administrative_recognition': 'Yes',
            'recognition_id': recognition_id,
            'recognition_basis': 'PSB Admin confirmed prior completion for existing authorization',
            'updated_on': now(),
        })

    existing = db_where('training_attestation_certificates', 'record_id = :rid AND status = :s', (('rid', record_id), ('s', 'Valid'))) if table_exists('training_attestation_certificates') else pd.DataFrame()
    if not existing.empty:
        cert_id = clean(existing.iloc[-1].get('certificate_id'))
    else:
        cert_id = uid('ATT')
        module_code, module_name = _module_for_training(training_id, modules)
        if not module_name:
            module_name = title
        verification_url = f'{PUBLIC_URL}/?verify={cert_id}'
        db_insert('training_attestation_certificates', {
            'certificate_id': cert_id,
            'record_id': record_id,
            'training_id': training_id,
            'user_id': user_id,
            'name': clean(user.get('name')),
            'training_title': title,
            'module_code': module_code or 'PATH',
            'module_name': module_name,
            'conducted_on': effective_date,
            'issue_date': today(),
            'trainer_id': trainer_id,
            'trainer_name': trainer_name,
            'trainer_signed_on': now(),
            'ceo_name': 'Cdre Dr. M Saeed Khalid SI(M)',
            'document_code': 'PSB-PTQ20-F03',
            'revision_no': '01',
            'revision_date': '11-02-2026',
            'verification_url': verification_url,
            'status': 'Valid',
            'completion_basis': 'Administrative recognition of prior completed training for an already-authorized person',
            'recognition_id': recognition_id,
            'administrative_signoff_id': actor_get(actor, 'user_id', ''),
            'administrative_signoff_name': actor_get(actor, 'name', ''),
            'created_on': now(),
            'updated_on': now(),
        })
    db_update('training_records', 'record_id', record_id, {
        'certificate_status': 'Issued',
        'certificate_id': cert_id,
        'certificate_issued_on': today(),
        'certificate_issued_by': trainer_name,
        'certificate_link': f'{PUBLIC_URL}/?verify={cert_id}',
        'updated_on': now(),
    })
    return cert_id


def _complete_modules(user_id: str, assignment_id: str, modules: pd.DataFrame, recognition_id: str, effective_date: str) -> int:
    count = 0
    if modules.empty or not table_exists('qualification_module_progress'):
        return count
    for _, module in modules.drop_duplicates(subset=['module_id']).iterrows():
        mid = clean(module.get('module_id'))
        if not mid:
            continue
        existing = db_where('qualification_module_progress', 'user_id = :uid AND module_id = :mid', (('uid', user_id), ('mid', mid)))
        payload = {
            'qualification_assignment_id': assignment_id,
            'theory_status': 'Complete',
            'guided_practical_status': 'Complete',
            'trainer_gate_status': 'Ready',
            'independent_practical_status': 'Complete',
            'competency_status': 'Complete',
            'module_status': 'Complete',
            'completion_percent': 100,
            'completed_on': effective_date,
            'administrative_recognition': 'Yes',
            'recognition_id': recognition_id,
            'recognition_basis': 'Existing authorization recognized by PSB Admin',
            'updated_on': now(),
        }
        if existing.empty:
            db_insert('qualification_module_progress', {
                'module_progress_id': uid('QMP'),
                'qualification_assignment_id': assignment_id,
                'module_id': mid,
                'user_id': user_id,
                **payload,
            })
        else:
            db_update('qualification_module_progress', 'module_progress_id', clean(existing.iloc[-1].get('module_progress_id')), payload)
        count += 1
    return count


def recognize_existing_authorization(user_id: str, path_name: str, scope: str, trainer_id: str, trainer_name: str, effective_date: str, reason: str, actor: dict) -> dict:
    if not _allowed(actor):
        raise PermissionError('Only PSB Admin can record an existing authorization recognition.')
    if path_name not in PATHS:
        raise ValueError('Select a controlled qualification path.')
    if not trainer_id or not trainer_name:
        raise ValueError('Select the verifying Trainer. The Trainer signature appears on each attestation certificate.')
    if not reason.strip():
        raise ValueError('Recognition reason/reference is required.')
    user = _row('users', 'user_id = :uid', (('uid', user_id),))
    if not user:
        raise ValueError('Selected user was not found.')
    path_id = PATHS[path_name]['id']
    job_type = PATHS[path_name]['job_type']
    existing = db_where(
        'administrative_authorization_recognitions',
        'user_id = :uid AND path_id = :pid AND status = :status',
        (('uid', user_id), ('pid', path_id), ('status', 'Finalized')),
    ) if table_exists('administrative_authorization_recognitions') else pd.DataFrame()
    if not existing.empty:
        row = existing.iloc[-1]
        return {
            'recognition_id': clean(row.get('recognition_id')),
            'training_count': int(row.get('training_count') or 0),
            'attestation_count': int(row.get('attestation_count') or 0),
            'module_count': int(row.get('module_count') or 0),
            'authorization_certificate_id': clean(row.get('authorization_certificate_id')),
            'existing': True,
        }

    recognition_id = uid('AAR')
    db_insert('administrative_authorization_recognitions', {
        'recognition_id': recognition_id,
        'user_id': user_id,
        'name': clean(user.get('name')),
        'path_id': path_id,
        'path_name': path_name,
        'scope': scope,
        'job_type': job_type,
        'trainer_id': trainer_id,
        'trainer_name': trainer_name,
        'effective_date': effective_date,
        'recognition_reason': reason.strip(),
        'declaration': 'Admin confirmed that the person had already completed the applicable training and held/qualified for the stated authorization before digital migration.',
        'status': 'In Progress',
        'recognized_by_id': actor_get(actor, 'user_id', ''),
        'recognized_by_name': actor_get(actor, 'name', ''),
        'recognized_on': now(),
        'created_on': now(),
        'updated_on': now(),
    })

    assignment_id = _ensure_assignment(user, path_name, path_id, trainer_id, trainer_name, actor)
    modules = _path_modules(path_id)
    trainings = _path_training_rows(path_id, modules)
    if trainings.empty:
        db_update('administrative_authorization_recognitions', 'recognition_id', recognition_id, {'status': 'Failed', 'updated_on': now()})
        raise ValueError('No active training requirements are linked to this qualification path. Configure the path curriculum first.')

    attestation_ids = []
    for training_id in trainings['training_id'].astype(str).tolist():
        cid = _complete_training(user, path_name, training_id, recognition_id, effective_date, trainer_id, trainer_name, actor, modules)
        attestation_ids.append(cid)
    module_count = _complete_modules(user_id, assignment_id, modules, recognition_id, effective_date)

    auth_id = uid('AUTH')
    req = {
        'authorization_id': auth_id,
        'user_id': user_id,
        'name': clean(user.get('name')),
        'trainee_path': path_name,
        'job_type': job_type,
        'scope': scope,
        'competency_id': '',
        'status': 'Management Approved',
        'tutor_remarks': 'Administrative recognition of existing authorization; linked training attestations generated from confirmed prior completion.',
        'tutor_signature': trainer_name,
        'tutor_signed_on': now(),
        'principal_remarks': 'Administrative migration / recognition.',
        'principal_signature': actor_get(actor, 'name', ''),
        'principal_signed_on': now(),
        'technical_remarks': 'Existing authorization recognized by PSB Admin.',
        'technical_signature': actor_get(actor, 'name', ''),
        'technical_signed_on': now(),
        'qms_remarks': 'Administrative recognition record retained in audit trail.',
        'qms_signature': actor_get(actor, 'name', ''),
        'qms_signed_on': now(),
        'crb_decision': 'Administrative Recognition',
        'crb_remarks': reason.strip(),
        'management_remarks': reason.strip(),
        'management_signature': actor_get(actor, 'name', ''),
        'management_signed_on': now(),
        'certificate_id': '',
        'certificate_html': '',
        'certificate_storage_link': '',
        'qr_data_uri': '',
        'recognition_id': recognition_id,
        'authorization_basis': 'Administrative recognition of existing authorization after PSB Admin verification',
        'created_on': now(),
        'updated_on': now(),
    }
    db_insert('authorization_requests', req)
    from psb_app.pages.authorization import _issue_authorization_certificate
    fresh = db_where('authorization_requests', 'authorization_id = :aid', (('aid', auth_id),)).iloc[-1]
    auth_cert_id = _issue_authorization_certificate(fresh, actor)
    db_update('authorization_certificates', 'certificate_id', auth_cert_id, {
        'recognition_id': recognition_id,
        'authorization_basis': 'Administrative recognition of existing authorization after PSB Admin verification',
    })
    db_update('authorization_requests', 'authorization_id', auth_id, {
        'recognition_id': recognition_id,
        'authorization_basis': 'Administrative recognition of existing authorization after PSB Admin verification',
        'updated_on': now(),
    })
    db_update('administrative_authorization_recognitions', 'recognition_id', recognition_id, {
        'training_count': len(trainings),
        'attestation_count': len(attestation_ids),
        'module_count': module_count,
        'authorization_id': auth_id,
        'authorization_certificate_id': auth_cert_id,
        'status': 'Finalized',
        'updated_on': now(),
    })
    audit(
        'Existing Authorization Recognized',
        f"{clean(user.get('name'))} · {path_name} · {scope}",
        actor=actor,
        entity_type='administrative_authorization_recognitions',
        entity_id=recognition_id,
        reason=f"{reason.strip()} · {len(attestation_ids)} training attestations · authorization certificate {auth_cert_id}",
    )
    try:
        create_notification(
            user_id,
            'Qualification & Authorization Digitized',
            f'{len(attestation_ids)} training attestation certificate(s) and authorization certificate {auth_cert_id} have been added to your record.',
            'Authorization',
        )
    except Exception:
        pass
    return {
        'recognition_id': recognition_id,
        'training_count': len(trainings),
        'attestation_count': len(attestation_ids),
        'module_count': module_count,
        'authorization_id': auth_id,
        'authorization_certificate_id': auth_cert_id,
        'existing': False,
    }


def admin_existing_authorization_panel(actor: dict) -> None:
    if not _allowed(actor):
        return
    with st.expander('Admin · Recognize Existing Authorized Person', expanded=False):
        st.caption(
            'Use only for a person whom PSB Admin confirms was already trained/authorized before this digital workflow. '
            'This does not invent an MCQ score: it records an explicit administrative recognition, completes the linked path training, '
            'issues one PSB-PTQ20-F03 attestation per training with the selected Trainer on the right and CEO on the left, '
            'then issues the PSB-PTQ20-F02 authorization certificate.'
        )
        users = db_all('users')
        if users.empty:
            st.info('No users are available.')
            return
        eligible = users[users.get('status', pd.Series(dtype=str)).astype(str).eq('Active')] if 'status' in users.columns else users
        labels = (eligible['name'].astype(str) + ' — ' + eligible['role'].astype(str) + ' — ' + eligible['user_id'].astype(str)).tolist()
        selected = st.selectbox('Person *', labels, key='admin_recognition_person')
        user_id = selected.rsplit(' — ', 1)[-1]
        user = eligible[eligible['user_id'].astype(str).eq(user_id)].iloc[-1]
        current_path = clean(user.get('trainee_path'))
        path_names = list(PATHS)
        path_index = path_names.index(current_path) if current_path in path_names else 0
        c1, c2 = st.columns(2)
        path_name = c1.selectbox('Qualification path *', path_names, index=path_index, key='admin_recognition_path')
        scope = c2.text_input('Authorization scope *', value=path_name, key='admin_recognition_scope')

        trainers = users[(users.get('role', pd.Series(dtype=str)).astype(str) == 'Trainer') & (users.get('status', pd.Series(dtype=str)).astype(str) == 'Active')] if not users.empty else pd.DataFrame()
        trainer_labels = (trainers['name'].astype(str) + ' — ' + trainers['user_id'].astype(str)).tolist() if not trainers.empty else []
        current_trainer_id = clean(user.get('trainer_id'))
        trainer_index = 0
        for i, label in enumerate(trainer_labels):
            if label.endswith(' — ' + current_trainer_id):
                trainer_index = i
                break
        trainer_selected = st.selectbox('Verifying Trainer / attestation signer *', trainer_labels, index=trainer_index if trainer_labels else 0, key='admin_recognition_trainer') if trainer_labels else ''
        effective = st.date_input('Confirmed training/authorization completion date', value=pd.to_datetime(today()).date(), key='admin_recognition_date')
        reason = st.text_area('Admin verification reference / reason *', placeholder='e.g. Existing personnel file, prior authorization register, signed training record reference...', key='admin_recognition_reason')
        declaration = st.checkbox(
            'I confirm that PSB has verified this person had already completed the applicable qualification training and was authorized/qualified for the selected scope. I understand this action creates permanent digital training attestations and an authorization certificate.',
            key='admin_recognition_declaration',
        )
        if st.button('Recognize Existing Authorization & Generate Certificates', type='primary', disabled=not declaration, key='admin_recognition_submit'):
            if not trainer_selected:
                st.error('An active Trainer must be selected as the attestation signer.')
                return
            trainer_name, trainer_id = trainer_selected.rsplit(' — ', 1)
            if not scope.strip():
                st.error('Authorization scope is required.')
                return
            try:
                result = recognize_existing_authorization(
                    user_id=user_id,
                    path_name=path_name,
                    scope=scope.strip(),
                    trainer_id=trainer_id,
                    trainer_name=trainer_name,
                    effective_date=str(effective),
                    reason=reason,
                    actor=actor,
                )
                if result.get('existing'):
                    st.info(f"This person already has finalized administrative recognition {result['recognition_id']} with authorization certificate {result['authorization_certificate_id']}.")
                else:
                    st.success(
                        f"Completed: {result['training_count']} training record(s), {result['attestation_count']} attestation certificate(s), "
                        f"{result['module_count']} module(s), and authorization certificate {result['authorization_certificate_id']}."
                    )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if table_exists('administrative_authorization_recognitions'):
            history = db_where('administrative_authorization_recognitions', 'user_id = :uid', (('uid', user_id),))
            if not history.empty:
                st.markdown('#### Existing Recognition History')
                cols = [c for c in ['recognition_id', 'path_name', 'scope', 'trainer_name', 'effective_date', 'training_count', 'attestation_count', 'authorization_certificate_id', 'status', 'recognized_by_name', 'recognized_on'] if c in history.columns]
                st.dataframe(history[cols].sort_values('recognized_on', ascending=False) if 'recognized_on' in history.columns else history[cols], use_container_width=True, hide_index=True)


def install_admin_authorization_recognition_patch() -> None:
    """Keep administratively recognized history complete during normal recalculation."""
    from psb_app.services import training_certification as tc
    from psb_app.pages import qualification as q
    from psb_app.pages import training as training_page_module

    if not hasattr(tc, '_psb_pre_admin_sync_training_record'):
        tc._psb_pre_admin_sync_training_record = tc.sync_training_record
    original_sync = tc._psb_pre_admin_sync_training_record

    def recognized_sync_training_record(user_id: str, training_id: str) -> dict:
        recs = db_where('training_records', 'user_id = :uid AND training_id = :tid', (('uid', user_id), ('tid', training_id)))
        if not recs.empty and clean(recs.iloc[-1].get('administrative_recognition')).casefold() == 'yes':
            rec = recs.iloc[-1]
            snap = {
                'complete': True,
                'completion_percent': 100,
                'content_published': True,
                'requirements': [],
                'done': 1,
                'total': 1,
                'assessment_required': False,
                'assessment_done': True,
                'assessment_status': 'Administratively Recognized',
                'basis': clean(rec.get('recognition_basis')) or 'Administrative recognition',
            }
            db_update('training_records', 'record_id', clean(rec.get('record_id')), {
                'status': 'Completed', 'progress': 100, 'certificate_status': 'Issued',
                'completion_snapshot_json': json.dumps(snap), 'updated_on': now()
            })
            return snap
        return original_sync(user_id, training_id)

    tc.sync_training_record = recognized_sync_training_record

    def recognized_update_progress(record_id: str) -> dict:
        rec = _row('training_records', 'record_id = :rid', (('rid', record_id),))
        if not rec:
            return {'complete': False, 'completion_percent': 0}
        return recognized_sync_training_record(clean(rec.get('user_id')), clean(rec.get('training_id')))

    training_page_module.update_training_progress = recognized_update_progress

    if not hasattr(q, '_psb_pre_admin_sync_module_progress'):
        q._psb_pre_admin_sync_module_progress = q._sync_module_progress
    original_module_sync = q._psb_pre_admin_sync_module_progress

    def recognized_module_sync(user_id: str, module_id: str, assignment_id: str = '') -> dict:
        progress = db_where('qualification_module_progress', 'user_id = :uid AND module_id = :mid', (('uid', user_id), ('mid', module_id))) if table_exists('qualification_module_progress') else pd.DataFrame()
        if not progress.empty and clean(progress.iloc[-1].get('administrative_recognition')).casefold() == 'yes':
            row = progress.iloc[-1]
            return {
                'theory_status': 'Complete',
                'guided_practical_status': 'Complete',
                'trainer_gate_status': 'Ready',
                'independent_practical_status': 'Complete',
                'competency_status': 'Complete',
                'module_status': 'Complete',
                'completion_percent': 100,
                'completed_on': clean(row.get('completed_on')),
                'updated_on': clean(row.get('updated_on')),
                'administrative_recognition': 'Yes',
            }
        return original_module_sync(user_id, module_id, assignment_id)

    q._sync_module_progress = recognized_module_sync
