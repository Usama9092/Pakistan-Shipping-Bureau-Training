"""Controlled course completion, attestation and authorization integration.

This service turns qualification training into a deterministic gate:
content published -> required learning items completed -> MCQ (when required)
-> Trainer digital attestation -> qualification/module completion -> final
Authorization Certificate after the existing governance approvals.
"""
from __future__ import annotations

import json
from typing import Any

from psb_app.common import (
    PUBLIC_URL,
    actor_get,
    audit,
    can_action,
    clean,
    create_notification,
    datetime,
    db_all,
    db_insert,
    db_update,
    db_where,
    now,
    pd,
    secure_file_bytes,
    secure_file_url,
    st,
    table_exists,
    timedelta,
    today,
    uid,
)


def _yes(value: Any, default: bool = False) -> bool:
    text = clean(value).strip().casefold()
    if not text:
        return default
    return text in {'yes', 'y', 'true', '1', 'required', 'mandatory'}


def _user(user_id: str) -> dict:
    rows = db_where('users', 'user_id = :uid', (('uid', user_id),))
    return rows.iloc[-1].to_dict() if not rows.empty else {}


def _training(training_id: str) -> dict:
    rows = db_where('trainings', 'training_id = :tid', (('tid', training_id),))
    return rows.iloc[-1].to_dict() if not rows.empty else {}


def _record(user_id: str, training_id: str) -> dict:
    rows = db_where('training_records', 'user_id = :uid AND training_id = :tid', (('uid', user_id), ('tid', training_id)))
    return rows.iloc[-1].to_dict() if not rows.empty else {}


def _record_by_id(record_id: str) -> dict:
    rows = db_where('training_records', 'record_id = :rid', (('rid', record_id),))
    return rows.iloc[-1].to_dict() if not rows.empty else {}


def _progress_done(user_id: str, training_id: str, item_type: str, item_id: str) -> bool:
    if not table_exists('training_resource_progress'):
        return False
    rows = db_where(
        'training_resource_progress',
        'user_id = :uid AND training_id = :tid AND item_type = :it AND item_id = :iid AND status = :status',
        (('uid', user_id), ('tid', training_id), ('it', item_type), ('iid', item_id), ('status', 'Completed')),
    )
    return not rows.empty


def _mark_progress(user_id: str, training_id: str, item_type: str, item_id: str) -> None:
    if not table_exists('training_resource_progress'):
        return
    rows = db_where(
        'training_resource_progress',
        'user_id = :uid AND training_id = :tid AND item_type = :it AND item_id = :iid',
        (('uid', user_id), ('tid', training_id), ('it', item_type), ('iid', item_id)),
    )
    patch = {'status': 'Completed', 'completed_on': now(), 'updated_on': now()}
    if rows.empty:
        db_insert('training_resource_progress', {
            'resource_progress_id': uid('TRP'), 'user_id': user_id, 'training_id': training_id,
            'item_type': item_type, 'item_id': item_id, **patch,
        })
    else:
        db_update('training_resource_progress', 'resource_progress_id', str(rows.iloc[-1].get('resource_progress_id')), patch)


def _sequence_gate(user_id: str, training_id: str) -> tuple[bool, list[str]]:
    if not table_exists('qualification_module_training'):
        return True, []
    link = db_where('qualification_module_training','training_id = :tid AND active = :a',(('tid', training_id), ('a', 'Yes')))
    if link.empty:
        return True, []
    current = link.iloc[-1]
    module_id = clean(current.get('module_id'))
    seq = int(current.get('sequence_no') or 1)
    earlier = db_where('qualification_module_training','module_id = :mid AND active = :a',(('mid', module_id), ('a', 'Yes')))
    if earlier.empty:
        return True, []
    earlier = earlier[pd.to_numeric(earlier.get('sequence_no', pd.Series(dtype=int)), errors='coerce').fillna(0) < seq]
    if 'mandatory' in earlier.columns:
        earlier = earlier[earlier['mandatory'].astype(str).eq('Yes')]
    missing = []
    for _, row in earlier.sort_values('sequence_no').iterrows():
        tid = clean(row.get('training_id'))
        rec = _record(user_id, tid)
        if clean(rec.get('certificate_status')) != 'Issued':
            tr = _training(tid)
            missing.append(clean(tr.get('title')) or tid)
    return not missing, missing


def course_content_readiness(training_id: str) -> dict:
    tr = _training(training_id)
    if not tr:
        return {'ready': False, 'gaps': ['Training definition is missing.'], 'learning_items': 0, 'mcqs': 0}
    files = db_where('files', 'linked_table = :t AND linked_id = :id', (('t', 'trainings'), ('id', training_id))) if table_exists('files') else pd.DataFrame()
    resources = db_where('training_resources', 'training_id = :tid AND active = :a', (('tid', training_id), ('a', 'Yes'))) if table_exists('training_resources') else pd.DataFrame()
    sessions = db_where('training_live_sessions', 'training_id = :tid', (('tid', training_id),)) if table_exists('training_live_sessions') else pd.DataFrame()
    qbank = db_where('question_bank', 'training_id = :tid', (('tid', training_id),)) if table_exists('question_bank') else pd.DataFrame()
    link_count = sum(bool(clean(tr.get(k))) for k in ['slides_link', 'video_link', 'reference_link', 'scorm_package_link'])
    learning_items = len(files) + len(resources) + len(sessions) + link_count
    minimum_mcqs = int(tr.get('minimum_mcqs') or 5)
    gaps = []
    if learning_items <= 0:
        gaps.append('Add at least one controlled learning item: document, link, video/reference, SCORM or live session.')
    if _yes(tr.get('assessment_required'), True) and len(qbank) < minimum_mcqs:
        gaps.append(f'Publish at least {minimum_mcqs} MCQs for the assessment (currently {len(qbank)}).')
    return {'ready': not gaps,'gaps': gaps,'learning_items': learning_items,'files': len(files),'resources': len(resources),'sessions': len(sessions),'links': link_count,'mcqs': len(qbank),'minimum_mcqs': minimum_mcqs,'content_status': clean(tr.get('content_status')) or 'Draft'}


def pre_assessment_snapshot(user_id: str, training_id: str) -> dict:
    tr = _training(training_id); rec = _record(user_id, training_id); requirements = []
    if not tr or not rec:
        return {'complete': False, 'requirements': requirements, 'done': 0, 'total': 0, 'content_published': False}
    published = clean(tr.get('content_status')) == 'Published'
    def add(kind, item_id, title, required, done, detail=''):
        requirements.append({'kind':kind,'item_id':item_id,'title':title,'required':required,'done':bool(done),'detail':detail})
    for title, field, required_field, done in [
        ('Slides','slides_link','slides_required',clean(rec.get('slides_opened'))=='Yes'),
        ('Video','video_link','video_required',clean(rec.get('video_opened'))=='Yes'),
        ('Reference','reference_link','reference_required',clean(rec.get('reference_opened'))=='Yes'),
        ('LMS / SCORM','scorm_package_link','scorm_required',clean(rec.get('lms_completed'))=='Yes')]:
        if clean(tr.get(field)): add('Link',field,title,_yes(tr.get(required_field),True),done)
    files = db_where('files','linked_table = :t AND linked_id = :id',(('t','trainings'),('id',training_id))) if table_exists('files') else pd.DataFrame()
    if not files.empty:
        if 'sequence_no' in files.columns: files=files.sort_values('sequence_no')
        for _,f in files.iterrows():
            fid=clean(f.get('file_id')) or clean(f.get('file_name'))
            add('File',fid,clean(f.get('file_name')) or 'Training document',_yes(f.get('mandatory'),True),_progress_done(user_id,training_id,'File',fid),clean(f.get('file_ext')))
    resources = db_where('training_resources','training_id = :tid AND active = :a',(('tid',training_id),('a','Yes'))) if table_exists('training_resources') else pd.DataFrame()
    if not resources.empty:
        if 'sequence_no' in resources.columns: resources=resources.sort_values('sequence_no')
        for _,r in resources.iterrows():
            rid=clean(r.get('resource_id'))
            add('Resource',rid,clean(r.get('title')) or clean(r.get('resource_type')) or 'Resource',_yes(r.get('mandatory'),True),_progress_done(user_id,training_id,'Resource',rid),clean(r.get('resource_type')))
    sessions = db_where('training_live_sessions','training_id = :tid',(('tid',training_id),)) if table_exists('training_live_sessions') else pd.DataFrame()
    required_sessions=sessions[sessions.get('attendance_required',pd.Series(dtype=str)).astype(str).eq('Yes')] if not sessions.empty else sessions
    for _,ss in required_sessions.iterrows():
        sid=clean(ss.get('session_id')); att=db_where('training_session_attendance','session_id = :sid AND user_id = :uid',(('sid',sid),('uid',user_id))) if table_exists('training_session_attendance') else pd.DataFrame(); status=clean(att.iloc[-1].get('attendance_status')) if not att.empty else 'Not Marked'
        add('Live Session',sid,clean(ss.get('session_title')) or 'Required live session',True,status in {'Present','Recording Viewed'},status)
    if _yes(tr.get('attendance_required'),False) and required_sessions.empty:
        status=clean(rec.get('live_attendance')); add('Attendance','course-attendance','Course attendance',True,status in {'Present','Recording Viewed'},status or 'Not Marked')
    required=[x for x in requirements if x['required']]; done=sum(1 for x in required if x['done'])
    return {'complete':bool(published and (not required or done==len(required))),'requirements':requirements,'done':done,'total':len(required),'content_published':published}


def training_completion_snapshot(user_id: str, training_id: str) -> dict:
    tr=_training(training_id); rec=_record(user_id,training_id); pre=pre_assessment_snapshot(user_id,training_id)
    assessment_required=_yes(tr.get('assessment_required'),True); assessment_done=(not assessment_required) or clean(rec.get('test_status'))=='Passed'
    checks=[x['done'] for x in pre['requirements'] if x['required']]+[assessment_done]; total=len(checks); done=sum(bool(x) for x in checks)
    complete=bool(pre['content_published'] and pre['complete'] and assessment_done)
    return {**pre,'assessment_required':assessment_required,'assessment_done':assessment_done,'assessment_status':clean(rec.get('test_status')) or ('Not Required' if not assessment_required else 'Not Started'),'complete':complete,'completion_percent':100 if complete else int(round(100*done/total)) if total else 0}


def sync_training_record(user_id: str, training_id: str) -> dict:
    rec=_record(user_id,training_id); tr=_training(training_id)
    if not rec or not tr: return {'complete':False,'completion_percent':0}
    snap=training_completion_snapshot(user_id,training_id); existing_cert=clean(rec.get('certificate_status'))=='Issued'
    status='Pending' if not snap['content_published'] else 'Completed' if snap['complete'] else 'In Progress' if snap['completion_percent']>0 else 'Pending'
    attestation_required=_yes(tr.get('attestation_required'),_yes(tr.get('certificate_required'),True)); cert_status=clean(rec.get('certificate_status')) or 'Not Issued'
    if snap['complete'] and attestation_required and not existing_cert: cert_status='Pending Trainer Signature'
    elif snap['complete'] and not attestation_required: cert_status='Not Required'
    db_update('training_records','record_id',clean(rec.get('record_id')),{'status':status,'progress':int(snap['completion_percent']),'completed_on':clean(rec.get('completed_on')) or (now() if snap['complete'] else ''),'certificate_status':cert_status,'completion_snapshot_json':json.dumps(snap,default=str),'updated_on':now()})
    return snap


def update_training_progress(record_id: str) -> dict:
    rec=_record_by_id(record_id)
    return sync_training_record(clean(rec.get('user_id')),clean(rec.get('training_id'))) if rec else {'complete':False,'completion_percent':0}


def _assigned_trainer(user: dict, tr: dict) -> tuple[str,str]:
    return (clean(user.get('trainer_id')) or clean(tr.get('trainer_id')), clean(user.get('trainer_name')) or clean(tr.get('trainer_name')) or 'Assigned Trainer')


def issue_training_attestation(record_id: str, actor: dict, requested_certificate_id: str='') -> str:
    rec=_record_by_id(record_id)
    if not rec: raise ValueError('Training record not found.')
    user_id=clean(rec.get('user_id')); training_id=clean(rec.get('training_id')); tr=_training(training_id); user=_user(user_id); snap=sync_training_record(user_id,training_id)
    if not snap.get('complete'): raise ValueError('Training attestation is locked until all mandatory learning items and the required assessment are complete.')
    trainer_id,trainer_name=_assigned_trainer(user,tr); actor_id=clean(actor_get(actor,'user_id')); actor_name=clean(actor_get(actor,'name')); privileged=can_action(actor,'Training','Manage','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
    if trainer_id and actor_id!=trainer_id and not privileged: raise ValueError('Only the learner’s assigned Trainer (or authorized organization administrator) may digitally sign this attestation.')
    existing=db_where('training_attestation_certificates','record_id = :rid AND status = :status',(('rid',record_id),('status','Valid'))) if table_exists('training_attestation_certificates') else pd.DataFrame()
    if not existing.empty:
        cert_id=clean(existing.iloc[-1].get('certificate_id')); db_update('training_records','record_id',record_id,{'certificate_status':'Issued','certificate_id':cert_id,'certificate_issued_on':clean(existing.iloc[-1].get('issue_date')),'certificate_issued_by':trainer_name,'certificate_link':clean(existing.iloc[-1].get('verification_url')),'updated_on':now()}); return cert_id
    cert_id=requested_certificate_id.strip() or uid('ATT'); issue_date=today(); module_id=clean(tr.get('module_id')); module_code=''; module_name=clean(rec.get('training_title')) or clean(tr.get('title'))
    if module_id and table_exists('qualification_modules'):
        m=db_where('qualification_modules','module_id = :mid',(('mid',module_id),))
        if not m.empty: module_code=clean(m.iloc[-1].get('module_code')); module_name=clean(m.iloc[-1].get('module_name')) or module_name
    verification_url=f'{PUBLIC_URL}/?verify={cert_id}'
    payload={'certificate_id':cert_id,'record_id':record_id,'training_id':training_id,'user_id':user_id,'name':clean(rec.get('name')) or clean(user.get('name')),'training_title':clean(tr.get('title')),'module_code':module_code,'module_name':module_name,'conducted_on':clean(rec.get('completed_on')) or issue_date,'issue_date':issue_date,'trainer_id':trainer_id or actor_id,'trainer_name':trainer_name or actor_name,'trainer_signed_on':now(),'ceo_name':'Cdre Dr. M Saeed Khalid SI(M)','document_code':'PSB-PTQ20-F03','revision_no':'01','revision_date':'11-02-2026','verification_url':verification_url,'status':'Valid','created_on':now(),'updated_on':now()}
    db_insert('training_attestation_certificates',payload); db_update('training_records','record_id',record_id,{'certificate_status':'Issued','certificate_id':cert_id,'certificate_issued_on':issue_date,'certificate_issued_by':trainer_name or actor_name,'certificate_link':verification_url,'updated_on':now()})
    try: create_notification(user_id,'Training Attestation Issued',f'{clean(tr.get("title"))} · {cert_id}','Training')
    except Exception: pass
    audit('Training Attestation Issued',f'{cert_id} — {clean(rec.get("name"))} — {clean(tr.get("title"))}',actor=actor,entity_type='training_attestation_certificates',entity_id=cert_id,reason='All controlled learning requirements complete; digitally signed by assigned Trainer')
    return cert_id


def _show_attestation(user_id: str, training_id: str) -> None:
    if not table_exists('training_attestation_certificates'): return
    certs=db_where('training_attestation_certificates','user_id = :uid AND training_id = :tid AND status = :status',(('uid',user_id),('tid',training_id),('status','Valid')))
    if certs.empty: return
    cert=certs.iloc[-1]; from psb_app.services.certificate_service import build_training_attestation; html,_=build_training_attestation(cert)
    st.success(f"Digital Training Course Attestation issued · {clean(cert.get('certificate_id'))}"); c1,c2=st.columns(2); c1.download_button('Download PSB-PTQ20-F03 Attestation',data=html,file_name=f"{clean(cert.get('certificate_id'))}.html",mime='text/html',use_container_width=True)
    if clean(cert.get('verification_url')): c2.link_button('Verify Certificate',clean(cert.get('verification_url')),use_container_width=True)


def enhanced_trainee_training(actor, tid: str) -> None:
    from psb_app.pages import training as t
    user_id=clean(actor_get(actor,'user_id')); rec=_record(user_id,tid); tr=_training(tid)
    if not rec: st.warning('Training not assigned.'); return
    if not tr: st.warning('Training details not found.'); return
    sequence_ok,earlier=_sequence_gate(user_id,tid); st.subheader(clean(tr.get('title'))); sync_training_record(user_id,tid); rec=_record(user_id,tid)
    c1,c2,c3,c4=st.columns(4); c1.metric('Progress',f"{int(rec.get('progress') or 0)}%"); c2.metric('Course Content',clean(tr.get('content_status')) or 'Draft'); c3.metric('Assessment',clean(rec.get('test_status')) or 'Not Started'); c4.metric('Attestation',clean(rec.get('certificate_status')) or 'Not Issued')
    st.caption(f"Trainer: {clean(_assigned_trainer(_user(user_id),tr)[1])} · Due: {clean(rec.get('due_date')) or 'Not set'}")
    if not sequence_ok:
        st.warning('This training is locked until the earlier mandatory training(s) in this module are completed and attested.'); [st.write('• '+x) for x in earlier]; return
    if clean(tr.get('content_status'))!='Published': st.info('The Trainer is preparing this course. Documents/links/MCQs must be published before you can start controlled completion.'); return
    st.markdown('### 1. Controlled Learning Material')
    for title,field,req_field,rec_field in [('Slides','slides_link','slides_required','slides_opened'),('Video','video_link','video_required','video_opened'),('Reference','reference_link','reference_required','reference_opened'),('LMS / SCORM','scorm_package_link','scorm_required','lms_completed')]:
        url=clean(tr.get(field))
        if not url: continue
        required=_yes(tr.get(req_field),True); done=clean(rec.get(rec_field))=='Yes'; a,b,c=st.columns([4,1,1]); a.link_button(f'Open {title}',url,key=f'open_{field}_{tid}_{user_id}'); b.caption('Mandatory' if required else 'Optional')
        if done: c.success('Completed')
        elif c.button('Complete',key=f'complete_{field}_{tid}_{user_id}'): db_update('training_records','record_id',clean(rec.get('record_id')),{rec_field:'Yes','updated_on':now()}); sync_training_record(user_id,tid); st.rerun()
    files=db_where('files','linked_table = :t AND linked_id = :id',(('t','trainings'),('id',tid))) if table_exists('files') else pd.DataFrame()
    if not files.empty:
        st.markdown('#### Documents / Files'); files=files.sort_values('sequence_no') if 'sequence_no' in files.columns else files
        for _,f in files.iterrows():
            file_name=clean(f.get('file_name')); fid=clean(f.get('file_id')) or file_name; required=_yes(f.get('mandatory'),True); url=secure_file_url(f.to_dict()); file_bytes=secure_file_bytes(f.to_dict()) if not url else None; a,b,c=st.columns([4,1,1])
            if url: a.link_button(f'Open {file_name}',url,key=f'open_file_{fid}_{user_id}')
            elif file_bytes is not None: a.download_button(f'Download {file_name}',data=file_bytes,file_name=file_name,key=f'dl_file_{fid}_{user_id}')
            else: a.write(file_name)
            b.caption('Mandatory' if required else 'Optional')
            if _progress_done(user_id,tid,'File',fid): c.success('Completed')
            elif c.button('Mark Read',key=f'done_file_{fid}_{user_id}'): _mark_progress(user_id,tid,'File',fid); sync_training_record(user_id,tid); st.rerun()
    resources=db_where('training_resources','training_id = :tid AND active = :a',(('tid',tid),('a','Yes'))) if table_exists('training_resources') else pd.DataFrame()
    if not resources.empty:
        st.markdown('#### Videos, Rules, Procedures & Other References'); resources=resources.sort_values('sequence_no') if 'sequence_no' in resources.columns else resources
        for _,r in resources.iterrows():
            rid=clean(r.get('resource_id')); required=_yes(r.get('mandatory'),True); url=clean(r.get('url')); a,b,c=st.columns([4,1,1]); label=f"{clean(r.get('resource_type'))}: {clean(r.get('title'))}"
            if url: a.link_button(label,url,key=f'open_res_{rid}_{user_id}')
            else: a.write(label)
            if clean(r.get('rule_reference')): a.caption(clean(r.get('rule_reference')))
            b.caption('Mandatory' if required else 'Optional')
            if _progress_done(user_id,tid,'Resource',rid): c.success('Completed')
            elif c.button('Reviewed',key=f'done_res_{rid}_{user_id}'): _mark_progress(user_id,tid,'Resource',rid); sync_training_record(user_id,tid); st.rerun()
    sessions=db_where('training_live_sessions','training_id = :tid',(('tid',tid),)) if table_exists('training_live_sessions') else pd.DataFrame()
    if not sessions.empty:
        st.markdown('#### Live / Online Sessions')
        for _,ss in sessions.iterrows():
            sid=clean(ss.get('session_id')); required=clean(ss.get('attendance_required'))=='Yes'; att=db_where('training_session_attendance','session_id = :sid AND user_id = :uid',(('sid',sid),('uid',user_id))) if table_exists('training_session_attendance') else pd.DataFrame(); status=clean(att.iloc[-1].get('attendance_status')) if not att.empty else 'Not Marked'; st.write(f"**{clean(ss.get('session_title'))}** · {clean(ss.get('session_date'))} {clean(ss.get('start_time'))} · {'Mandatory' if required else 'Optional'} · Attendance: **{status}**")
            if clean(ss.get('meeting_link')): st.link_button('Join Session',clean(ss.get('meeting_link')),key=f'join_{sid}_{user_id}')
    pre=pre_assessment_snapshot(user_id,tid); required_rows=[r for r in pre['requirements'] if r['required']]
    if required_rows:
        st.markdown('#### Completion Checklist'); st.dataframe(pd.DataFrame([{'Requirement':r['title'],'Type':r['kind'],'Status':'Complete' if r['done'] else 'Pending','Detail':r['detail']} for r in required_rows]),use_container_width=True,hide_index=True)
    if not pre['complete']: st.warning(f"Complete all mandatory learning requirements before the assessment. {pre['done']}/{pre['total']} completed."); return
    st.markdown('### 2. Timed MCQ Assessment')
    if not _yes(tr.get('assessment_required'),True):
        st.info('No MCQ assessment is required for this course.'); sync_training_record(user_id,tid); _show_attestation(user_id,tid)
        if clean(_record(user_id,tid).get('certificate_status'))!='Issued': st.success('Course requirements complete. Awaiting the assigned Trainer’s digital signature on the attestation certificate.')
        return
    qs=db_where('question_bank','training_id = :tid',(('tid',tid),)) if table_exists('question_bank') else pd.DataFrame()
    if qs.empty: st.warning('The Trainer has not yet published the MCQ assessment.'); return
    rec=_record(user_id,tid)
    if clean(rec.get('test_status'))=='Passed':
        st.success(f"Assessment passed · Score {rec.get('score',0)}%"); sync_training_record(user_id,tid); _show_attestation(user_id,tid)
        if clean(_record(user_id,tid).get('certificate_status'))!='Issued': st.success('Training completed. Your attestation is awaiting the assigned Trainer’s digital signature.')
        return
    history=db_where('assessment_history','user_id = :uid AND training_id = :tid',(('uid',user_id),('tid',tid))) if table_exists('assessment_history') else pd.DataFrame(); attempts=len(history) if not history.empty else 0
    cfg=db_where('training_assessment_configs','training_id = :tid AND active = :a',(('tid',tid),('a','Yes'))) if table_exists('training_assessment_configs') else pd.DataFrame(); conf=cfg.iloc[-1].to_dict() if not cfg.empty else {'duration_minutes':30,'passing_score':int(tr.get('passing_marks') or 70),'max_attempts':int(tr.get('max_attempts') or 2),'show_result_immediately':'Yes'}
    duration=int(conf.get('duration_minutes') or 30); max_attempts=int(conf.get('max_attempts') or 2); pass_mark=int(conf.get('passing_score') or tr.get('passing_marks') or 70)
    if attempts>=max_attempts: st.error('Maximum assessment attempts have been used. Contact your Trainer for a controlled reassessment decision.'); return
    window_ok,window_message=t._assessment_window_open(conf); inprog=db_where('training_assessment_sessions','user_id = :uid AND training_id = :tid AND status = :status',(('uid',user_id),('tid',tid),('status','In Progress'))) if table_exists('training_assessment_sessions') else pd.DataFrame()
    if inprog.empty and not window_ok: st.info(window_message); return
    session=inprog.iloc[-1].to_dict() if not inprog.empty else {}
    if not session:
        st.info(f"Questions: {len(qs)} · Duration: {duration} minutes · Pass mark: {pass_mark}% · Attempts remaining: {max_attempts-attempts}")
        if st.button('Start Timed Assessment',key=f'controlled_start_{tid}_{user_id}',type='primary'):
            started=datetime.now(); expires=started+timedelta(minutes=duration); sid=uid('TAS'); db_insert('training_assessment_sessions',{'assessment_session_id':sid,'user_id':user_id,'training_id':tid,'attempt_no':attempts+1,'started_at':started.strftime('%Y-%m-%d %H:%M:%S'),'expires_at':expires.strftime('%Y-%m-%d %H:%M:%S'),'submitted_at':'','status':'In Progress','score':0,'result':'','correct_count':0,'question_count':len(qs),'created_on':now(),'updated_on':now()}); audit('Timed Training Assessment Started',clean(tr.get('title')),actor=actor,entity_type='training_assessment_sessions',entity_id=sid,reason=f'{duration} minute controlled assessment'); st.rerun()
        return
    expires=datetime.strptime(str(session.get('expires_at')),'%Y-%m-%d %H:%M:%S'); remaining=max(0,int((expires-datetime.now()).total_seconds()))
    if remaining<=0:
        db_update('training_assessment_sessions','assessment_session_id',session['assessment_session_id'],{'submitted_at':now(),'status':'Submitted','score':0,'result':'Failed','correct_count':0,'question_count':len(qs),'updated_on':now()}); db_insert('assessment_history',{'assessment_id':uid('ASM'),'user_id':user_id,'name':actor_get(actor,'name'),'training_id':tid,'training_title':clean(tr.get('title')),'attempt_no':int(session.get('attempt_no') or attempts+1),'score':0,'result':'Failed','attempted_on':now(),'next_retest_allowed':'','remarks':'Assessment auto-submitted because the server-side timer expired.'}); db_update('training_records','record_id',clean(rec.get('record_id')),{'score':0,'test_status':'Failed','remarks':'Timed assessment expired before submission','updated_on':now()}); sync_training_record(user_id,tid); st.error('Time expired. The assessment was automatically submitted as failed.'); st.rerun()
    mins,secs=divmod(remaining,60); st.warning(f'⏱ Time Remaining: {mins:02d}:{secs:02d}'); question_rows=t._stable_question_rows(qs,str(session.get('assessment_session_id')),conf.get('randomize_questions','Yes'))
    with st.form(f'controlled_assessment_{tid}_{user_id}_{session.get("assessment_session_id")}'):
        answers={}
        for i,qrow in enumerate(question_rows,1):
            st.markdown(f"**Q{i}. {qrow['question']}**"); opts=t._stable_options(qrow,str(session.get('assessment_session_id')),conf.get('randomize_answers','Yes')); answers[qrow['question_id']]=st.radio('Select',opts,key=f"controlled_{session.get('assessment_session_id')}_{qrow['question_id']}",label_visibility='collapsed')
        submit=st.form_submit_button('Submit Assessment')
    if submit:
        if datetime.now()>expires: db_update('training_assessment_sessions','assessment_session_id',session['assessment_session_id'],{'submitted_at':now(),'status':'Submitted','score':0,'result':'Failed','updated_on':now()}); st.error('The timer expired before submission reached the server.'); st.rerun()
        correct=sum(1 for qrow in question_rows if answers.get(qrow['question_id'])==qrow['correct_answer']); score=round(correct/len(question_rows)*100,2); result='Passed' if score>=pass_mark else 'Failed'; db_update('training_assessment_sessions','assessment_session_id',session['assessment_session_id'],{'submitted_at':now(),'status':'Submitted','score':score,'result':result,'correct_count':correct,'question_count':len(qs),'updated_on':now()}); db_insert('assessment_history',{'assessment_id':uid('ASM'),'user_id':user_id,'name':actor_get(actor,'name'),'training_id':tid,'training_title':clean(tr.get('title')),'attempt_no':int(session.get('attempt_no') or attempts+1),'score':score,'result':result,'attempted_on':now(),'next_retest_allowed':'','remarks':f'Correct {correct}/{len(question_rows)} · controlled timed assessment'}); db_update('training_records','record_id',clean(rec.get('record_id')),{'score':score,'test_status':result,'certificate_status':'Pending Trainer Signature' if result=='Passed' else 'Not Issued','certificate_link':'','remarks':f'Correct {correct}/{len(question_rows)}','last_assessment_on':now(),'updated_on':now()}); sync_training_record(user_id,tid); audit('Timed Training Assessment Submitted',clean(tr.get('title')),actor=actor,entity_type='training_assessment_sessions',entity_id=session['assessment_session_id'],reason=f'{result} {score}%')
        if result=='Passed': st.success(f'Passed: {score}%. Training is complete and awaiting Trainer digital attestation.')
        else: st.error(f'Failed: {score}%')
        st.rerun()


def trainer_course_control_panel(actor: dict) -> None:
    role=clean(actor_get(actor,'role')); allowed=role=='Trainer' or can_action(actor,'Training','Manage','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
    if not allowed: return
    actor_id=clean(actor_get(actor,'user_id')); users=db_all('users'); trainings=db_all('trainings'); records=db_all('training_records')
    if trainings.empty: return
    assigned_ids=set()
    if role=='Trainer':
        assigned_ids=set(users[users.get('trainer_id',pd.Series('',index=users.index)).astype(str).eq(actor_id)].get('user_id',pd.Series(dtype=str)).astype(str).tolist()) if not users.empty else set(); training_ids=set(records[records.get('user_id',pd.Series(dtype=str)).astype(str).isin(assigned_ids)].get('training_id',pd.Series(dtype=str)).astype(str).tolist()) if not records.empty else set(); own=set(trainings[trainings.get('trainer_id',pd.Series('',index=trainings.index)).astype(str).eq(actor_id)].get('training_id',pd.Series(dtype=str)).astype(str).tolist()); training_ids|=own; scoped=trainings[trainings['training_id'].astype(str).isin(training_ids)] if training_ids else trainings.iloc[0:0]
    else: scoped=trainings
    with st.expander('Controlled Course Content, Publication & Digital Attestations',expanded=False):
        st.caption('Trainer adds PPT/PPTX, PDF, Word, Excel, videos/links, rules/references, live sessions and MCQs in the Qualification Workspace. This control makes those items mandatory/optional, publishes the course, and digitally signs the learner attestation after completion.')
        if scoped.empty: st.info('No qualification training is currently linked to your assigned learners. Assign a qualification path first.'); return
        labels=(scoped['title'].astype(str)+' — '+scoped['training_id'].astype(str)).tolist(); chosen=st.selectbox('Controlled training',labels,key='cert_control_training'); tid=chosen.rsplit(' — ',1)[-1]; tr=scoped[scoped['training_id'].astype(str).eq(tid)].iloc[-1]; readiness=course_content_readiness(tid)
        a,b,c,d=st.columns(4); a.metric('Content',clean(tr.get('content_status')) or 'Draft'); b.metric('Learning Items',readiness['learning_items']); c.metric('MCQs',f"{readiness['mcqs']}/{readiness['minimum_mcqs'] if _yes(tr.get('assessment_required'),True) else 0}"); d.metric('Ready to Publish','Yes' if readiness['ready'] else 'No')
        st.info('Accepted controlled documents include PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX, CSV/TXT and approved media/images. Uploads, resources, live sessions and MCQ authoring remain in the existing Theoretical Training & MCQ workspace below.')
        st.markdown('#### Links & Requirement Rules')
        with st.form(f'controlled_links_{tid}'):
            x1,x2=st.columns(2); slides=x1.text_input('Slides URL',value=clean(tr.get('slides_link'))); slides_req=x2.checkbox('Slides mandatory',value=_yes(tr.get('slides_required'),True)); video=x1.text_input('Video URL',value=clean(tr.get('video_link'))); video_req=x2.checkbox('Video mandatory',value=_yes(tr.get('video_required'),True)); reference=x1.text_input('Reference / Rule URL',value=clean(tr.get('reference_link'))); reference_req=x2.checkbox('Reference mandatory',value=_yes(tr.get('reference_required'),True)); scorm=x1.text_input('LMS / SCORM URL',value=clean(tr.get('scorm_package_link'))); scorm_req=x2.checkbox('LMS / SCORM mandatory',value=_yes(tr.get('scorm_required'),True)); min_mcq=x1.number_input('Minimum published MCQs',1,100,int(tr.get('minimum_mcqs') or 5)); attendance_req=x2.checkbox('Course attendance mandatory when no specific live-session attendance rule exists',value=_yes(tr.get('attendance_required'),False)); save=st.form_submit_button('Save Controlled Content Rules',type='primary')
        if save:
            db_update('trainings','training_id',tid,{'slides_link':slides.strip(),'video_link':video.strip(),'reference_link':reference.strip(),'scorm_package_link':scorm.strip(),'slides_required':'Yes' if slides_req else 'No','video_required':'Yes' if video_req else 'No','reference_required':'Yes' if reference_req else 'No','scorm_required':'Yes' if scorm_req else 'No','minimum_mcqs':int(min_mcq),'attendance_required':'Yes' if attendance_req else 'No','content_status':'Draft','attestation_required':'Yes','certificate_required':'Yes','updated_on':now()}); audit('Training Content Rules Updated',clean(tr.get('title')),actor=actor,entity_type='trainings',entity_id=tid,reason='Controlled completion requirements changed; course returned to Draft for republishing'); st.success('Content rules saved. Course returned to Draft and must be republished after validation.'); st.rerun()
        files=db_where('files','linked_table = :t AND linked_id = :id',(('t','trainings'),('id',tid))) if table_exists('files') else pd.DataFrame()
        if not files.empty:
            st.markdown('#### Uploaded Document Requirement'); st.dataframe(files[[c for c in ['file_name','file_ext','mandatory','sequence_no','review_status'] if c in files.columns]],use_container_width=True,hide_index=True); fmap={f"{clean(r.get('file_name'))} — {clean(r.get('file_id'))}":clean(r.get('file_id')) for _,r in files.iterrows()}; fl=st.selectbox('Document to configure',list(fmap),key=f'file_req_{tid}'); fid=fmap[fl]; fr=files[files['file_id'].astype(str).eq(fid)].iloc[-1]; fc1,fc2,fc3=st.columns([2,1,1]); mandatory=fc1.selectbox('Requirement',['Mandatory','Optional'],index=0 if _yes(fr.get('mandatory'),True) else 1,key=f'file_mand_{tid}'); seq=fc2.number_input('Sequence',1,999,int(fr.get('sequence_no') or 1),key=f'file_seq_{tid}')
            if fc3.button('Save Document Rule',key=f'save_file_req_{tid}'): db_update('files','file_id',fid,{'mandatory':'Yes' if mandatory=='Mandatory' else 'No','sequence_no':int(seq),'updated_on':now()}); db_update('trainings','training_id',tid,{'content_status':'Draft','updated_on':now()}); st.success('Document requirement saved. Republish the course.'); st.rerun()
        resources=db_where('training_resources','training_id = :tid AND active = :a',(('tid',tid),('a','Yes'))) if table_exists('training_resources') else pd.DataFrame()
        if not resources.empty:
            st.markdown('#### Resource Requirement'); st.dataframe(resources[[c for c in ['resource_type','title','mandatory','sequence_no','rule_reference'] if c in resources.columns]],use_container_width=True,hide_index=True); rmap={f"{clean(r.get('title'))} — {clean(r.get('resource_id'))}":clean(r.get('resource_id')) for _,r in resources.iterrows()}; rl=st.selectbox('Resource to configure',list(rmap),key=f'res_req_{tid}'); rid=rmap[rl]; rr=resources[resources['resource_id'].astype(str).eq(rid)].iloc[-1]; rc1,rc2,rc3=st.columns([2,1,1]); rmand=rc1.selectbox('Requirement',['Mandatory','Optional'],index=0 if _yes(rr.get('mandatory'),True) else 1,key=f'res_mand_{tid}'); rseq=rc2.number_input('Sequence',1,999,int(rr.get('sequence_no') or 1),key=f'res_seq_{tid}')
            if rc3.button('Save Resource Rule',key=f'save_res_req_{tid}'): db_update('training_resources','resource_id',rid,{'mandatory':'Yes' if rmand=='Mandatory' else 'No','sequence_no':int(rseq),'updated_on':now()}); db_update('trainings','training_id',tid,{'content_status':'Draft','updated_on':now()}); st.success('Resource requirement saved. Republish the course.'); st.rerun()
        readiness=course_content_readiness(tid)
        for gap in readiness['gaps']: st.warning(gap)
        if clean(tr.get('content_status'))=='Published':
            if st.button('Return Course to Draft',key=f'unpublish_{tid}'): db_update('trainings','training_id',tid,{'content_status':'Draft','updated_on':now()}); audit('Training Unpublished',clean(tr.get('title')),actor=actor,entity_type='trainings',entity_id=tid,reason='Trainer reopened controlled content'); st.rerun()
        elif st.button('Validate & Publish Controlled Training',key=f'publish_{tid}',type='primary',disabled=not readiness['ready']): db_update('trainings','training_id',tid,{'content_status':'Published','certificate_required':'Yes','attestation_required':'Yes','updated_on':now()}); audit('Training Published',clean(tr.get('title')),actor=actor,entity_type='trainings',entity_id=tid,reason=f"{readiness['learning_items']} learning items and {readiness['mcqs']} MCQs validated"); st.success('Training published. Learners can now complete it in the controlled sequence.'); st.rerun()
        st.markdown('#### Attestation Signature Queue'); assigned=records[records.get('training_id',pd.Series(dtype=str)).astype(str).eq(tid)] if not records.empty else pd.DataFrame()
        if role=='Trainer' and not assigned.empty: assigned=assigned[assigned.get('user_id',pd.Series(dtype=str)).astype(str).isin(assigned_ids)]
        if assigned.empty: st.info('No assigned learner records for this training.')
        else:
            queue=[]
            for _,row in assigned.iterrows():
                sync_training_record(clean(row.get('user_id')),tid); fresh=_record(clean(row.get('user_id')),tid); queue.append({'Record ID':fresh.get('record_id'),'Learner':fresh.get('name'),'Progress':fresh.get('progress'),'Status':fresh.get('status'),'Assessment':fresh.get('test_status'),'Attestation':fresh.get('certificate_status')})
            qdf=pd.DataFrame(queue); st.dataframe(qdf,use_container_width=True,hide_index=True); pending=qdf[(qdf['Status']=='Completed') & (qdf['Attestation']!='Issued')]
            if not pending.empty:
                options=(pending['Learner'].astype(str)+' — '+pending['Record ID'].astype(str)).tolist(); pick=st.selectbox('Completed learner awaiting signature',options,key=f'attest_queue_{tid}'); rid=pick.rsplit(' — ',1)[-1]; declaration=st.checkbox('I confirm this learner completed all controlled requirements and I am digitally signing PSB-PTQ20-F03 as the assigned Trainer.',key=f'attest_decl_{tid}')
                if st.button('Digitally Sign & Issue Attestation',key=f'issue_attest_{tid}',type='primary',disabled=not declaration):
                    try: cid=issue_training_attestation(rid,actor); st.success(f'Attestation issued: {cid}'); st.rerun()
                    except Exception as exc: st.error(str(exc))


def certificate_center_addon(actor: dict) -> None:
    if not table_exists('training_attestation_certificates'): return
    certs=db_all('training_attestation_certificates')
    if certs.empty: return
    actor_id=clean(actor_get(actor,'user_id')); role=clean(actor_get(actor,'role')); enterprise=can_action(actor,'Authorization','Manage','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
    if not enterprise:
        certs=certs[certs.get('trainer_id',pd.Series(dtype=str)).astype(str).eq(actor_id)] if role=='Trainer' else certs[certs.get('user_id',pd.Series(dtype=str)).astype(str).eq(actor_id)]
    if certs.empty: return
    st.subheader('Training Course Attestations · PSB-PTQ20-F03'); st.caption('Each attestation is issued only after all mandatory course material and the configured assessment are complete, then digitally signed by the assigned Trainer with the CEO signature block on the left.'); st.dataframe(certs[[c for c in ['certificate_id','name','training_title','module_code','module_name','issue_date','trainer_name','status'] if c in certs.columns]].sort_values('issue_date',ascending=False),use_container_width=True,hide_index=True); ids=certs['certificate_id'].astype(str).tolist(); chosen=st.selectbox('Attestation certificate',['—']+ids,key='attestation_center_select')
    if chosen!='—':
        row=certs[certs['certificate_id'].astype(str).eq(chosen)].iloc[-1]; from psb_app.services.certificate_service import build_training_attestation; html,_=build_training_attestation(row); c1,c2=st.columns(2); c1.download_button('Download Digital Attestation',data=html,file_name=f'{chosen}.html',mime='text/html',use_container_width=True)
        if clean(row.get('verification_url')): c2.link_button('Public Verification',clean(row.get('verification_url')),use_container_width=True)


def _qualification_theory_status(user_id: str, module_id: str):
    from psb_app.pages import qualification as q
    mts=q._module_trainings(module_id)
    if mts.empty: return True,0,0
    mandatory=mts[mts.get('mandatory',pd.Series(dtype=str)).astype(str).eq('Yes')] if 'mandatory' in mts.columns else mts; total=len(mandatory); complete=0
    for _,mt in mandatory.iterrows():
        tid=clean(mt.get('training_id')); rec=_record(user_id,tid)
        if not rec: continue
        snap=sync_training_record(user_id,tid); tr=_training(tid); attestation_required=_yes(tr.get('attestation_required'),_yes(tr.get('certificate_required'),True)); attestation_ok=(clean(_record(user_id,tid).get('certificate_status'))=='Issued') if attestation_required else True
        if snap.get('complete') and attestation_ok: complete+=1
    return complete>=total,complete,total


def _enhanced_authorization_issue(req, actor):
    from psb_app.pages import authorization as a
    original=getattr(a,'_psb_original_issue_authorization_certificate',None)
    if original is None: raise RuntimeError('Authorization certificate issuer is not initialized.')
    enriched=req.copy(); user_id=clean(enriched.get('user_id')); user=_user(user_id); enriched['trainer_name']=clean(user.get('trainer_name')) or clean(enriched.get('tutor_signature')) or 'Assigned Trainer'; enriched['trainer_id']=clean(user.get('trainer_id')); enriched['ceo_name']='Cdre (R) Dr. M Saeed Khalid'
    try:
        from psb_app.pages import qualification as q
        if q._assignment(user_id):
            ready,snapshot=q._qualification_readiness(user_id)
            if not ready: raise ValueError(f"Authorization certificate is locked: qualification modules complete {snapshot.get('modules_complete',0)}/{snapshot.get('modules_required',0)}.")
    except ValueError: raise
    except Exception: pass
    modules=[]
    if table_exists('qualification_module_progress') and table_exists('qualification_modules'):
        prog=db_where('qualification_module_progress','user_id = :uid AND module_status = :s',(('uid',user_id),('s','Complete'))); qmods=db_all('qualification_modules')
        if not prog.empty and not qmods.empty:
            merged=prog.merge(qmods[['module_id','module_code','module_name']],on='module_id',how='left')
            for _,m in merged.iterrows():
                label=f"{clean(m.get('module_code'))} — {clean(m.get('module_name'))}".strip(' —')
                if label and label not in modules: modules.append(label)
    enriched['completed_modules']='\n'.join(modules); cert_id=original(enriched,actor); certs=db_where('authorization_certificates','certificate_id = :cid',(('cid',cert_id),))
    if not certs.empty:
        row=certs.iloc[-1].to_dict(); enriched['certificate_id']=cert_id; enriched['issue_date']=row.get('issue_date',''); enriched['decision_date']=row.get('issue_date',''); enriched['expiry_date']=row.get('expiry_date',''); enriched['status']='Management Approved'; from psb_app.services.certificate_service import build_certificate; _,html,qr=build_certificate(pd.Series(enriched)); patch={'certificate_html':html,'qr_data_uri':qr,'trainer_id':enriched.get('trainer_id',''),'trainer_name':enriched.get('trainer_name',''),'ceo_name':enriched.get('ceo_name',''),'completed_modules':enriched.get('completed_modules',''),'document_code':'PSB-PTQ20-F02','revision_no':'01','revision_date':'11-02-2026'}; db_update('authorization_certificates','certificate_id',cert_id,patch); db_update('authorization_requests','authorization_id',clean(enriched.get('authorization_id')),{'certificate_html':html,'qr_data_uri':qr,'updated_on':now()})
    return cert_id


def install_training_certification_patch() -> None:
    from psb_app.pages import training as t
    from psb_app.pages import qualification as q
    from psb_app.pages import authorization as a
    if getattr(t,'_psb_training_certification_installed',False): return
    t._psb_training_certification_installed=True; raw_db_update=t.db_update; t._psb_original_db_update=raw_db_update
    def patched_training_db_update(table_name,key_col,key_value,patch):
        patch=dict(patch or {})
        if table_name=='training_records' and clean(patch.get('certificate_status'))=='Issued':
            if 'test_status' in patch:
                patch['certificate_status']='Pending Trainer Signature' if clean(patch.get('test_status'))=='Passed' else 'Not Issued'; patch['certificate_link']=''; result=raw_db_update(table_name,key_col,key_value,patch); rec=_record_by_id(clean(key_value)) if key_col=='record_id' else {}
                if rec: sync_training_record(clean(rec.get('user_id')),clean(rec.get('training_id')))
                return result
            actor=st.session_state.get('psb_actor',{}) or {}; record_id=clean(key_value) if key_col=='record_id' else ''
            if not record_id:
                rows=db_where('training_records',f'{key_col} = :v',(('v',key_value),)); record_id=clean(rows.iloc[-1].get('record_id')) if not rows.empty else ''
            return issue_training_attestation(record_id,actor,clean(patch.get('certificate_id')))
        return raw_db_update(table_name,key_col,key_value,patch)
    t.db_update=patched_training_db_update; t.update_training_progress=update_training_progress; t.trainee_training=enhanced_trainee_training; q._theory_status=_qualification_theory_status
    if not hasattr(a,'_psb_original_issue_authorization_certificate'): a._psb_original_issue_authorization_certificate=a._issue_authorization_certificate
    a._issue_authorization_certificate=_enhanced_authorization_issue
