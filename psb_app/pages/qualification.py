from __future__ import annotations
import json
from psb_app.common import actor_get, audit, db_all, db_delete, db_insert, db_update, db_where, file_upload_panel, generate_mcqs, now, pd, st, table_exists, today, uid, can_action, create_notification

PATHS = {
    'NSC Surveyor': {'id':'QP-NSC','department':'Survey NSC','technical_role':'Surveyor'},
    'In-Service Surveyor': {'id':'QP-IS','department':'Survey Inservice','technical_role':'Surveyor'},
    'Industrial Surveyor': {'id':'QP-IND','department':'Survey Inservice','technical_role':'Industrial Surveyor'},
    'Plan Appraiser': {'id':'QP-PA','department':'Plan Appraisal','technical_role':'Plan Appraiser'},
}
ELIGIBLE_PERSON_ROLES={'Trainee','On Probation','Surveyor','NSC Surveyor','In-Service Surveyor','Industrial Surveyor','Plan Appraiser'}
PRACTICAL_ACTIVITY_OPTIONS = {
    'NSC Survey': ['Design / Pre-construction Review Meeting','Material Identification and Certification Review','Steel Preparation and Fit-up Inspection','Welding Procedure and Welder Qualification Verification','Hull Block Fabrication Survey','Hull Erection and Alignment Survey','Keel Laying / Initial Survey','Structural Scantling and Construction Verification','NDT and Weld Inspection Witness','Watertight / Weathertight Closing Appliance Survey','Tank Structural and Tightness Test Witness','Shell Openings, Sea Inlets and Overboard Discharge Inspection','Rudder, Propeller and Shafting Installation Survey','Main Engine and Auxiliary Machinery Installation Survey','Boiler and Pressure Vessel Installation Survey','Piping System Fabrication, Installation and Pressure Test','Steering Gear Installation and Test','Electrical Generation and Distribution Installation Survey','Emergency Power and Lighting Test','Navigation and Communication Equipment Installation Survey','Fire Safety Construction and Equipment Survey','Life-saving Appliances Installation Survey','Load Line Conditions of Assignment Survey','Accommodation and Crew Safety Survey','Environmental Compliance Equipment Installation Survey','Inclining Experiment / Lightweight Survey Witness','Harbour Acceptance Test Witness','Sea Trial Witness','Final Classification and Statutory Survey'],
    'In-Service Survey': ['Annual Survey','Intermediate Survey','Renewal / Special Survey','Damage Survey','Docking / Bottom Survey','Machinery Survey','Load Line Survey','Safety Equipment Survey','Safety Radio Survey'],
    'Industrial Survey': ['Vendor / Works Capability Assessment','Quality Plan and Inspection Test Plan Review','Raw Material Identification and Traceability Inspection','Material Certificate Review','Chemical Composition Test Witness','Mechanical / Tensile / Impact Test Witness','Welding Procedure Specification Review','Welding Procedure Qualification Test Witness','Welder Qualification Test Witness','Welding Consumable Control Inspection','Fabrication Fit-up and Dimensional Inspection','Visual Weld Inspection','Radiographic Testing Witness','Ultrasonic Testing Witness','Magnetic Particle Testing Witness','Dye Penetrant Testing Witness','Heat Treatment / PWHT Record Review','Pressure / Hydrostatic Test Witness','Pneumatic / Leak Test Witness','Load / Proof Test Witness','Machinery Shop Test Witness','Electrical Equipment Routine Test Witness','Factory Acceptance Test','Coating Surface Preparation and DFT Inspection','Packing, Marking and Final Release Inspection','Non-conformity and Corrective Action Verification'],
    'Plan Appraisal': ['General Arrangement Plan','Midship Section Plan','Shell Expansion Plan','Structural Scantling Plans','Deck, Bulkhead and Framing Plans','Fore and Aft End Structure Plans','Superstructure and Deckhouse Plans','Hatch Cover and Closing Appliance Plans','Rudder, Stern Frame and Shaft Bracket Plans','Foundations and Supporting Structure Plans','Cargo Hold / Tank Structural Plans','Machinery Arrangement Plan','Engine Room Arrangement Plan','Shafting Arrangement and Alignment Calculations','Propeller Plan and Calculations','Steering Gear System Plan','Boiler and Pressure Vessel Plans','Piping System Plans','Bilge and Ballast System Plan','Fuel Oil and Lubricating Oil System Plans','Cooling Water and Compressed Air System Plans','Electrical Single-line Diagram','Load Analysis and Short-circuit Calculation','Main and Emergency Switchboard Plans','Cable Routing and Electrical Equipment Plans','Automation, Alarm and Safety System Plans','Intact Stability Booklet','Damage Stability Calculations','Loading Manual and Loading Instrument Documentation','Inclining Experiment Procedure','Fire Control Plan','Structural Fire Protection Plan','Fire Detection and Alarm System Plan','Fixed Fire-extinguishing System Plans','Life-saving Appliances Plan','Navigation Lights and Shapes Plan','Radio and Navigation Equipment Plan','Load Line Plan and Conditions of Assignment','Tonnage Calculation Plan','MARPOL Pollution-prevention System Plans','Energy Efficiency / Environmental Compliance Documentation','Dangerous Goods Arrangement Plan','Helideck / Special Feature Plan','Statutory Arrangement and Compliance Plans'],
}
CUSTOM_PRACTICAL_ACTIVITY='Other — Add custom activity / plan'

def _uid(actor): return str(actor_get(actor,'user_id','') or '')

def _case_message(authorization_id: str, actor: dict, message_type: str, message: str, visibility: str='Case Participants'):
    if table_exists('case_correspondence'):
        db_insert('case_correspondence',{'correspondence_id':uid('MSG'),'authorization_id':authorization_id,'actor_id':actor_get(actor,'user_id',''),'actor_name':actor_get(actor,'name',''),'actor_role':actor_get(actor,'role',''),'message_type':message_type,'message':message,'visibility':visibility,'created_on':now()})

def _notify_roles(roles: set[str], subject: str, message: str, ntype: str='Workflow'):
    users=db_all('users')
    if users.empty: return
    for _,u in users[users.get('role',pd.Series(dtype=str)).astype(str).isin(roles)].iterrows():
        try: create_notification(str(u.get('user_id')),subject,message,ntype)
        except Exception: pass
def _user(uidv):
    u=db_where('users','user_id = :uid',(('uid',uidv),))
    return u.iloc[0].to_dict() if not u.empty else {}
def _assignment(uidv):
    if not table_exists('qualification_assignments'): return {}
    a=db_where('qualification_assignments','user_id = :uid AND status = :status',(('uid',uidv),('status','Active')))
    return a.iloc[-1].to_dict() if not a.empty else {}
def _path_from_assignment(a,user):
    pid=str(a.get('path_id',''))
    for name,cfg in PATHS.items():
        if cfg['id']==pid: return name,cfg
    legacy=str(user.get('trainee_path','') or '')
    return legacy, PATHS.get(legacy,{})


def _ensure_path_training_records(user_id, user_name, user_role, path_name, path_id):
    """Materialize path requirements into the learner record without duplicating existing assignments."""
    if not table_exists('qualification_path_training') or not table_exists('training_records'):
        return 0
    links=db_where('qualification_path_training','path_id = :pid AND active = :active',(('pid',path_id),('active','Yes')))
    # Module-specific theoretical training is also materialized into the learner record.
    if table_exists('qualification_module_training') and table_exists('qualification_path_versions') and table_exists('qualification_path_levels') and table_exists('qualification_level_modules'):
        v=_active_path_version(path_id)
        extra=[]
        for _,level in _levels(v.get('path_version_id','')).iterrows():
            mods=_level_modules(str(level.get('level_id','')))
            for _,m in mods.iterrows():
                mt=_module_trainings(str(m.get('module_id','')))
                for _,x in mt.iterrows(): extra.append({'training_id':x.get('training_id'),'mandatory':x.get('mandatory','Yes'),'sequence_no':x.get('sequence_no',1),'active':'Yes'})
        if extra:
            links=pd.concat([links,pd.DataFrame(extra)],ignore_index=True).drop_duplicates(subset=['training_id'],keep='last')
    created=0
    for _,link in links.iterrows():
        tid=str(link.get('training_id','') or '')
        if not tid: continue
        existing=db_where('training_records','user_id = :uid AND training_id = :tid',(('uid',user_id),('tid',tid)))
        if not existing.empty: continue
        course=db_where('trainings','training_id = :tid',(('tid',tid),))
        title=str(course.iloc[0].get('title','Training')) if not course.empty else 'Training'
        passing=int(course.iloc[0].get('passing_marks') or 70) if not course.empty else 70
        db_insert('training_records',{'record_id':uid('TREC'),'user_id':user_id,'name':user_name,'role':user_role,'trainee_path':path_name,'training_id':tid,'training_title':title,'status':'Assigned','test_status':'Not Started','score':0,'passing_marks':passing,'certificate_status':'Not Issued','due_date':'','completed_on':'','progress':0,'remarks':'Assigned automatically from predefined qualification path','updated_on':now()})
        created+=1
    return created

def my_development_page(actor):
    from psb_app.pages.people import development_plan_page
    development_plan_page(actor)

def department_qualification_page(actor):
    role=str(actor_get(actor,'role','')); dept=str(actor_get(actor,'primary_department',actor_get(actor,'department','')) or '').split(',')[0].strip()
    allowed = can_action(actor,'Department Qualification','View','Department') or can_action(actor,'Administration','Manage','Organization-wide')
    if not allowed:
        st.error('You do not have access to Department Qualification.'); return
    st.header('Department Qualification')
    if role=='Department Manager' and dept not in {'Survey NSC','Survey Inservice','Plan Appraisal'}:
        st.error('Department Manager access is valid only for the assigned Survey NSC, Survey Inservice or Plan Appraisal department.'); return
    st.caption('Department-scoped oversight of people, predefined paths, training, practical/witness, competency and authorization readiness.')
    users=db_all('users'); people=users if role=='Admin' else users[users.get('primary_department',pd.Series(dtype=str)).astype(str).eq(dept)]
    a,b,c=st.columns(3); a.metric('Department',dept if role!='Admin' else 'All'); b.metric('People',len(people)); c.metric('With Path',int(people.get('trainee_path',pd.Series(dtype=str)).astype(str).isin(PATHS.keys()).sum()) if not people.empty else 0)
    tabs=st.tabs(['Overview','People','Training','Practical / Witness','Competency','Authorization Readiness'])
    with tabs[0]: st.info('Use this single workspace to govern qualification inside the assigned department. The Department Manager does not receive organization-wide technical authority by virtue of the title.')
    with tabs[1]:
        if people.empty: st.info('No people are assigned to this department.')
        else: st.dataframe(people[[x for x in ['employee_id','name','role','trainee_path','trainer_name','competency_level','account_status'] if x in people.columns]],use_container_width=True,hide_index=True)
    ids=set(people.get('user_id',pd.Series(dtype=str)).astype(str).tolist()) if not people.empty else set()
    with tabs[2]:
        tr=db_all('training_records'); tr=tr[tr.get('user_id',pd.Series(dtype=str)).astype(str).isin(ids)] if not tr.empty else tr
        st.dataframe(tr[[x for x in ['name','trainee_path','training_title','status','score','progress'] if x in tr.columns]],use_container_width=True,hide_index=True) if not tr.empty else st.info('No department training records yet.')
    with tabs[3]:
        pa=db_all('practical_activities') if table_exists('practical_activities') else pd.DataFrame(); pa=pa[pa.get('user_id',pd.Series(dtype=str)).astype(str).isin(ids)] if not pa.empty else pa
        st.dataframe(pa[[x for x in ['name','scope','job_type','witness_name','status'] if x in pa.columns]],use_container_width=True,hide_index=True) if not pa.empty else st.info('No practical activity records yet.')
    with tabs[4]:
        cp=db_all('competency_matrix'); cp=cp[cp.get('user_id',pd.Series(dtype=str)).astype(str).isin(ids)] if not cp.empty else cp
        st.dataframe(cp[[x for x in ['name','area','scope','competency_level','status'] if x in cp.columns]],use_container_width=True,hide_index=True) if not cp.empty else st.info('No competency records yet.')
    with tabs[5]:
        ar=db_all('authorization_requests'); ar=ar[ar.get('user_id',pd.Series(dtype=str)).astype(str).isin(ids)] if not ar.empty else ar
        st.dataframe(ar[[x for x in ['name','trainee_path','scope','job_type','status'] if x in ar.columns]],use_container_width=True,hide_index=True) if not ar.empty else st.info('No authorization cases yet.')

def _qualification_readiness(user_id):
    assn=_assignment(user_id)
    if not assn: return False, {'reason':'No active qualification path assignment'}
    state=_assignment_state(str(assn.get('qualification_assignment_id','')))
    version_id=str(state.get('path_version_id') or '')
    levels=_levels(version_id)
    if levels.empty: return False, {'reason':'No levels configured'}
    module_count=0; complete_count=0
    for _,lv in levels.iterrows():
        mods=_level_modules(str(lv.get('level_id','')))
        mandatory=mods[mods.get('mandatory',pd.Series(dtype=str)).astype(str).eq('Yes')] if not mods.empty and 'mandatory' in mods.columns else mods
        for _,m in mandatory.iterrows():
            module_count+=1; snap=_sync_module_progress(user_id,str(m.get('module_id','')),str(assn.get('qualification_assignment_id','')))
            if snap.get('module_status')=='Complete': complete_count+=1
    ready=module_count>0 and complete_count==module_count
    return ready, {'modules_complete':complete_count,'modules_required':module_count,'path_id':assn.get('path_id',''),'assignment_id':assn.get('qualification_assignment_id',''),'target_department':state.get('target_department','')}

def people_capability_page(actor):
    st.header('People & Capability')
    st.caption('Organization-level qualification oversight and controlled probation progression decisions.')
    users=db_all('users'); assignments=db_all('qualification_assignments') if table_exists('qualification_assignments') else pd.DataFrame()
    c1,c2,c3,c4=st.columns(4); c1.metric('People',len(users)); c2.metric('Active Qualification Paths',int(assignments.get('status',pd.Series(dtype=str)).astype(str).eq('Active').sum()) if not assignments.empty else 0); c3.metric('On Probation',int(users.get('role',pd.Series(dtype=str)).astype(str).eq('On Probation').sum()) if not users.empty else 0); c4.metric('Trainees',int(users.get('role',pd.Series(dtype=str)).astype(str).eq('Trainee').sum()) if not users.empty else 0)
    tabs=st.tabs(['Qualification Overview','Probation Progression'])
    with tabs[0]:
        rows=[]
        for _,u in users.iterrows():
            aid=_assignment(str(u.get('user_id','')))
            if aid:
                ready,snap=_qualification_readiness(str(u.get('user_id',''))); rows.append({'Person':u.get('name'),'Role':u.get('role'),'Department':u.get('primary_department'),'Path':u.get('trainee_path'),'Modules':f"{snap.get('modules_complete',0)}/{snap.get('modules_required',0)}",'Authorization Readiness':'Ready' if ready else 'In Progress'})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True) if rows else st.info('No active qualification assignments.')
    with tabs[1]:
        if not table_exists('probation_transitions'): st.info('Probation transition storage is not available.'); return
        pending=db_where('probation_transitions','decision = :d',(('d','Pending Approval'),))
        if pending.empty: st.info('No probation progression recommendations are awaiting decision.'); return
        st.dataframe(pending[[c for c in ['transition_id','user_id','target_department','trainer_recommendation','created_on'] if c in pending.columns]],use_container_width=True,hide_index=True)
        labels=(pending['user_id'].astype(str)+' — '+pending['target_department'].astype(str)+' — '+pending['transition_id'].astype(str)).tolist(); sel=st.selectbox('Progression recommendation',labels); tid=sel.rsplit(' — ',1)[-1]; trn=pending[pending['transition_id'].astype(str).eq(tid)].iloc[-1]
        remarks=st.text_area('Decision remarks *'); decision=st.selectbox('Decision',['Approve Progression','Return to Trainer','Reject'])
        permitted=can_action(actor,'Authorization','Approve','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
        if st.button('Record Progression Decision',type='primary',disabled=not permitted):
            if not remarks.strip(): st.error('Decision remarks are required.'); return
            uidv=str(trn.get('user_id','')); assn=_assignment(uidv); state=_assignment_state(str(assn.get('qualification_assignment_id',''))) if assn else {}
            if decision=='Approve Progression':
                db_update('probation_transitions','transition_id',tid,{'decision':'Approved','decided_by':_uid(actor),'decided_on':now()}); db_update('users','user_id',uidv,{'role':'Trainee','primary_department':str(trn.get('target_department',''))})
                if state: db_update('qualification_assignment_state','state_id',str(state.get('state_id')),{'person_stage':'Trainee','target_department':str(trn.get('target_department','')),'updated_by':_uid(actor),'updated_on':now()})
                final='Approved'
            elif decision=='Return to Trainer': db_update('probation_transitions','transition_id',tid,{'decision':'Returned','decided_by':_uid(actor),'decided_on':now()}); final='Returned'
            else: db_update('probation_transitions','transition_id',tid,{'decision':'Rejected','decided_by':_uid(actor),'decided_on':now()}); final='Rejected'
            if table_exists('probation_progression_approvals'):
                ex=db_where('probation_progression_approvals','transition_id = :tid',(('tid',tid),)); patch={'decision':final,'decision_remarks':remarks.strip(),'decided_by':_uid(actor),'decided_on':now(),'updated_on':now()}
                if ex.empty: db_insert('probation_progression_approvals',{'progression_approval_id':uid('PPA'),'transition_id':tid,'user_id':uidv,'requested_by':str(trn.get('created_by','')),'requested_on':str(trn.get('created_on','')),**patch})
                else: db_update('probation_progression_approvals','progression_approval_id',str(ex.iloc[-1].get('progression_approval_id')),patch)
            audit('Probation Progression Decision',f'{uidv}: {final}',actor=actor,entity_type='probation_transitions',entity_id=tid,reason=remarks.strip()); st.success(f'Progression decision recorded: {final}.'); st.rerun()

def _open_current_authorization(user_id):
    a=db_where('authorization_requests','user_id = :uid',(('uid',user_id),)) if table_exists('authorization_requests') else pd.DataFrame()
    if a.empty: return {}
    open_status={'Department Recommended','CRB Review','CRB Recommended','Returned for Clarification','Deferred'}
    a=a[a.get('status',pd.Series(dtype=str)).astype(str).isin(open_status)]
    return a.iloc[-1].to_dict() if not a.empty else {}

def authorization_cases_page(actor):
    st.header('Authorization Cases')
    st.caption('Department qualification recommendation → case-based CRB review → final authorization decision.')
    users=db_all('users'); dept=str(actor_get(actor,'primary_department',actor_get(actor,'department','')) or '').split(',')[0].strip()
    scope_allowed=can_action(actor,'Authorization','Review','Department') or can_action(actor,'Authorization','Manage','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
    if not scope_allowed: st.error('You do not have authorization-case review access.'); return
    if not (can_action(actor,'Authorization','Manage','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')) and not users.empty:
        users=users[users.get('primary_department',pd.Series(dtype=str)).astype(str).eq(dept)]
    rows=[]
    for _,u in users.iterrows():
        if not _assignment(str(u.get('user_id',''))): continue
        ready,snap=_qualification_readiness(str(u.get('user_id',''))); existing=_open_current_authorization(str(u.get('user_id','')))
        rows.append({'User ID':u.get('user_id'),'Person':u.get('name'),'Department':u.get('primary_department'),'Path':u.get('trainee_path'),'Modules':f"{snap.get('modules_complete',0)}/{snap.get('modules_required',0)}",'Readiness':'Ready' if ready else 'Not Ready','Case Status':existing.get('status','Not Created'),'Authorization ID':existing.get('authorization_id','')})
    view=pd.DataFrame(rows); st.dataframe(view,use_container_width=True,hide_index=True) if not view.empty else st.info('No qualification people are available in scope.')
    ready_rows=view[(view['Readiness']=='Ready')] if not view.empty else pd.DataFrame()
    if ready_rows.empty: return
    labels=(ready_rows['Person'].astype(str)+' — '+ready_rows['Path'].astype(str)+' — '+ready_rows['User ID'].astype(str)).tolist(); sel=st.selectbox('Ready person',labels); uidv=sel.rsplit(' — ',1)[-1]; person=users[users['user_id'].astype(str).eq(uidv)].iloc[-1]; existing=_open_current_authorization(uidv)
    if existing: st.info(f"Existing case: {existing.get('authorization_id')} · {existing.get('status')}"); return
    managers=db_all('users'); managers=managers[(managers.get('role',pd.Series(dtype=str)).astype(str).eq('Management')) & (managers.get('status',pd.Series(dtype=str)).astype(str).str.casefold().isin(['active','enabled']))] if not managers.empty else pd.DataFrame()
    if managers.empty: st.warning('A Management user must exist before the CRB case can be constituted.'); return
    mmap={f"{r.get('name','')} — {r.get('user_id','')}":str(r.get('user_id')) for _,r in managers.iterrows()}; ml=st.selectbox('Management CRB representative',list(mmap)); mid=mmap[ml]; remarks=st.text_area('Department Manager recommendation *')
    if st.button('Recommend & Create Authorization Case',type='primary'):
        if not remarks.strip(): st.error('Recommendation remarks are required.'); return
        aid=uid('AUTH'); expiry=''; path=str(person.get('trainee_path') or '')
        db_insert('authorization_requests',{'authorization_id':aid,'user_id':uidv,'name':person.get('name',''),'trainee_path':path,'job_type':path,'scope':path,'competency_id':'','status':'CRB Review','tutor_remarks':'','tutor_signature':'','tutor_signed_on':'','principal_remarks':remarks.strip(),'principal_signature':actor_get(actor,'name',''),'principal_signed_on':now(),'technical_remarks':'','technical_signature':'','technical_signed_on':'','qms_remarks':'','qms_signature':'','qms_signed_on':'','crb_decision':'','crb_remarks':'','management_remarks':'','management_signature':'','management_signed_on':'','expiry_date':expiry,'certificate_id':'','certificate_html':'','certificate_storage_link':'','qr_data_uri':'','created_on':now(),'updated_on':now()})
        if table_exists('crb_case_board_assignments'): db_insert('crb_case_board_assignments',{'board_assignment_id':uid('CRBA'),'authorization_id':aid,'user_id':mid,'system_role':'Management','board_role':'Management Member','voting_authority':'Yes','conflict_declared':'No','attendance_status':'Pending','decision':'','comments':'','assigned_by':_uid(actor),'assigned_on':now(),'decided_on':''})
        audit('Authorization Case Created',f'{person.get("name")} / {path}',actor=actor,entity_type='authorization_requests',entity_id=aid,reason=remarks.strip()); create_notification(mid,'CRB Authorization Case Assigned',f'{person.get("name")} — {path}','Authorization'); st.success('Authorization case created and Management CRB representative assigned.'); st.rerun()

def crb_cases_page(actor):
    st.header('CRB Cases')
    uidv=_uid(actor); assigned=db_where('crb_case_board_assignments','user_id = :uid',(('uid',uidv),)) if table_exists('crb_case_board_assignments') else pd.DataFrame()
    if assigned.empty: st.info('No CRB cases are assigned to you.'); return
    auth=db_all('authorization_requests'); view=assigned.merge(auth,on='authorization_id',how='left',suffixes=('','_case')) if not auth.empty else assigned
    st.dataframe(view[[c for c in ['authorization_id','name','scope','status','board_role','attendance_status','decision'] if c in view.columns]],use_container_width=True,hide_index=True)
    labels=(view.get('name',pd.Series(dtype=str)).astype(str)+' — '+view.get('scope',pd.Series(dtype=str)).astype(str)+' — '+view.get('authorization_id',pd.Series(dtype=str)).astype(str)).tolist(); sel=st.selectbox('CRB case',labels); aid=sel.rsplit(' — ',1)[-1]; case=view[view['authorization_id'].astype(str).eq(aid)].iloc[-1]
    learner_id=str(case.get('user_id_case') or case.get('user_id') or ''); ready,snap=_qualification_readiness(learner_id)
    c1,c2,c3=st.columns(3); c1.metric('Qualification Ready','Yes' if ready else 'No'); c2.metric('Modules',f"{snap.get('modules_complete',0)}/{snap.get('modules_required',0)}"); c3.metric('Department Recommendation','Recorded' if str(case.get('principal_remarks') or '').strip() else 'Missing')
    conflict=st.checkbox('I declare a conflict of interest in this case.'); decision=st.selectbox('CRB decision',['Recommend Approval','Recommend Rejection','Defer','Request Clarification']); comments=st.text_area('CRB comments *'); declare=st.checkbox('I have reviewed the qualification evidence available in this case.')
    if st.button('Record CRB Decision',type='primary'):
        if conflict: st.error('A conflicted member cannot vote. Record the conflict and arrange a replacement member.'); return
        if not declare or not comments.strip(): st.error('Evidence review declaration and comments are required.'); return
        ba=assigned[assigned['authorization_id'].astype(str).eq(aid)].iloc[-1]; db_update('crb_case_board_assignments','board_assignment_id',str(ba.get('board_assignment_id')),{'conflict_declared':'No','attendance_status':'Present','decision':decision,'comments':comments.strip(),'decided_on':now()})
        board=db_where('crb_case_board_assignments','authorization_id = :aid',(('aid',aid),)); voting=board[(board.get('voting_authority',pd.Series(dtype=str)).astype(str).eq('Yes')) & (~board.get('conflict_declared',pd.Series(dtype=str)).astype(str).eq('Yes'))]
        decisions=voting.get('decision',pd.Series(dtype=str)).astype(str).tolist(); final='CRB Review'
        if len(voting)>=1 and decisions and all(x=='Recommend Approval' for x in decisions): final='CRB Recommended'
        elif any(x=='Recommend Rejection' for x in decisions): final='CRB Rejected'
        elif any(x in {'Defer','Request Clarification'} for x in decisions): final='CRB Deferred'
        db_update('authorization_requests','authorization_id',aid,{'status':final,'crb_decision':final,'crb_remarks':comments.strip(),'updated_on':now()}); _case_message(aid,actor,'CRB Decision',f'{decision}: {comments.strip()}');
        if final=='CRB Recommended': _notify_roles({'Management','GM'},'Authorization Ready for Final Decision',f'{aid} has been recommended by CRB.','Authorization');
        audit('CRB Decision Recorded',f'{aid}: {decision}',actor=actor,entity_type='authorization_requests',entity_id=aid,reason=comments.strip()); st.success(f'CRB decision recorded. Case status: {final}.'); st.rerun()

def authorization_decisions_page(actor):
    st.header('Authorization Decisions')
    allowed=can_action(actor,'Authorization','Approve','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
    if not allowed:
        st.error('You do not have final authorization decision authority.'); return
    auth=db_where('authorization_requests','status = :s',(('s','CRB Recommended'),)) if table_exists('authorization_requests') else pd.DataFrame()
    if auth.empty:
        st.info('No CRB-approved/recommended authorization cases are awaiting final decision.'); return
    st.dataframe(auth[[c for c in ['authorization_id','name','scope','status','created_on'] if c in auth.columns]],use_container_width=True,hide_index=True)
    labels=(auth['name'].astype(str)+' — '+auth['scope'].astype(str)+' — '+auth['authorization_id'].astype(str)).tolist()
    sel=st.selectbox('Select person / authorization case',labels)
    aid=sel.rsplit(' — ',1)[-1]
    req=auth[auth['authorization_id'].astype(str).eq(aid)].iloc[-1]
    ready,snap=_qualification_readiness(str(req.get('user_id','')))
    st.markdown('### Authorization Decision Workspace')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Applicant',str(req.get('name','—')))
    c2.metric('Authorization',str(req.get('scope','—')))
    c3.metric('Qualification', 'READY' if ready else 'NOT READY')
    c4.metric('CRB', 'RECOMMENDED')
    tabs=st.tabs(['Qualification Evidence','Department Recommendation','CRB Discussion & Decision','Final Action','Activity & Correspondence'])
    with tabs[0]:
        st.write(f"Mandatory qualification modules: **{snap.get('modules_complete',0)}/{snap.get('modules_required',0)} complete**")
        progress=db_where('qualification_module_progress','user_id = :uid',(('uid',str(req.get('user_id',''))),)) if table_exists('qualification_module_progress') else pd.DataFrame()
        if not progress.empty: st.dataframe(progress[[c for c in ['module_id','theory_status','guided_practical_status','trainer_gate_status','independent_practical_status','competency_status','module_status','completion_percent'] if c in progress.columns]],use_container_width=True,hide_index=True)
        certs=db_where('authorization_certificates','user_id = :uid',(('uid',str(req.get('user_id',''))),)) if table_exists('authorization_certificates') else pd.DataFrame()
        if not certs.empty: st.caption('Existing/historical certificate records are shown for duplicate-control and traceability.'); st.dataframe(certs[[c for c in ['certificate_id','scope','issue_date','expiry_date','status'] if c in certs.columns]],use_container_width=True,hide_index=True)
    with tabs[1]:
        st.write('**Department Manager recommendation**')
        st.info(str(req.get('principal_remarks') or 'No recommendation text recorded.'))
        st.caption(f"Recommended by: {req.get('principal_signature','—')} · {req.get('principal_signed_on','—')}")
    with tabs[2]:
        board=db_where('crb_case_board_assignments','authorization_id = :aid',(('aid',aid),)) if table_exists('crb_case_board_assignments') else pd.DataFrame()
        if board.empty:
            st.error('CRB board record is missing. Final authorization must not proceed without a completed CRB case.')
        else:
            st.dataframe(board[[c for c in ['system_role','board_role','voting_authority','conflict_declared','attendance_status','decision','comments','decided_on'] if c in board.columns]],use_container_width=True,hide_index=True)
            st.success('CRB discussion/decision is complete and the case has been recommended for final authorization.')
            if str(req.get('crb_remarks') or '').strip(): st.info('CRB recorded remarks: '+str(req.get('crb_remarks')))
    with tabs[3]:
        st.warning('Approval creates the Digital Certificate of Authorization immediately. Its validity is exactly 12 months from this final approval date and it will appear on the person’s My Qualification / My Certificates pages.')
        decision=st.selectbox('Final Decision',['Approve Authorization & Allocate Digital Certificate','Return for Clarification','Defer','Reject'])
        remarks=st.text_area('Decision remarks *')
        if st.button('Submit Final Authorization Decision',type='primary'):
            if not remarks.strip(): st.error('Decision remarks are required.'); return
            if decision.startswith('Approve Authorization'):
                if not ready: st.error('Qualification readiness is no longer complete. The case cannot be approved.'); return
                board=db_where('crb_case_board_assignments','authorization_id = :aid',(('aid',aid),)) if table_exists('crb_case_board_assignments') else pd.DataFrame()
                if board.empty or not board.get('decision',pd.Series(dtype=str)).astype(str).eq('Recommend Approval').any(): st.error('A completed CRB recommendation is required before final authorization.'); return
                db_update('authorization_requests','authorization_id',aid,{'status':'Management Approved','management_remarks':remarks.strip(),'management_signature':actor_get(actor,'name',''),'management_signed_on':now(),'updated_on':now()})
                from psb_app.pages.authorization import _issue_authorization_certificate
                fresh=db_where('authorization_requests','authorization_id = :aid',(('aid',aid),)).iloc[-1]
                cert=_issue_authorization_certificate(fresh,actor)
                final=f'Approved · Digital Certificate of Authorization {cert} issued for one year'
            elif decision=='Return for Clarification':
                db_update('authorization_requests','authorization_id',aid,{'status':'Returned for Clarification','management_remarks':remarks.strip(),'updated_on':now()}); final='Returned for Clarification'
            elif decision=='Defer':
                db_update('authorization_requests','authorization_id',aid,{'status':'Deferred','management_remarks':remarks.strip(),'updated_on':now()}); final='Deferred'
            else:
                db_update('authorization_requests','authorization_id',aid,{'status':'Rejected','management_remarks':remarks.strip(),'updated_on':now()}); final='Rejected'
            _case_message(aid,actor,'Final Authorization Decision',f'{final}: {remarks.strip()}');
            try: create_notification(str(req.get('user_id','')),'Authorization Decision',final,'Authorization')
            except Exception: pass
            audit('Final Authorization Decision',f'{aid}: {final}',actor=actor,entity_type='authorization_requests',entity_id=aid,reason=remarks.strip())
            st.success(final); st.rerun()
    with tabs[4]:
        msgs=db_where('case_correspondence','authorization_id = :aid',(('aid',aid),)) if table_exists('case_correspondence') else pd.DataFrame()
        if msgs.empty: st.info('No case correspondence yet.')
        else: st.dataframe(msgs[[c for c in ['created_on','actor_name','actor_role','message_type','message'] if c in msgs.columns]].sort_values('created_on'),use_container_width=True,hide_index=True)
        note=st.text_area('Add case note / clarification',key=f'case_note_{aid}')
        if st.button('Post Case Note',key=f'post_case_note_{aid}'):
            if not note.strip(): st.error('Enter a note.')
            else: _case_message(aid,actor,'Case Note',note.strip()); st.success('Case note posted.'); st.rerun()

def my_authorization_cases_page(actor):
    crb_cases_page(actor)

# -----------------------------------------------------------------------------
# Qualification Curriculum v2: predefined Path -> Version -> Level -> Modules.
# These definitions intentionally override the earlier flat-path UI while keeping
# backward-compatible helpers and data already created by migration 037.
# -----------------------------------------------------------------------------

def _active_path_version(path_id):
    if not table_exists('qualification_path_versions'): return {}
    df=db_where('qualification_path_versions','path_id = :pid AND status = :status',(('pid',path_id),('status','Active')))
    return df.iloc[-1].to_dict() if not df.empty else {}

def _levels(path_version_id):
    if not table_exists('qualification_path_levels') or not path_version_id: return pd.DataFrame()
    df=db_where('qualification_path_levels','path_version_id = :pvid AND active = :active',(('pvid',path_version_id),('active','Yes')))
    return df.sort_values('sequence_no') if not df.empty and 'sequence_no' in df.columns else df

def _assignment_state(assignment_id):
    if not table_exists('qualification_assignment_state') or not assignment_id: return {}
    df=db_where('qualification_assignment_state','qualification_assignment_id = :aid AND status = :status',(('aid',assignment_id),('status','Active')))
    return df.iloc[-1].to_dict() if not df.empty else {}

def _level_modules(level_id):
    if not table_exists('qualification_level_modules') or not level_id: return pd.DataFrame()
    lm=db_where('qualification_level_modules','level_id = :lid AND active = :active',(('lid',level_id),('active','Yes')))
    if lm.empty or not table_exists('qualification_modules'): return lm
    mods=db_all('qualification_modules')
    if mods.empty: return lm
    out=lm.merge(mods,on='module_id',how='left',suffixes=('','_module'))
    return out.sort_values('sequence_no') if 'sequence_no' in out.columns else out


def _module_trainings(module_id):
    if not module_id or not table_exists('qualification_module_training') or not table_exists('trainings'): return pd.DataFrame()
    links=db_where('qualification_module_training','module_id = :mid AND active = :active',(('mid',module_id),('active','Yes')))
    if links.empty: return links
    tr=db_all('trainings')
    if tr.empty: return links
    out=links.merge(tr,on='training_id',how='left',suffixes=('','_course'))
    return out.sort_values('sequence_no') if 'sequence_no' in out.columns else out

def _module_gate(module_id):
    if not module_id or not table_exists('module_practical_gates'): return {'minimum_guided_practical':2,'trainer_satisfaction_required':'Yes','independent_practical_required':1}
    g=db_where('module_practical_gates','module_id = :mid AND active = :active',(('mid',module_id),('active','Yes')))
    return g.iloc[-1].to_dict() if not g.empty else {'minimum_guided_practical':2,'trainer_satisfaction_required':'Yes','independent_practical_required':1}

def _completed_training_item_ids(user_id, training_id):
    if not table_exists('training_resource_progress'):
        return set()
    df=db_where('training_resource_progress','user_id = :uid AND training_id = :tid AND status = :status',(('uid',user_id),('tid',training_id),('status','Completed')))
    if df.empty: return set()
    return set((df.get('item_type',pd.Series(dtype=str)).astype(str)+':'+df.get('item_id',pd.Series(dtype=str)).astype(str)).tolist())

def _theory_status(user_id,module_id):
    """Canonical theory gate: passed MCQ + mandatory files/resources + required live attendance."""
    mts=_module_trainings(module_id)
    if mts.empty: return True,0,0
    mandatory=mts[mts.get('mandatory',pd.Series(dtype=str)).astype(str).eq('Yes')] if 'mandatory' in mts.columns else mts
    total=len(mandatory); complete=0
    rec_all=db_where('training_records','user_id = :uid',(('uid',user_id),)) if table_exists('training_records') else pd.DataFrame()
    for _,mt in mandatory.iterrows():
        tid=str(mt.get('training_id','') or '')
        rec=rec_all[rec_all.get('training_id',pd.Series(dtype=str)).astype(str).eq(tid)] if not rec_all.empty else pd.DataFrame()
        if rec.empty or str(rec.iloc[-1].get('test_status',''))!='Passed':
            continue
        completed=_completed_training_item_ids(user_id,tid)
        files=db_where('files','linked_table = :t AND linked_id = :id',(('t','trainings'),('id',tid))) if table_exists('files') else pd.DataFrame()
        files_ok=all(('File:'+str(r.get('file_id') or r.get('file_name') or '')) in completed for _,r in files.iterrows()) if not files.empty else True
        resources=db_where('training_resources','training_id = :tid AND active = :a',(('tid',tid),('a','Yes'))) if table_exists('training_resources') else pd.DataFrame()
        mandatory_resources=resources[resources.get('mandatory',pd.Series(dtype=str)).astype(str).eq('Yes')] if not resources.empty else resources
        resources_ok=all(('Resource:'+str(r.get('resource_id') or '')) in completed for _,r in mandatory_resources.iterrows()) if not mandatory_resources.empty else True
        sessions=db_where('training_live_sessions','training_id = :tid AND attendance_required = :a',(('tid',tid),('a','Yes'))) if table_exists('training_live_sessions') else pd.DataFrame()
        attendance_ok=True
        if not sessions.empty:
            for _,ss in sessions.iterrows():
                att=db_where('training_session_attendance','session_id = :sid AND user_id = :uid',(('sid',str(ss.get('session_id'))),('uid',user_id))) if table_exists('training_session_attendance') else pd.DataFrame()
                if att.empty or str(att.iloc[-1].get('attendance_status','')) not in {'Present','Recording Viewed'}:
                    attendance_ok=False; break
        if files_ok and resources_ok and attendance_ok:
            complete+=1
    return complete>=total,complete,total

def _guided_status(user_id,module_id):
    if not table_exists('guided_practical_training'): return 0,False
    gp=db_where('guided_practical_training','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',module_id)))
    reviewed=gp[gp.get('trainer_decision',pd.Series(dtype=str)).astype(str).isin(['Satisfactory Training Progress','Ready for Independent Practical'])] if not gp.empty else gp
    satisfied=False
    if table_exists('module_trainer_readiness'):
        rd=db_where('module_trainer_readiness','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',module_id)))
        if not rd.empty: satisfied=str(rd.iloc[-1].get('decision',''))=='Ready for Independent Practical'
    return len(reviewed),bool(satisfied)

def _module_name(module_id):
    if not table_exists('qualification_modules'): return module_id
    d=db_where('qualification_modules','module_id = :mid',(('mid',module_id),))
    return str(d.iloc[-1].get('module_name',module_id)) if not d.empty else module_id

def _independent_status(user_id,module_id):
    if not table_exists('independent_practical_records'): return 0,0
    ip=db_where('independent_practical_records','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',module_id)))
    if ip.empty: return 0,0
    passed=int(ip.get('assessment_outcome',pd.Series(dtype=str)).astype(str).isin(['Competent','Competent / Requirement Satisfied']).sum())
    return passed,len(ip)

def _competency_complete(user_id,module_id):
    name=_module_name(module_id)
    cp=db_where('competency_matrix','user_id = :uid',(('uid',user_id),)) if table_exists('competency_matrix') else pd.DataFrame()
    if cp.empty: return False
    match=cp[(cp.get('area',pd.Series(dtype=str)).astype(str).eq(name)) | (cp.get('scope',pd.Series(dtype=str)).astype(str).eq(name))]
    return (not match.empty) and match.get('status',pd.Series(dtype=str)).astype(str).isin(['Approved','Competent','Current']).any()

def _specific_practical_requirements_status(user_id,module_id):
    if not table_exists('qualification_practical_requirements'):
        return True, True, 0, 0
    reqs=db_where('qualification_practical_requirements','module_id = :mid AND active = :a',(('mid',module_id),('a','Yes')))
    if reqs.empty:
        return True, True, 0, 0
    mandatory=reqs[reqs.get('mandatory',pd.Series(dtype=str)).astype(str).eq('Yes')] if 'mandatory' in reqs.columns else reqs
    guided_required=guided_done=ind_required=ind_done=0
    gp=db_where('guided_practical_training','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',module_id))) if table_exists('guided_practical_training') else pd.DataFrame()
    ip=db_where('independent_practical_records','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',module_id))) if table_exists('independent_practical_records') else pd.DataFrame()
    for _,r in mandatory.iterrows():
        rid=str(r.get('practical_requirement_id','')); needed=int(r.get('required_count') or 1); mode=str(r.get('activity_mode',''))
        if mode=='Independent Practical':
            ind_required+=needed
            if not ip.empty:
                linked=ip[ip.get('practical_requirement_id',pd.Series(dtype=str)).astype(str).eq(rid)]
                ind_done+=int(linked.get('assessment_outcome',pd.Series(dtype=str)).astype(str).isin(['Competent','Competent / Requirement Satisfied']).sum())
        else:
            guided_required+=needed
            if not gp.empty:
                linked=gp[gp.get('practical_requirement_id',pd.Series(dtype=str)).astype(str).eq(rid)]
                guided_done+=int(linked.get('trainer_decision',pd.Series(dtype=str)).astype(str).isin(['Satisfactory Training Progress','Ready for Independent Practical']).sum())
    return guided_done>=guided_required, ind_done>=ind_required, guided_done+ind_done, guided_required+ind_required

def _sync_module_progress(user_id,module_id,assignment_id=''):
    theory_ok,td,tt=_theory_status(user_id,module_id); gate=_module_gate(module_id); gd,sat=_guided_status(user_id,module_id); minimum=int(gate.get('minimum_guided_practical') or 2); required_ip=int(gate.get('independent_practical_required') or 1); ip_passed,ip_total=_independent_status(user_id,module_id); comp=_competency_complete(user_id,module_id)
    req_guided_ok,req_independent_ok,req_done,req_total=_specific_practical_requirements_status(user_id,module_id)
    guided_ok=gd>=minimum and req_guided_ok; trainer_ok=sat or str(gate.get('trainer_satisfaction_required','Yes'))=='No'; independent_ok=ip_passed>=required_ip and req_independent_ok
    complete=theory_ok and guided_ok and trainer_ok and independent_ok and comp
    pct=int(round(100*sum([theory_ok,guided_ok,trainer_ok,independent_ok,comp])/5))
    snapshot={'theory_status':'Complete' if theory_ok else 'In Progress','guided_practical_status':'Complete' if guided_ok else ('Available' if theory_ok else 'Locked'),'trainer_gate_status':'Ready' if trainer_ok else 'Pending','independent_practical_status':'Complete' if independent_ok else ('Available' if trainer_ok and guided_ok and theory_ok else 'Locked'),'competency_status':'Complete' if comp else 'Pending','module_status':'Complete' if complete else 'In Progress','completion_percent':pct,'completed_on':now() if complete else '','updated_on':now()}
    if table_exists('qualification_module_progress'):
        ex=db_where('qualification_module_progress','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',module_id)))
        if ex.empty: db_insert('qualification_module_progress',{'module_progress_id':uid('QMP'),'qualification_assignment_id':assignment_id,'module_id':module_id,'user_id':user_id,**snapshot})
        else: db_update('qualification_module_progress','module_progress_id',str(ex.iloc[-1].get('module_progress_id')),snapshot)
    return snapshot

def _module_prereqs_complete(user_id, level_id, module_id):
    lm=db_where('qualification_level_modules','level_id = :lid AND module_id = :mid',(('lid',level_id),('mid',module_id))) if table_exists('qualification_level_modules') else pd.DataFrame()
    if lm.empty: return True
    refs=[x.strip() for x in str(lm.iloc[-1].get('prerequisite_module_ids') or '').replace(';',',').split(',') if x.strip()]
    for rid in refs:
        p=db_where('qualification_module_progress','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',rid))) if table_exists('qualification_module_progress') else pd.DataFrame()
        if p.empty or str(p.iloc[-1].get('module_status',''))!='Complete': return False
    return True

def _level_complete(user_id, level_id):
    mods=_level_modules(level_id)
    if mods.empty: return True
    mandatory=mods[mods.get('mandatory',pd.Series(dtype=str)).astype(str).eq('Yes')] if 'mandatory' in mods.columns else mods
    for _,m in mandatory.iterrows():
        mid=str(m.get('module_id','')); p=db_where('qualification_module_progress','user_id = :uid AND module_id = :mid',(('uid',user_id),('mid',mid))) if table_exists('qualification_module_progress') else pd.DataFrame()
        if p.empty or str(p.iloc[-1].get('module_status',''))!='Complete': return False
    return True

def my_qualification_page(actor):
    st.header('My Qualification')
    st.caption('Your assigned qualification path, levels, modules, training, practical/witness, competency and authorization journey in one workspace.')
    uidv=_uid(actor); user=_user(uidv); assn=_assignment(uidv); path_name,cfg=_path_from_assignment(assn,user)
    state=_assignment_state(str(assn.get('qualification_assignment_id',''))) if assn else {}
    version={}
    if state.get('path_version_id') and table_exists('qualification_path_versions'):
        v=db_where('qualification_path_versions','path_version_id = :id',(('id',state.get('path_version_id')),)); version=v.iloc[0].to_dict() if not v.empty else {}
    if not version and cfg: version=_active_path_version(cfg.get('id',''))
    levels=_levels(version.get('path_version_id',''))
    current_level_id=str(state.get('current_level_id') or state.get('starting_level_id') or '')
    current_level='Not Started'
    if current_level_id and not levels.empty:
        m=levels[levels['level_id'].astype(str).eq(current_level_id)]
        if not m.empty: current_level=str(m.iloc[0].get('level_name','Not Started'))
    a,b,c,d=st.columns(4)
    a.metric('Qualification Path',path_name or 'Not Assigned')
    b.metric('Current Level',current_level)
    c.metric('Current Role',user.get('role','—'))
    d.metric('Trainer',user.get('trainer_name') or user.get('tutor_name') or 'Not Assigned')
    if not path_name:
        st.warning('No qualification path has been assigned. Your assigned Trainer must select the applicable predefined path before qualification work begins.'); return
    st.caption(f"Path version: {version.get('version_no','—')} · Department/target placement: {state.get('target_department') or cfg.get('department') or user.get('primary_department','—')}")
    tabs=st.tabs(['Overview','Path','Training','Practical / Witness','Competency','Authorization','Evidence','History'])
    # Recalculate canonical module progress and advance to the next level only when the current level is complete.
    if not levels.empty:
        for _, _lv in levels.iterrows():
            for _, _m in _level_modules(str(_lv.get('level_id',''))).iterrows():
                _sync_module_progress(uidv,str(_m.get('module_id','')),str(assn.get('qualification_assignment_id','')))
        if current_level_id and _level_complete(uidv,current_level_id):
            ordered=levels.sort_values('sequence_no').reset_index(drop=True)
            pos=ordered.index[ordered['level_id'].astype(str).eq(current_level_id)].tolist()
            if pos and pos[0] < len(ordered)-1:
                next_id=str(ordered.iloc[pos[0]+1].get('level_id',''))
                if state and next_id and next_id!=current_level_id:
                    db_update('qualification_assignment_state','state_id',str(state.get('state_id')),{'current_level_id':next_id,'updated_by':'system-progression','updated_on':now()})
                    current_level_id=next_id
    tr=db_where('training_records','user_id = :uid',(('uid',uidv),)) if table_exists('training_records') else pd.DataFrame()
    cp=db_where('competency_matrix','user_id = :uid',(('uid',uidv),)) if table_exists('competency_matrix') else pd.DataFrame()
    pa=db_where('practical_activities','user_id = :uid',(('uid',uidv),)) if table_exists('practical_activities') else pd.DataFrame()
    auth=db_where('authorization_requests','user_id = :uid',(('uid',uidv),)) if table_exists('authorization_requests') else pd.DataFrame()
    with tabs[0]:
        total=len(tr); complete=int(tr.get('status',pd.Series(dtype=str)).astype(str).isin(['Completed','Passed','Current']).sum()) if not tr.empty else 0
        practical_done=int(pa.get('status',pd.Series(dtype=str)).astype(str).isin(['Verified','Completed']).sum()) if not pa.empty else 0
        comp_done=int(cp.get('status',pd.Series(dtype=str)).astype(str).isin(['Approved','Competent','Current']).sum()) if not cp.empty else 0
        x1,x2,x3,x4=st.columns(4); x1.metric('Training',f'{complete}/{total}'); x2.metric('Practical Verified',practical_done); x3.metric('Competency Current',comp_done); x4.metric('Authorization','Not Started' if auth.empty else str(auth.iloc[-1].get('status','In Progress')))
        st.subheader('What you need to do next')
        if total==0: st.info('Your Trainer has not yet assigned training/module requirements for the current path level.')
        elif complete<total: st.warning(f'{total-complete} training requirement(s) remain incomplete.')
        else: st.success('Assigned training requirements are complete. Continue the active modules and next qualification requirements.')
    with tabs[1]:
        st.subheader(f'{path_name} — Qualification Path')
        if levels.empty: st.info('No levels have yet been configured for this path version.')
        else:
            for _,lv in levels.iterrows():
                lid=str(lv.get('level_id','')); is_current=lid==current_level_id
                badge='CURRENT' if is_current else ('AVAILABLE' if int(lv.get('sequence_no') or 0)>=1 else '')
                with st.expander(f"{lv.get('level_code','')} · {lv.get('level_name','Level')}  {('— '+badge) if badge else ''}",expanded=is_current):
                    st.caption(str(lv.get('description') or ''))
                    mods=_level_modules(lid)
                    if mods.empty: st.info('Trainer has not yet added modules to this level.')
                    else:
                        view=mods.copy(); statuses=[]; percents=[]; locks=[]
                        previous_levels=levels[pd.to_numeric(levels.get('sequence_no',pd.Series(dtype=int)),errors='coerce') < int(lv.get('sequence_no') or 0)]
                        prior_ok=all(_level_complete(uidv,str(x.get('level_id',''))) for _,x in previous_levels.iterrows())
                        for _,m in view.iterrows():
                            mid=str(m.get('module_id','')); snap=_sync_module_progress(uidv,mid,str(assn.get('qualification_assignment_id',''))); prereq_ok=_module_prereqs_complete(uidv,lid,mid); unlocked=prior_ok and prereq_ok
                            statuses.append(snap.get('module_status') if unlocked else 'Locked'); percents.append(snap.get('completion_percent',0) if unlocked else 0); locks.append('No' if unlocked else 'Yes')
                        view['Status']=statuses; view['Progress %']=percents; view['Locked']=locks
                        cols=[x for x in ['module_code','module_name','module_type','mandatory','Status','Progress %','Locked'] if x in view.columns]
                        st.dataframe(view[cols],use_container_width=True,hide_index=True)
    with tabs[2]:
        st.subheader('Theoretical Training')
        module_rows=[]; training_rows=[]
        for _,lv in levels.iterrows():
            mods=_level_modules(str(lv.get('level_id','')))
            for _,m in mods.iterrows():
                mts=_module_trainings(str(m.get('module_id','')))
                for _,tt in mts.iterrows():
                    rec=tr[tr.get('training_id',pd.Series(dtype=str)).astype(str).eq(str(tt.get('training_id','')))] if not tr.empty else pd.DataFrame(); rr=rec.iloc[-1].to_dict() if not rec.empty else {}
                    training_rows.append({'Level':lv.get('level_name'),'Module':m.get('module_name'),'Training':tt.get('title'),'Mandatory':tt.get('mandatory','Yes'),'Status':rr.get('status','Assigned'),'Test':rr.get('test_status','Not Started'),'Score':rr.get('score',0),'Training ID':tt.get('training_id')})
        if training_rows:
            tv=pd.DataFrame(training_rows); st.dataframe(tv.drop(columns=['Training ID']),use_container_width=True,hide_index=True)
            opts=(tv['Training'].astype(str)+' — '+tv['Module'].astype(str)+' — '+tv['Training ID'].astype(str)).tolist(); chosen=st.selectbox('Open theoretical training',opts,key='my_theory_training'); tid=chosen.rsplit(' — ',1)[-1]
            resources=db_where('training_resources','training_id = :tid AND active = :active',(('tid',tid),('active','Yes'))) if table_exists('training_resources') else pd.DataFrame()
            if not resources.empty:
                st.markdown('#### Video, Rules & References')
                for _,r in resources.iterrows():
                    title=f"{r.get('resource_type','Resource')}: {r.get('title','')}"; url=str(r.get('url') or '').strip(); ref=str(r.get('rule_reference') or '').strip();
                    if url: st.link_button(title,url)
                    else: st.write(title)
                    if ref: st.caption(ref)
            sessions=db_where('training_live_sessions','training_id = :tid',(('tid',tid),)) if table_exists('training_live_sessions') else pd.DataFrame()
            if not sessions.empty:
                st.markdown('#### Live / Zoom Sessions')
                for _,ss in sessions.iterrows():
                    st.write(f"**{ss.get('session_title','Live Training')}** · {ss.get('session_date','')} {ss.get('start_time','')}–{ss.get('end_time','')} · {ss.get('platform','')}")
                    if str(ss.get('meeting_link') or '').strip(): st.link_button('Join Online Session',str(ss.get('meeting_link')).strip(),key=f"join_{ss.get('session_id')}")
            st.markdown('#### Course material & timed MCQ')
            from psb_app.pages.training import trainee_training
            trainee_training(actor,tid)
        else: st.info('No theoretical training has yet been configured inside your assigned path modules.')
    with tabs[3]:
        st.subheader('Practical / Witness Development')
        st.caption('Theory must be complete before guided practical training starts. Each module requires at least two guided Practical/Witness Training activities unless the approved module gate requires more. Independent practical stays locked until the Trainer is satisfied.')
        module_choices=[]
        for _,lv in levels.iterrows():
            mods=_level_modules(str(lv.get('level_id','')))
            for _,m in mods.iterrows(): module_choices.append((f"{lv.get('level_name')} — {m.get('module_name')}",str(m.get('module_id'))))
        if not module_choices: st.info('No modules are configured yet.')
        else:
            mmap=dict(module_choices); ml=st.selectbox('Module',list(mmap),key='my_practical_module'); mid=mmap[ml]
            lmrow=db_where('qualification_level_modules','module_id = :mid',(('mid',mid),)) if table_exists('qualification_level_modules') else pd.DataFrame(); selected_level_id=str(lmrow.iloc[-1].get('level_id','')) if not lmrow.empty else ''
            if selected_level_id and not _module_prereqs_complete(uidv,selected_level_id,mid):
                st.warning('This module is locked until its prerequisite module(s) are complete.'); return
            theory_ok,theory_done,theory_total=_theory_status(uidv,mid); gate=_module_gate(mid); guided_done,satisfied=_guided_status(uidv,mid); minimum=int(gate.get('minimum_guided_practical') or 2)
            a,b,c=st.columns(3); a.metric('Theory',f'{theory_done}/{theory_total}' if theory_total else 'No mandatory theory'); b.metric('Guided Practical',f'{guided_done}/{minimum}'); c.metric('Trainer Gate','Satisfied' if satisfied else 'Pending')
            practical_reqs=db_where('qualification_practical_requirements','module_id = :mid AND active = :a',(('mid',mid),('a','Yes'))) if table_exists('qualification_practical_requirements') else pd.DataFrame()
            if not practical_reqs.empty:
                st.markdown('#### Required Survey / Plan Practical Work')
                st.dataframe(practical_reqs[[c for c in ['activity_domain','activity_title','activity_mode','required_count','mandatory','description'] if c in practical_reqs.columns]],use_container_width=True,hide_index=True)
            if not theory_ok: st.warning('Guided practical is locked until all mandatory theoretical training and required MCQ assessments for this module are passed.')
            else:
                gp=db_where('guided_practical_training','user_id = :uid AND module_id = :mid',(('uid',uidv),('mid',mid))) if table_exists('guided_practical_training') else pd.DataFrame()
                if not gp.empty: st.dataframe(gp[[c for c in ['sequence_no','activity_title','activity_date','status','trainer_decision'] if c in gp.columns]],use_container_width=True,hide_index=True)
                next_seq=(int(pd.to_numeric(gp.get('sequence_no',pd.Series(dtype=int)),errors='coerce').max())+1) if not gp.empty else 1
                guided_reqs=practical_reqs[~practical_reqs.get('activity_mode',pd.Series(dtype=str)).astype(str).eq('Independent Practical')] if not practical_reqs.empty else pd.DataFrame()
                with st.form('guided_practical_report'):
                    practical_requirement_id=''
                    default_title=f'Guided Practical Training {next_seq}'
                    if not guided_reqs.empty:
                        req_map={f"{r.get('activity_mode','')} — {r.get('activity_title','')} — {r.get('practical_requirement_id','')}":str(r.get('practical_requirement_id')) for _,r in guided_reqs.iterrows()}
                        req_label=st.selectbox('Required survey / plan practical item *',list(req_map))
                        practical_requirement_id=req_map[req_label]
                        rr=guided_reqs[guided_reqs['practical_requirement_id'].astype(str).eq(practical_requirement_id)].iloc[-1]
                        default_title=str(rr.get('activity_title') or default_title)
                    title=st.text_input('Practical/Witness Training activity *',value=default_title); activity_date=st.text_input('Activity date (YYYY-MM-DD)',value=today()); location=st.text_input('Location'); reference=st.text_input('Survey / plan / activity reference *'); activity=st.text_area('Activity performed *'); preparation=st.text_area('Preparation undertaken'); rules=st.text_area('Applicable rules / procedures used'); observations=st.text_area('Observations'); deficiencies=st.text_area('Deficiencies identified'); evidence=st.text_area('Evidence collected / linked references'); learning=st.text_area('What I learned *'); difficulties=st.text_area('Difficulties encountered'); submit_gp=st.form_submit_button('Submit Guided Practical Report',type='primary')
                if submit_gp:
                    if not title.strip() or not reference.strip() or not activity.strip() or not learning.strip(): st.error('Required practical item, survey/plan reference, activity performed and learning fields are required.')
                    else:
                        gid=uid('GPT'); db_insert('guided_practical_training',{'guided_practical_id':gid,'qualification_assignment_id':assn.get('qualification_assignment_id',''),'module_id':mid,'practical_requirement_id':practical_requirement_id,'user_id':uidv,'trainer_id':assn.get('trainer_id') or user.get('trainer_id'),'trainer_name':user.get('trainer_name',''),'sequence_no':next_seq,'activity_title':title.strip(),'activity_date':activity_date.strip(),'location':location.strip(),'activity_reference':reference.strip(),'learner_activity':activity.strip(),'learner_preparation':preparation.strip(),'learner_rules_used':rules.strip(),'learner_observations':observations.strip(),'learner_deficiencies':deficiencies.strip(),'learner_evidence':evidence.strip(),'learner_learning':learning.strip(),'learner_difficulties':difficulties.strip(),'trainer_observations':'','trainer_strengths':'','trainer_development_areas':'','trainer_technical_observations':'','trainer_required_improvement':'','trainer_decision':'Pending','trainer_declaration':'No','learner_submitted_on':now(),'trainer_reviewed_on':'','status':'Submitted','created_on':now(),'updated_on':now()}); audit('Guided Practical Report Submitted',title.strip(),actor=actor,entity_type='Guided Practical',entity_id=gid,reason='Assigned qualification path practical requirement'); st.success('Guided practical report submitted to your Trainer for review.'); st.rerun()
            ready=theory_ok and guided_done>=minimum and (satisfied or str(gate.get('trainer_satisfaction_required','Yes'))=='No')
            st.markdown('#### Independent Practical')
            if not ready: st.info('Locked until theory is passed, minimum guided practical training is completed, and Trainer satisfaction is recorded.')
            else:
                existing_ip=db_where('independent_practical_records','user_id = :uid AND module_id = :mid',(('uid',uidv),('mid',mid))) if table_exists('independent_practical_records') else pd.DataFrame()
                if not existing_ip.empty: st.dataframe(existing_ip[[c for c in ['activity_title','activity_date','activity_reference','status','assessment_outcome'] if c in existing_ip.columns]],use_container_width=True,hide_index=True)
                independent_reqs=practical_reqs[practical_reqs.get('activity_mode',pd.Series(dtype=str)).astype(str).eq('Independent Practical')] if not practical_reqs.empty else pd.DataFrame()
                practical_requirement_id=''; independent_title=f'Independent Practical — {ml}'
                if not independent_reqs.empty:
                    imap={f"{r.get('activity_title','')} — {r.get('practical_requirement_id','')}":str(r.get('practical_requirement_id')) for _,r in independent_reqs.iterrows()}
                    il=st.selectbox('Independent practical requirement',list(imap),key=f'ind_req_{mid}'); practical_requirement_id=imap[il]; independent_title=str(independent_reqs[independent_reqs['practical_requirement_id'].astype(str).eq(practical_requirement_id)].iloc[-1].get('activity_title') or independent_title)
                independent_reference=st.text_input('Planned survey / plan / activity reference *',key=f'ind_ref_{mid}')
                if st.button('Request / Start Independent Practical',type='primary',key=f'independent_{mid}'):
                    if not independent_reference.strip(): st.error('A survey / plan / activity reference is required for independent practical.')
                    else:
                        iid=uid('IPR'); db_insert('independent_practical_records',{'independent_practical_id':iid,'qualification_assignment_id':assn.get('qualification_assignment_id',''),'module_id':mid,'practical_requirement_id':practical_requirement_id,'user_id':uidv,'activity_title':independent_title,'activity_date':'','activity_reference':independent_reference.strip(),'assessor_id':'','assessor_name':'','prerequisite_snapshot':f'Theory complete; guided practical {guided_done}/{minimum}; trainer satisfied={satisfied}','report_summary':'','evidence_reference':'','assessment_outcome':'Pending','status':'Requested','created_on':now(),'updated_on':now()}); audit('Independent Practical Unlocked',independent_title,actor=actor,entity_type='Independent Practical',entity_id=iid,reason='Theory and guided practical gate satisfied'); st.success('Independent practical request created.'); st.rerun()
        if not pa.empty:
            st.markdown('#### Existing technical practical/witness records')
            st.dataframe(pa[[x for x in ['scope','job_type','activity_date','status','witness_name'] if x in pa.columns]],use_container_width=True,hide_index=True)
    with tabs[4]:
        st.dataframe(cp[[x for x in ['area','scope','competency_level','status','expiry_date'] if x in cp.columns]],use_container_width=True,hide_index=True) if not cp.empty else st.info('Competency evidence has not yet been recorded.')
    with tabs[5]:
        st.subheader('Authorization Readiness & Digital Certificate')
        if auth.empty:
            st.info('Authorization starts after the path/module, practical and competency requirements reach the defined readiness criteria.')
        else:
            st.dataframe(auth[[x for x in ['scope','job_type','status','decision_date','expiry_date','certificate_id','created_on','updated_on'] if x in auth.columns]],use_container_width=True,hide_index=True)
            latest=auth.iloc[-1]
            cert_id=str(latest.get('certificate_id') or '')
            if cert_id and table_exists('authorization_certificates'):
                cert=db_where('authorization_certificates','certificate_id = :cid',(('cid',cert_id),))
                if not cert.empty:
                    cr=cert.iloc[-1]
                    a,b,c=st.columns(3); a.metric('Certificate','ACTIVE' if str(cr.get('status'))=='Valid' else str(cr.get('status'))); b.metric('Issued',str(cr.get('issue_date','—'))); c.metric('Valid Until',str(cr.get('expiry_date','—')))
                    st.success('Your Digital Certificate of Authorization is attached to your profile for the approved one-year validity period.')
                    html=str(cr.get('certificate_html') or '')
                    if html: st.download_button('Download Digital Certificate of Authorization',data=html,file_name=f'{cert_id}.html',mime='text/html',key=f'my_cert_download_{cert_id}')
                    if str(cr.get('verification_url') or '').strip(): st.link_button('Open Public Certificate Verification',str(cr.get('verification_url')))
    with tabs[6]:
        st.caption('Evidence is referenced once and reused across qualification stages; it should not be uploaded repeatedly.')
        files=db_where('files','owner_user_id = :uid',(('uid',uidv),)) if table_exists('files') else pd.DataFrame()
        st.dataframe(files[[x for x in ['category','file_name','linked_table','linked_id','review_status','created_on'] if x in files.columns]],use_container_width=True,hide_index=True) if not files.empty else st.info('No linked evidence is available yet.')
    with tabs[7]: st.caption('Controlled history records path assignment, Trainer assignment changes, module completion, probation progression, practical/witness, competency and authorization events.')

def independent_practical_assessor_panel(actor):
    """Assigned independent-practical queue with live authorization revalidation."""
    if not table_exists('independent_practical_records'):
        return
    uidv=_uid(actor)
    rows=db_where('independent_practical_records','assessor_id = :uid',(('uid',uidv),))
    rows=rows[rows.get('status',pd.Series(dtype=str)).astype(str).isin(['Assessor Assigned','In Assessment','More Practice'])] if not rows.empty else rows
    st.subheader('Independent Practical Assessments')
    if rows.empty:
        st.info('No independent practical assessments are assigned to you.')
        return
    st.dataframe(rows[[c for c in ['independent_practical_id','user_id','activity_title','activity_date','status','assessment_outcome'] if c in rows.columns]],use_container_width=True,hide_index=True)
    labels=(rows.get('activity_title',pd.Series(dtype=str)).astype(str)+' — '+rows.get('user_id',pd.Series(dtype=str)).astype(str)+' — '+rows.get('independent_practical_id',pd.Series(dtype=str)).astype(str)).tolist()
    chosen=st.selectbox('Open independent practical assessment',labels,key='independent_assessment_case'); iid=chosen.rsplit(' — ',1)[-1]; rec=rows[rows['independent_practical_id'].astype(str).eq(iid)].iloc[-1]
    learner=_user(str(rec.get('user_id',''))); module_id=str(rec.get('module_id','')); module_name=_module_name(module_id); scope=str(learner.get('trainee_path') or module_name)
    from psb_app.pages.practical_witness import _witness_eligibility
    actor_row=pd.Series(_user(uidv)); eligible,reasons,auth_id=_witness_eligibility(actor_row,str(rec.get('user_id','')),scope,'General')
    if not eligible:
        st.error('Your current authorization no longer permits this assessment.')
        for reason in reasons: st.caption(f'• {reason}')
        return
    st.success(f'Assessor eligibility verified · Authorization: {auth_id or "verified technical authority"}')
    c1,c2,c3=st.columns(3); c1.metric('Learner',learner.get('name',rec.get('user_id',''))); c2.metric('Module',module_name); c3.metric('Path',scope)
    with st.form(f'independent_assessment_{iid}'):
        activity_date=st.text_input('Independent practical date (YYYY-MM-DD)',value=str(rec.get('activity_date') or today()))
        activity_reference=st.text_input('Activity / survey reference',value=str(rec.get('activity_reference') or ''))
        report_summary=st.text_area('Learner practical report / summary',value=str(rec.get('report_summary') or ''))
        evidence_reference=st.text_area('Evidence references',value=str(rec.get('evidence_reference') or ''))
        criteria=['Preparation & planning','Rules & procedures','Technical execution','Deficiency identification','Objective evidence','Reporting','Professional judgement','Communication']
        scores={}
        for i,criterion in enumerate(criteria):
            scores[criterion]=st.radio(criterion,['Not Demonstrated','Developing','Satisfactory','Competent'],horizontal=True,key=f'ip_{iid}_{i}')
        strengths=st.text_area('Strengths'); development=st.text_area('Development areas'); observations=st.text_area('Technical observations')
        outcome=st.selectbox('Outcome',['Competent','More Practice Required','Unsatisfactory','Assessment Invalid / Could Not Observe'])
        declaration=st.checkbox('I directly observed sufficient independent performance and assessed it objectively within my current authorization scope.')
        submit=st.form_submit_button('Submit Independent Practical Assessment',type='primary')
    if submit:
        if not declaration: st.error('Assessor declaration is required.'); return
        aid=uid('IPA'); db_insert('independent_practical_assessments',{'independent_assessment_id':aid,'independent_practical_id':iid,'user_id':str(rec.get('user_id','')),'assessor_id':uidv,'assessor_name':actor_get(actor,'name',''),'criteria_scores_json':json.dumps(scores),'strengths':strengths.strip(),'development_areas':development.strip(),'technical_observations':observations.strip(),'outcome':outcome,'declaration':'Yes','assessed_on':now(),'status':'Submitted','created_on':now(),'updated_on':now()})
        status='Completed' if outcome=='Competent' else 'More Practice' if outcome in {'More Practice Required','Unsatisfactory'} else 'Closed'
        db_update('independent_practical_records','independent_practical_id',iid,{'activity_date':activity_date.strip(),'activity_reference':activity_reference.strip(),'report_summary':report_summary.strip(),'evidence_reference':evidence_reference.strip(),'assessment_outcome':outcome,'status':status,'updated_on':now()})
        if outcome=='Competent':
            existing=db_where('competency_matrix','user_id = :uid',(('uid',str(rec.get('user_id',''))),)) if table_exists('competency_matrix') else pd.DataFrame()
            match=existing[(existing.get('area',pd.Series(dtype=str)).astype(str).eq(module_name)) | (existing.get('scope',pd.Series(dtype=str)).astype(str).eq(module_name))] if not existing.empty else pd.DataFrame()
            evidence=json.dumps({'source':'Independent Practical','independent_practical_id':iid,'assessment_id':aid,'assessor_authorization_id':auth_id})
            if match.empty:
                db_insert('competency_matrix',{'competency_id':uid('COMP'),'user_id':str(rec.get('user_id','')),'name':learner.get('name',''),'role':learner.get('role',''),'trainee_path':learner.get('trainee_path',''),'area':module_name,'competency_level':'Competent','scope':module_name,'job_type':'Qualification Module','required_training_ids':'','required_witness_count':0,'required_supervised_count':0,'required_joint_plan_count':0,'required_independent_plan_count':1,'required_level_for_auth':'Competent','status':'Competent','expiry_date':'','evidence':evidence,'created_on':now(),'updated_on':now()})
            else:
                db_update('competency_matrix','competency_id',str(match.iloc[-1].get('competency_id')),{'competency_level':'Competent','status':'Competent','evidence':evidence,'updated_on':now()})
        _sync_module_progress(str(rec.get('user_id','')),module_id,str(rec.get('qualification_assignment_id','')))
        audit('Independent Practical Assessment Submitted',f'{iid}: {outcome}',actor=actor,entity_type='independent_practical_assessments',entity_id=aid,reason='Qualification module independent practical assessment')
        create_notification(str(rec.get('user_id','')),'Independent Practical Assessment Result',f'{module_name}: {outcome}','Qualification')
        st.success('Independent practical assessment recorded and module/competency progress recalculated.'); st.rerun()

def trainer_paths_training_page(actor):
    role=str(actor_get(actor,'role',''))
    allowed = can_action(actor,'Training','Edit','Assigned') or can_action(actor,'Training','Manage','Organization-wide') or can_action(actor,'Administration','Manage','Organization-wide')
    if not allowed: st.error('You do not have permission to manage qualification paths.'); return
    st.header('Qualification Workspace')
    st.caption('One Trainer workspace for assigned learners, path curriculum, theoretical training, AI-assisted MCQ review/publishing, practical/witness development, probation progression and the controlled Knowledge Library.')
    users=db_all('users')
    assigned = users[users.get('trainer_id',pd.Series('',index=users.index)).astype(str).eq(_uid(actor))] if role=='Trainer' and not users.empty else users
    c1,c2,c3,c4=st.columns(4); c1.metric('Assigned Learners',len(assigned)); c2.metric('On Probation',int(assigned.get('role',pd.Series(dtype=str)).astype(str).eq('On Probation').sum()) if not assigned.empty else 0); c3.metric('Trainees',int(assigned.get('role',pd.Series(dtype=str)).astype(str).eq('Trainee').sum()) if not assigned.empty else 0); c4.metric('Technical Staff in Path',int(assigned.get('role',pd.Series(dtype=str)).astype(str).isin(['Surveyor','NSC Surveyor','In-Service Surveyor','Industrial Surveyor','Plan Appraiser']).sum()) if not assigned.empty else 0)
    if not assigned.empty:
        with st.expander('My Assigned Learners',expanded=False):
            st.dataframe(assigned[[c for c in ['employee_id','name','role','primary_department','trainee_path','account_status'] if c in assigned.columns]],use_container_width=True,hide_index=True)
    tabs=st.tabs(['Path Library','Levels','Modules','Theoretical Training & MCQ','Practical / Witness Development','Assign Person','Probation Progression','Path Matrix','Knowledge Library'])
    with tabs[0]:
        rows=[]
        for n,cfg in PATHS.items():
            v=_active_path_version(cfg['id']); lv=_levels(v.get('path_version_id',''))
            rows.append({'Path':n,'Department':cfg['department'],'Technical outcome':cfg['technical_role'],'Active version':v.get('version_no','—'),'Levels':len(lv)})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.info('The four path families are controlled. Trainers configure their versions, levels and modules rather than creating ad-hoc person-specific path names.')
        st.markdown('#### Create and activate a path version')
        with st.form('create_path_version'):
            version_path=st.selectbox('Controlled path family',list(PATHS),key='version_path_family')
            a,b=st.columns(2)
            version_no=a.text_input('Version number *',placeholder='e.g. 1.0')
            effective_from=b.date_input('Effective from',value=pd.to_datetime(today()).date())
            create_version=st.form_submit_button('Create and Activate Version',type='primary',use_container_width=True)
        if create_version:
            cfg=PATHS[version_path]
            version_no=version_no.strip()
            if not version_no:
                st.error('Enter a version number.')
            else:
                existing=db_where('qualification_path_versions','path_id = :pid AND version_no = :version',(('pid',cfg['id']),('version',version_no)))
                if not existing.empty:
                    st.error('That version number already exists for this path.')
                else:
                    current=db_where('qualification_path_versions','path_id = :pid AND status = :status',(('pid',cfg['id']),('status','Active')))
                    for _,old in current.iterrows():
                        db_update('qualification_path_versions','path_version_id',str(old['path_version_id']),{'status':'Superseded','effective_to':str(effective_from),'updated_on':now()})
                    pvid=uid('QPV')
                    db_insert('qualification_path_versions',{'path_version_id':pvid,'path_id':cfg['id'],'version_no':version_no,'status':'Active','effective_from':str(effective_from),'effective_to':'','created_by':_uid(actor),'created_on':now(),'updated_on':now()})
                    audit('Qualification Path Version Activated',f'{version_path} v{version_no}',actor=actor,entity_type='Qualification Path',entity_id=cfg['id'],reason='Trainer curriculum configuration')
                    st.success(f'{version_path} version {version_no} is now active. Open Levels to continue.')
                    st.rerun()
    with tabs[1]:
        pname=st.selectbox('Qualification path',list(PATHS),key='levels_path'); cfg=PATHS[pname]; v=_active_path_version(cfg['id'])
        st.caption(f"Active version: {v.get('version_no','—')}")
        lv=_levels(v.get('path_version_id',''))
        if not lv.empty: st.dataframe(lv[[x for x in ['level_code','level_name','sequence_no','entry_criteria','completion_criteria','active'] if x in lv.columns]],use_container_width=True,hide_index=True)
        if v:
            with st.form('add_level'):
                a,b=st.columns(2); code=a.text_input('Level code *'); name=b.text_input('Level name *'); seq=a.number_input('Sequence',1,99,max(1,len(lv)+1)); desc=b.text_input('Description'); entry=st.text_area('Entry criteria'); completion=st.text_area('Completion criteria'); ok=st.form_submit_button('Add Level',type='primary')
            if ok and code.strip() and name.strip():
                db_insert('qualification_path_levels',{'level_id':uid('QL'),'path_version_id':v['path_version_id'],'level_code':code.strip(),'level_name':name.strip(),'sequence_no':int(seq),'description':desc.strip(),'entry_criteria':entry.strip(),'completion_criteria':completion.strip(),'active':'Yes','created_by':_uid(actor),'created_on':now(),'updated_on':now()}); audit('Qualification Level Added',f'{pname}: {name}',actor=actor,entity_type='Qualification Path',entity_id=cfg['id'],reason='Curriculum configuration'); st.success('Level added.'); st.rerun()
    with tabs[2]:
        pname=st.selectbox('Path',list(PATHS),key='module_path'); cfg=PATHS[pname]; v=_active_path_version(cfg['id']); lv=_levels(v.get('path_version_id',''))
        if lv.empty: st.info('Create a level first.')
        else:
            level_map={f"{r['level_code']} — {r['level_name']}":str(r['level_id']) for _,r in lv.iterrows()}; level_label=st.selectbox('Level',list(level_map)); lid=level_map[level_label]
            mods=_level_modules(lid)
            prerequisite_options={f"{r.get('module_code','')} — {r.get('module_name','')}":str(r.get('module_id','')) for _,r in mods.iterrows()} if not mods.empty else {}
            if not mods.empty:
                module_display=mods[[x for x in ['module_code','module_name','module_type','mandatory','passing_score','evidence_required','assessment_required','practical_training_required','practical_observations_required','witness_required','sequence_no'] if x in mods.columns]].reset_index(drop=True)
                module_event=st.dataframe(module_display,use_container_width=True,hide_index=True,on_select='rerun',selection_mode='single-row',key=f'module_table_{lid}')
                selected_rows=module_event.selection.rows
                if selected_rows:
                    selected=mods.reset_index(drop=True).iloc[int(selected_rows[0])].to_dict(); selected_mid=str(selected.get('module_id','')); type_options=['Theoretical Training','Practical Training']; yes_no=['No','Yes']
                    available_prerequisites={label:value for label,value in prerequisite_options.items() if value!=selected_mid}; existing_prereq_ids={x.strip() for x in str(selected.get('prerequisite_module_ids') or '').split(',') if x.strip()}; existing_prereq_labels=[label for label,value in available_prerequisites.items() if value in existing_prereq_ids]
                    st.markdown('#### Edit selected module')
                    with st.form(f'edit_module_{selected_mid}'):
                        a,b=st.columns(2); edit_code=a.text_input('Module code *',value=str(selected.get('module_code') or '')); edit_name=b.text_input('Module name *',value=str(selected.get('module_name') or '')); current_type=str(selected.get('module_type') or 'Theoretical Training'); edit_type=a.selectbox('Module type',type_options,index=type_options.index(current_type) if current_type in type_options else 0); current_mandatory=str(selected.get('mandatory') or 'Yes'); edit_mandatory=b.selectbox('Mandatory',yes_no,index=yes_no.index(current_mandatory) if current_mandatory in yes_no else 1); edit_seq=a.number_input('Module sequence',1,99,int(selected.get('sequence_no') or 1)); edit_passing=b.number_input('Passing score',0,100,int(selected.get('passing_score') or 0)); current_evidence=str(selected.get('evidence_required') or 'No'); edit_evidence=a.selectbox('Evidence required',yes_no,index=yes_no.index(current_evidence) if current_evidence in yes_no else 0); current_assess=str(selected.get('assessment_required') or 'No'); edit_assess=b.selectbox('Assessment required',yes_no,index=yes_no.index(current_assess) if current_assess in yes_no else 0); current_practical=str(selected.get('practical_training_required') or ('Yes' if current_type=='Practical Training' else 'No')); edit_practical=a.selectbox('Practical Training Required',yes_no,index=yes_no.index(current_practical) if current_practical in yes_no else 0); edit_obs=b.number_input('Practical observations required',0,99,int(selected.get('practical_observations_required') or 0)); current_witness=str(selected.get('witness_required') or 'No'); edit_witness=a.selectbox('Witness required',yes_no,index=yes_no.index(current_witness) if current_witness in yes_no else 0); edit_prerequisites=st.multiselect('Prerequisite modules (optional)',list(available_prerequisites),default=existing_prereq_labels,placeholder='None'); edit_completion=st.text_area('Completion criteria',value=str(selected.get('completion_criteria') or '')); edit_desc=st.text_area('Description',value=str(selected.get('description') or '')); save_module=st.form_submit_button('Save Module Changes',type='primary')
                    if save_module:
                        if not edit_code.strip() or not edit_name.strip(): st.error('Module code and module name are required.')
                        else:
                            edit_prereq=','.join(available_prerequisites[label] for label in edit_prerequisites)
                            db_update('qualification_modules','module_id',selected_mid,{'module_code':edit_code.strip(),'module_name':edit_name.strip(),'module_type':edit_type,'description':edit_desc.strip(),'mandatory':edit_mandatory,'passing_score':int(edit_passing),'evidence_required':edit_evidence,'assessment_required':edit_assess,'practical_training_required':edit_practical,'practical_observations_required':int(edit_obs),'witness_required':edit_witness,'updated_on':now()})
                            db_update('qualification_level_modules','level_module_id',str(selected.get('level_module_id','')),{'sequence_no':int(edit_seq),'prerequisite_module_ids':edit_prereq,'completion_criteria':edit_completion.strip()})
                            audit('Qualification Module Updated',f'{pname}/{level_label}: {edit_name}',actor=actor,entity_type='Qualification Module',entity_id=selected_mid,reason='Trainer curriculum edit'); st.success('Module changes saved.'); st.rerun()
            with st.form('add_module'):
                a,b=st.columns(2); code=a.text_input('Module code *'); name=b.text_input('Module name *'); mtype=a.selectbox('Module type',['Theoretical Training','Practical Training']); mandatory=b.selectbox('Mandatory',['Yes','No']); seq=a.number_input('Module sequence',1,99,max(1,len(mods)+1)); passing=b.number_input('Passing score',0,100,0); evidence=a.selectbox('Evidence required',['No','Yes']); assess=b.selectbox('Assessment required',['No','Yes']); practical_required=a.selectbox('Practical Training Required',['No','Yes'],index=1 if mtype=='Practical Training' else 0); obs=b.number_input('Practical observations required',0,99,0); witness=a.selectbox('Witness required',['No','Yes']); selected_prerequisites=st.multiselect('Prerequisite modules (optional)',list(prerequisite_options),placeholder='None'); completion=st.text_area('Completion criteria'); desc=st.text_area('Description'); ok=st.form_submit_button('Add Module',type='primary')
            if ok and code.strip() and name.strip():
                prereq=','.join(prerequisite_options[label] for label in selected_prerequisites)
                mid=uid('QMOD'); db_insert('qualification_modules',{'module_id':mid,'module_code':code.strip(),'module_name':name.strip(),'module_type':mtype,'description':desc.strip(),'mandatory':mandatory,'passing_score':int(passing),'evidence_required':evidence,'assessment_required':assess,'practical_training_required':practical_required,'practical_observations_required':int(obs),'witness_required':witness,'active':'Yes','created_by':_uid(actor),'created_on':now(),'updated_on':now()}); db_insert('qualification_level_modules',{'level_module_id':uid('QLM'),'level_id':lid,'module_id':mid,'sequence_no':int(seq),'prerequisite_module_ids':prereq,'completion_criteria':completion.strip(),'active':'Yes','created_by':_uid(actor),'created_on':now()}); audit('Qualification Module Added',f'{pname}/{level_label}: {name}',actor=actor,entity_type='Qualification Module',entity_id=mid,reason='Curriculum configuration'); st.success('Module added to the selected level.'); st.rerun()
            if not mods.empty:
                st.markdown('#### Add requirement to module')
                mmap={f"{r.get('module_code','')} — {r.get('module_name','')}":str(r.get('module_id','')) for _,r in mods.iterrows()}; ml=st.selectbox('Module',list(mmap),key='req_module');
                with st.form('add_module_requirement'):
                    rt=st.selectbox('Requirement type',['Training','Reading / Procedure','Assessment','Practical Activity','Witness','Evidence','Competency']); title=st.text_input('Requirement title *'); mandatory=st.selectbox('Mandatory',['Yes','No'],key='req_mand'); count=st.number_input('Required count',1,99,1); notes=st.text_area('Notes'); ok=st.form_submit_button('Add Requirement')
                if ok and title.strip(): db_insert('qualification_module_requirements',{'requirement_id':uid('QREQ'),'module_id':mmap[ml],'requirement_type':rt,'requirement_ref_id':'','requirement_title':title.strip(),'mandatory':mandatory,'required_count':int(count),'notes':notes.strip(),'active':'Yes','created_by':_uid(actor),'created_on':now()}); st.success('Requirement added.'); st.rerun()
    with tabs[5]:
        trainer_id=_uid(actor); eligible=users[users.get('role',pd.Series(dtype=str)).astype(str).isin(ELIGIBLE_PERSON_ROLES)] if not users.empty else pd.DataFrame()
        if role=='Trainer' and not eligible.empty: eligible=eligible[eligible.get('trainer_id',pd.Series('',index=eligible.index)).astype(str).eq(trainer_id)]
        if eligible.empty: st.info('No eligible learners are assigned to you.')
        else:
            labels=(eligible['name'].astype(str)+' — '+eligible['role'].astype(str)+' — '+eligible['user_id'].astype(str)).tolist(); pl=st.selectbox('Person',labels); pid=pl.rsplit(' — ',1)[-1]; person=eligible[eligible['user_id'].astype(str).eq(pid)].iloc[0]; prole=str(person.get('role',''))
            allowed=list(PATHS)
            if prole=='Industrial Surveyor': allowed=['Industrial Surveyor']
            elif prole=='Plan Appraiser': allowed=['Plan Appraiser']
            elif prole=='NSC Surveyor': allowed=['NSC Surveyor']
            elif prole=='In-Service Surveyor': allowed=['In-Service Surveyor']
            elif prole=='Surveyor': allowed=['NSC Surveyor','In-Service Surveyor']
            pname=st.selectbox('Predefined qualification path',allowed); cfg=PATHS[pname]; v=_active_path_version(cfg['id']); lv=_levels(v.get('path_version_id',''))
            level_options={f"{r['level_code']} — {r['level_name']}":str(r['level_id']) for _,r in lv.iterrows()} if not lv.empty else {}
            start_label=st.selectbox('Starting level',list(level_options)) if level_options else None
            if prole in {'Surveyor','NSC Surveyor','In-Service Surveyor','Industrial Surveyor','Plan Appraiser'}: st.caption('Starting above the first level must be supported by a reason/evidence; prior employment role does not silently waive mandatory requirements.')
            skip_reason=st.text_area('Starting-level justification / prior-learning reason',help='Required when starting above the first configured level.')
            skip_evidence=st.text_input('Supporting evidence reference (if applicable)')
            target_default=cfg['department']; target=st.selectbox('Target department', ['Survey NSC','Survey Inservice','Plan Appraisal'],index=['Survey NSC','Survey Inservice','Plan Appraisal'].index(target_default) if target_default in ['Survey NSC','Survey Inservice','Plan Appraisal'] else 0)
            if st.button('Assign Qualification Path',type='primary',use_container_width=True):
                if not v or not start_label: st.error('The path requires an active version and starting level.')
                else:
                    first_id=str(lv.sort_values('sequence_no').iloc[0]['level_id']); start_id=level_options[start_label]
                    if start_id!=first_id and not skip_reason.strip(): st.error('A justification is required when starting above the first level.')
                    else:
                        tutor_id=trainer_id; tutor_name=actor_get(actor,'name',''); old=_assignment(pid)
                        if old: db_update('qualification_assignments','qualification_assignment_id',old['qualification_assignment_id'],{'status':'Replaced','updated_on':now()})
                        aid=uid('QASN'); db_insert('qualification_assignments',{'qualification_assignment_id':aid,'user_id':pid,'path_id':cfg['id'],'trainer_id':trainer_id,'tutor_id':tutor_id,'status':'Active','assigned_by':trainer_id,'assigned_on':now(),'updated_on':now()}); db_insert('qualification_assignment_state',{'state_id':uid('QSTATE'),'qualification_assignment_id':aid,'path_version_id':v['path_version_id'],'starting_level_id':start_id,'current_level_id':start_id,'target_department':target,'person_stage':prole,'skip_reason':skip_reason.strip(),'skip_evidence_ref':skip_evidence.strip(),'status':'Active','updated_by':trainer_id,'updated_on':now()})
                        # On Probation keeps probation status; formal department placement occurs on progression. Others can use current/target technical department.
                        upd={'trainee_path':pname,'trainer_id':trainer_id,'trainer_name':actor_get(actor,'name',''),'tutor_id':tutor_id,'tutor_name':tutor_name,'mentor_id':tutor_id,'mentor_name':tutor_name}
                        if prole!='On Probation': upd['primary_department']=target
                        db_update('users','user_id',pid,upd)
                        if trainer_id and table_exists('user_assignments'): db_insert('user_assignments',{'assignment_id':uid('UASN'),'user_id':pid,'assignment_type':'Trainer','assigned_user_id':trainer_id,'assigned_user_name':tutor_name,'effective_from':today(),'effective_to':'','status':'Active','created_by':trainer_id,'created_on':now()})
                        cnt=_ensure_path_training_records(pid,str(person.get('name',pid)),prole,pname,cfg['id']); audit('Qualification Path Assigned',f'{person.get("name",pid)} → {pname} v{v.get("version_no")} / {start_label}',actor=actor,entity_type='User',entity_id=pid,reason='Controlled versioned qualification path assignment'); st.success(f'Path assigned. {cnt} path training requirement(s) were materialized automatically.'); st.rerun()
    with tabs[3]:
        st.subheader('Theoretical Training inside Modules')
        st.caption('Each module can contain multiple theoretical trainings. Each training may include downloadable files, video/rule links, one or more live Zoom/online sessions, and a timed MCQ assessment.')
        pname=st.selectbox('Path',list(PATHS),key='theory_path'); cfg=PATHS[pname]; v=_active_path_version(cfg['id']); lv=_levels(v.get('path_version_id',''))
        allmods=[]
        for _,l in lv.iterrows():
            mm=_level_modules(str(l.get('level_id','')))
            for _,m in mm.iterrows(): allmods.append((f"{l.get('level_code')} — {m.get('module_code')} — {m.get('module_name')}",str(m.get('module_id'))))
        if not allmods: st.info('Create path levels and modules first.')
        else:
            mmap=dict(allmods); ml=st.selectbox('Module',list(mmap),key='theory_module'); mid=mmap[ml]; existing=_module_trainings(mid)
            if not existing.empty: st.dataframe(existing[[c for c in ['title','mandatory','sequence_no','passing_marks','delivery_mode','status'] if c in existing.columns]],use_container_width=True,hide_index=True)
            with st.form('add_theoretical_training'):
                title=st.text_input('Theoretical training title *'); a,b,c=st.columns(3); mandatory=a.selectbox('Mandatory',['Yes','No']); seq=b.number_input('Sequence',1,99,max(1,len(existing)+1)); passing=c.number_input('Passing score %',1,100,70); duration=a.number_input('MCQ timer (minutes)',1,240,30); attempts=b.number_input('Maximum attempts',1,10,2); delivery=c.selectbox('Delivery mode',['Self-paced','Online','Classroom','Blended']); standards=st.text_area('Rules / standards / other references'); create=st.form_submit_button('Add Theoretical Training',type='primary')
            if create and title.strip():
                tid=uid('TRN'); db_insert('trainings',{'training_id':tid,'module_id':'','title':title.strip(),'category':'Technical','standards':standards.strip(),'target_roles':cfg['technical_role'],'target_paths':pname,'trainer_id':_uid(actor),'trainer_name':actor_get(actor,'name',''),'slides_link':'','video_link':'','reference_link':'','scorm_package_link':'','lms_course_id':'','schedule_date':'','schedule_time':'','meeting_link':'','recording_link':'','passing_marks':int(passing),'max_attempts':int(attempts),'retest_wait_days':0,'delivery_mode':delivery,'duration_hours':0,'location_or_platform':'','capacity':0,'enrollment_open':'Yes','course_version':v.get('version_no','1.0'),'prerequisite_text':'','assessment_required':'Yes','certificate_required':'No','status':'Active','created_on':now(),'updated_on':now()}); db_insert('qualification_module_training',{'module_training_id':uid('QMT'),'module_id':mid,'training_id':tid,'sequence_no':int(seq),'mandatory':mandatory,'active':'Yes','created_by':_uid(actor),'created_on':now()}); db_insert('training_assessment_configs',{'assessment_config_id':uid('TAC'),'training_id':tid,'title':title.strip()+' Knowledge Assessment','duration_minutes':int(duration),'passing_score':int(passing),'max_attempts':int(attempts),'randomize_questions':'Yes','randomize_answers':'Yes','show_result_immediately':'Yes','show_correct_answers':'After Final Attempt','available_from':'','available_until':'','active':'Yes','created_by':_uid(actor),'created_on':now(),'updated_on':now()});
                assigned_count=0
                qa=db_where('qualification_assignments','path_id = :pid AND status = :status',(('pid',cfg['id']),('status','Active'))) if table_exists('qualification_assignments') else pd.DataFrame()
                for _,q in qa.iterrows():
                    u=_user(str(q.get('user_id',''))); assigned_count+=_ensure_path_training_records(str(q.get('user_id','')),str(u.get('name','')),str(u.get('role','')),pname,cfg['id'])
                audit('Module Theoretical Training Added',f'{pname}/{ml}: {title}',actor=actor,entity_type='Training',entity_id=tid,reason='Qualification curriculum'); st.success(f'Theoretical training added to the module and materialized for {assigned_count} active learner record(s).'); st.rerun()
            if not existing.empty:
                opts=(existing['title'].astype(str)+' — '+existing['training_id'].astype(str)).tolist(); sel=st.selectbox('Configure theoretical training',opts,key='theory_config'); tid=sel.rsplit(' — ',1)[-1]
                st.markdown('#### Downloadable learning material')
                file_upload_panel(actor,'trainings',tid,'Training Material')
                files=db_where('files','linked_table = :t AND linked_id = :id',(('t','trainings'),('id',tid))) if table_exists('files') else pd.DataFrame()
                if not files.empty: st.dataframe(files[[c for c in ['file_name','file_ext','review_status','created_on'] if c in files.columns]],use_container_width=True,hide_index=True)
                st.markdown('#### Video / Rules / Other links')
                with st.form('add_training_resource'):
                    rtype=st.selectbox('Resource type',['Video','Rule / Regulation','Procedure / Guidance','Reference Link','Other']); rtitle=st.text_input('Title *'); url=st.text_input('URL'); rr=st.text_input('Rule / reference citation'); mand=st.selectbox('Mandatory',['Yes','No'],key='resource_mand'); add=st.form_submit_button('Add Resource')
                if add and rtitle.strip(): db_insert('training_resources',{'resource_id':uid('TRES'),'training_id':tid,'resource_type':rtype,'title':rtitle.strip(),'url':url.strip(),'rule_reference':rr.strip(),'mandatory':mand,'sequence_no':1,'active':'Yes','created_by':_uid(actor),'created_on':now(),'updated_on':now()}); st.success('Resource added.'); st.rerun()
                resources=db_where('training_resources','training_id = :tid AND active = :a',(('tid',tid),('a','Yes'))) if table_exists('training_resources') else pd.DataFrame()
                if not resources.empty: st.dataframe(resources[[c for c in ['resource_type','title','url','rule_reference','mandatory'] if c in resources.columns]],use_container_width=True,hide_index=True)
                st.markdown('#### Live / Zoom session')
                with st.form('add_live_session'):
                    session_title=st.text_input('Session title *'); a,b,c=st.columns(3); session_date=a.date_input('Date',value=pd.to_datetime(today()).date()); start_time=b.time_input('Start time'); end_time=c.time_input('End time'); mode=a.selectbox('Mode',['Online','Classroom','Hybrid']); platform=b.text_input('Platform','Zoom'); meeting=c.text_input('Zoom / meeting link'); venue=st.text_input('Venue (if physical)'); attendance=st.selectbox('Attendance required',['Yes','No']); add_session=st.form_submit_button('Add Live Session')
                if add_session and session_title.strip(): db_insert('training_live_sessions',{'session_id':uid('TLS'),'training_id':tid,'session_title':session_title.strip(),'session_date':str(session_date),'start_time':start_time.strftime('%H:%M'),'end_time':end_time.strftime('%H:%M'),'delivery_mode':mode,'platform':platform.strip(),'meeting_link':meeting.strip(),'venue':venue.strip(),'attendance_required':attendance,'trainer_id':_uid(actor),'trainer_name':actor_get(actor,'name',''),'status':'Scheduled','created_by':_uid(actor),'created_on':now(),'updated_on':now()}); st.success('Live session added.'); st.rerun()
                sessions=db_where('training_live_sessions','training_id = :tid',(('tid',tid),)) if table_exists('training_live_sessions') else pd.DataFrame()
                if not sessions.empty: st.dataframe(sessions[[c for c in ['session_title','session_date','start_time','end_time','delivery_mode','platform','meeting_link','attendance_required','status'] if c in sessions.columns]],use_container_width=True,hide_index=True)
                if not sessions.empty and table_exists('training_session_attendance'):
                    st.markdown('##### Mark learner attendance')
                    session_map={f"{r.get('session_title','Session')} — {r.get('session_date','')} — {r.get('session_id','')}":str(r.get('session_id')) for _,r in sessions.iterrows()}
                    sl=st.selectbox('Live session',list(session_map),key=f'att_session_{tid}'); sid=session_map[sl]
                    assigned=db_where('training_records','training_id = :tid',(('tid',tid),)) if table_exists('training_records') else pd.DataFrame()
                    if not assigned.empty:
                        learner_map={f"{r.get('name','')} — {r.get('user_id','')}":str(r.get('user_id')) for _,r in assigned.iterrows()}
                        ll=st.selectbox('Learner',list(learner_map),key=f'att_learner_{tid}'); luid=learner_map[ll]; status=st.selectbox('Attendance status',['Present','Absent','Excused','Recording Viewed'],key=f'att_status_{tid}'); remarks=st.text_input('Attendance remarks',key=f'att_rem_{tid}')
                        if st.button('Save Session Attendance',key=f'save_session_att_{tid}'):
                            ex=db_where('training_session_attendance','session_id = :sid AND user_id = :uid',(('sid',sid),('uid',luid)))
                            patch={'attendance_status':status,'remarks':remarks.strip(),'marked_by':_uid(actor),'marked_on':now(),'updated_on':now()}
                            if ex.empty: db_insert('training_session_attendance',{'attendance_id':uid('TATT'),'session_id':sid,'training_id':tid,'user_id':luid,**patch})
                            else: db_update('training_session_attendance','attendance_id',str(ex.iloc[-1].get('attendance_id')),patch)
                            audit('Training Session Attendance Updated',f'{luid} / {sid} / {status}',actor=actor,entity_type='training_session_attendance',entity_id=sid,reason=remarks.strip() or status); st.success('Attendance saved.'); st.rerun()
                st.markdown('#### Timed MCQ Test Builder')
                ac=db_where('training_assessment_configs','training_id = :tid AND active = :a',(('tid',tid),('a','Yes'))) if table_exists('training_assessment_configs') else pd.DataFrame(); conf=ac.iloc[-1].to_dict() if not ac.empty else {}
                parsed_from=pd.to_datetime(conf.get('available_from') or '',errors='coerce'); parsed_until=pd.to_datetime(conf.get('available_until') or '',errors='coerce'); default_dt=pd.Timestamp.now().floor('min')
                with st.form('assessment_config_module'):
                    a,b,c=st.columns(3)
                    timer=a.number_input('Timer (minutes)',1,240,int(conf.get('duration_minutes') or 30))
                    pass_score=b.number_input('Pass mark %',1,100,int(conf.get('passing_score') or 70))
                    max_attempts=c.number_input('Max attempts',1,10,int(conf.get('max_attempts') or 2))
                    randomq=a.selectbox('Randomize questions',['Yes','No'],index=0 if str(conf.get('randomize_questions','Yes'))=='Yes' else 1)
                    randoma=b.selectbox('Randomize answers',['Yes','No'],index=0 if str(conf.get('randomize_answers','Yes'))=='Yes' else 1)
                    immediate=c.selectbox('Show result immediately',['Yes','No'],index=0 if str(conf.get('show_result_immediately','Yes'))=='Yes' else 1)
                    use_availability=st.checkbox('Set assessment availability dates and times',value=bool(conf.get('available_from') or conf.get('available_until')))
                    d1,t1,d2,t2=st.columns(4)
                    available_from_date=d1.date_input('Available from date',value=(parsed_from if not pd.isna(parsed_from) else default_dt).date())
                    available_from_time=t1.time_input('Available from time',value=(parsed_from if not pd.isna(parsed_from) else default_dt).time())
                    available_until_date=d2.date_input('Available until date',value=(parsed_until if not pd.isna(parsed_until) else default_dt+pd.Timedelta(days=7)).date())
                    available_until_time=t2.time_input('Available until time',value=(parsed_until if not pd.isna(parsed_until) else default_dt+pd.Timedelta(days=7)).time())
                    save_ac=st.form_submit_button('Save Test Rules')
                if save_ac:
                    available_from=f'{available_from_date} {available_from_time.strftime("%H:%M")}' if use_availability else ''
                    available_until=f'{available_until_date} {available_until_time.strftime("%H:%M")}' if use_availability else ''
                    if conf.get('assessment_config_id'): db_update('training_assessment_configs','assessment_config_id',conf['assessment_config_id'],{'duration_minutes':int(timer),'passing_score':int(pass_score),'max_attempts':int(max_attempts),'randomize_questions':randomq,'randomize_answers':randoma,'show_result_immediately':immediate,'available_from':available_from,'available_until':available_until,'updated_on':now()})
                    else: db_insert('training_assessment_configs',{'assessment_config_id':uid('TAC'),'training_id':tid,'title':'Knowledge Assessment','duration_minutes':int(timer),'passing_score':int(pass_score),'max_attempts':int(max_attempts),'randomize_questions':randomq,'randomize_answers':randoma,'show_result_immediately':immediate,'show_correct_answers':'After Final Attempt','available_from':available_from,'available_until':available_until,'active':'Yes','created_by':_uid(actor),'created_on':now(),'updated_on':now()})
                    db_update('trainings','training_id',tid,{'passing_marks':int(pass_score),'max_attempts':int(max_attempts),'updated_on':now()}); audit('Training Assessment Rules Updated',sel,actor=actor,entity_type='Training',entity_id=tid,reason='Qualification theoretical training'); st.success('Test rules saved.'); st.rerun()
                extracted=''
                if not files.empty and 'extracted_text' in files.columns:
                    extracted='\n'.join(files['extracted_text'].fillna('').astype(str).tolist())
                source=extracted.strip()
                st.text_area('MCQ source material from uploaded files',value=source,height=180,key=f'mcq_source_{tid}',disabled=True,help='This text is extracted automatically from the uploaded training files and is the controlled source for MCQ generation.')
                qcount=st.slider('Number of MCQs',5,50,10,key=f'mcq_count_{tid}')
                if st.button('Generate Professional MCQ Draft',key=f'mcq_generate_{tid}',type='primary'):
                    qs=generate_mcqs(tid,source,qcount) if source else pd.DataFrame()
                    if qs.empty:
                        st.error('Questions could not be generated. Add clearer training/rule source material.')
                    else:
                        oldd=db_where('training_mcq_drafts','training_id = :tid AND status != :status',(('tid',tid),('status','Superseded'))) if table_exists('training_mcq_drafts') else pd.DataFrame()
                        for _,oq in oldd.iterrows(): db_update('training_mcq_drafts','draft_id',str(oq.get('draft_id','')),{'status':'Superseded','updated_on':now()})
                        import hashlib
                        fp=hashlib.sha256(source.encode('utf-8')).hexdigest()[:24]
                        generation_method=str(qs.attrs.get('generation_method','Controlled source generator'))
                        for _,q in qs.iterrows():
                            db_insert('training_mcq_drafts',{'draft_id':uid('MCQD'),'training_id':tid,'question':q.get('question',''),'option_a':q.get('option_a',''),'option_b':q.get('option_b',''),'option_c':q.get('option_c',''),'option_d':q.get('option_d',''),'correct_answer':q.get('correct_answer',''),'marks':int(q.get('marks') or 1),'status':'Draft','source_fingerprint':fp,'generation_method':generation_method,'generated_by':_uid(actor),'generated_on':now(),'reviewed_by':'','reviewed_on':'','published_on':'','updated_on':now()})
                        audit('Training MCQ Draft Generated',sel,actor=actor,entity_type='Training',entity_id=tid,reason=f'{len(qs)} draft questions generated from controlled training material')
                        st.success(f'{len(qs)} draft MCQs generated. Review/edit them before publishing to learners.')
                        st.rerun()
                drafts=db_where('training_mcq_drafts','training_id = :tid AND status != :status',(('tid',tid),('status','Superseded'))) if table_exists('training_mcq_drafts') else pd.DataFrame()
                if not drafts.empty:
                    st.markdown('##### Trainer Review — Draft Questions')
                    edit_cols=['question','option_a','option_b','option_c','option_d','correct_answer','marks']
                    edited=st.data_editor(drafts[edit_cols],use_container_width=True,num_rows='fixed',key=f'mcq_editor_{tid}')
                    csave,cpublish=st.columns(2)
                    if csave.button('Save Reviewed Drafts',key=f'save_mcq_drafts_{tid}'):
                        for i,(_,orig) in enumerate(drafts.iterrows()):
                            row=edited.iloc[i]
                            db_update('training_mcq_drafts','draft_id',str(orig.get('draft_id')),{ 'question':str(row.get('question','')).strip(),'option_a':str(row.get('option_a','')).strip(),'option_b':str(row.get('option_b','')).strip(),'option_c':str(row.get('option_c','')).strip(),'option_d':str(row.get('option_d','')).strip(),'correct_answer':str(row.get('correct_answer','')).strip(),'marks':int(row.get('marks') or 1),'status':'Reviewed','reviewed_by':_uid(actor),'reviewed_on':now(),'updated_on':now()})
                        audit('Training MCQ Draft Reviewed',sel,actor=actor,entity_type='Training',entity_id=tid,reason='Trainer reviewed generated MCQs')
                        st.success('Reviewed draft questions saved.')
                        st.rerun()
                    if cpublish.button('Publish MCQs to Assigned Learners',key=f'publish_mcq_{tid}',type='primary'):
                        latest=db_where('training_mcq_drafts','training_id = :tid',(('tid',tid),))
                        if latest.empty or len(latest)<5:
                            st.error('At least five reviewed questions are required before publishing.')
                        elif not latest.get('status',pd.Series(dtype=str)).astype(str).isin(['Reviewed','Published']).all():
                            st.error('Review and save all draft questions before publishing.')
                        else:
                            oldq=db_where('question_bank','training_id = :tid',(('tid',tid),))
                            for _,oq in oldq.iterrows(): db_delete('question_bank','question_id',str(oq.get('question_id','')))
                            for _,q in latest.iterrows():
                                db_insert('question_bank',{'question_id':uid('Q'),'training_id':tid,'question':q.get('question',''),'option_a':q.get('option_a',''),'option_b':q.get('option_b',''),'option_c':q.get('option_c',''),'option_d':q.get('option_d',''),'correct_answer':q.get('correct_answer',''),'marks':int(q.get('marks') or 1),'generated_on':now()})
                                db_update('training_mcq_drafts','draft_id',str(q.get('draft_id')),{ 'status':'Published','published_on':now(),'updated_on':now()})
                            assigned_records=db_where('training_records','training_id = :tid',(('tid',tid),))
                            for _,rr in assigned_records.iterrows():
                                create_notification(str(rr.get('user_id','')),'MCQ Assessment Published',f'{sel} · Timed assessment is now available under My Qualification → Training.','Training')
                            audit('Training MCQ Published',sel,actor=actor,entity_type='Training',entity_id=tid,reason=f'{len(latest)} Trainer-reviewed MCQs published to assigned learners')
                            st.success('MCQ assessment published to all people assigned this theoretical training.')
                            st.rerun()
                qbank=db_where('question_bank','training_id = :tid',(('tid',tid),)) if table_exists('question_bank') else pd.DataFrame()
                if not qbank.empty:
                    st.success(f'Published assessment: {len(qbank)} question(s) visible to assigned learners.')


    with tabs[4]:
        st.subheader('Guided Practical → Trainer Satisfaction → Independent Practical')
        st.caption('Each module can require multiple guided Practical/Witness Training activities. The default minimum is two. Independent practical remains locked until theory is passed, the minimum guided activities are reviewed, and the Trainer records satisfaction.')
        pname=st.selectbox('Path',list(PATHS),key='practical_path'); cfg=PATHS[pname]; v=_active_path_version(cfg['id']); lv=_levels(v.get('path_version_id','')); allmods=[]
        for _,l in lv.iterrows():
            mm=_level_modules(str(l.get('level_id','')))
            for _,m in mm.iterrows():
                practical_flag=str(m.get('practical_training_required') or ('Yes' if str(m.get('module_type'))=='Practical Training' else 'No'))
                if practical_flag=='Yes': allmods.append((f"{l.get('level_code')} — {m.get('module_code')} — {m.get('module_name')}",str(m.get('module_id'))))
        if not allmods: st.info('No modules in this path are marked Practical Training Required: Yes.')
        else:
            mmap=dict(allmods); ml=st.selectbox('Module',list(mmap),key='gate_module'); mid=mmap[ml]; gate=_module_gate(mid)
            with st.form('practical_gate'):
                a,b=st.columns(2); minimum=a.number_input('Minimum guided Practical/Witness trainings',2,20,int(gate.get('minimum_guided_practical') or 2)); independent=b.number_input('Required independent practical activities',1,20,int(gate.get('independent_practical_required') or 1)); satisfaction=st.selectbox('Trainer satisfaction required',['Yes','No'],index=0 if str(gate.get('trainer_satisfaction_required','Yes'))=='Yes' else 1); save_gate=st.form_submit_button('Save Practical Gate',type='primary')
            if save_gate:
                if gate.get('practical_gate_id'): db_update('module_practical_gates','practical_gate_id',gate['practical_gate_id'],{'minimum_guided_practical':int(minimum),'independent_practical_required':int(independent),'trainer_satisfaction_required':satisfaction,'updated_on':now()})
                else: db_insert('module_practical_gates',{'practical_gate_id':uid('MPG'),'module_id':mid,'minimum_guided_practical':int(minimum),'trainer_satisfaction_required':satisfaction,'independent_practical_required':int(independent),'active':'Yes','created_by':_uid(actor),'created_on':now(),'updated_on':now()})
                audit('Module Practical Gate Updated',ml,actor=actor,entity_type='Qualification Module',entity_id=mid,reason='Guided practical progression control'); st.success('Practical gate saved.'); st.rerun()
            st.markdown('#### Path-specific Practical / Witness Work')
            st.caption('Define the actual surveys or plan-appraisal work the learner must witness, work together on, or perform as practical experience. Multiple requirements are allowed per module.')
            practical_reqs=db_where('qualification_practical_requirements','module_id = :mid AND active = :a',(('mid',mid),('a','Yes'))) if table_exists('qualification_practical_requirements') else pd.DataFrame()
            if not practical_reqs.empty:
                st.dataframe(practical_reqs[[c for c in ['activity_domain','activity_title','activity_mode','required_count','mandatory','description'] if c in practical_reqs.columns]],use_container_width=True,hide_index=True)
            domain_defaults={'NSC Surveyor':'NSC Survey','In-Service Surveyor':'In-Service Survey','Industrial Surveyor':'Industrial Survey','Plan Appraiser':'Plan Appraisal'}
            domain_options=list(PRACTICAL_ACTIVITY_OPTIONS)
            domain=st.selectbox('Work domain',domain_options,index=domain_options.index(domain_defaults[pname]),key=f'practical_domain_{mid}')
            selected_activity=st.selectbox('Required survey / plan / practical activity *',PRACTICAL_ACTIVITY_OPTIONS[domain]+[CUSTOM_PRACTICAL_ACTIVITY],key=f'practical_activity_{mid}')
            custom_activity=st.text_input('Custom activity / plan *',placeholder='Enter the required activity or plan name',key=f'custom_practical_activity_{mid}') if selected_activity==CUSTOM_PRACTICAL_ACTIVITY else ''
            activity_title=custom_activity.strip() if selected_activity==CUSTOM_PRACTICAL_ACTIVITY else selected_activity
            with st.form(f'practical_requirement_{mid}'):
                activity_mode=st.selectbox('Required participation mode',['Witness / Observe','Work Together / Joint','Guided Practical','Independent Practical'])
                required_count=st.number_input('Required number',1,20,1)
                mandatory_req=st.selectbox('Mandatory',['Yes','No'],key=f'prac_req_mand_{mid}')
                description=st.text_area('Requirement / expected work scope')
                add_req=st.form_submit_button('Add Practical / Witness Requirement')
            if add_req and activity_title:
                prid=uid('PWR')
                db_insert('qualification_practical_requirements',{'practical_requirement_id':prid,'module_id':mid,'activity_domain':domain,'activity_title':activity_title.strip(),'activity_mode':activity_mode,'required_count':int(required_count),'description':description.strip(),'mandatory':mandatory_req,'active':'Yes','created_by':_uid(actor),'created_on':now(),'updated_on':now()})
                audit('Qualification Practical Requirement Added',f'{pname}/{ml}: {activity_title}',actor=actor,entity_type='qualification_practical_requirements',entity_id=prid,reason=activity_mode)
                st.success('Practical / witness work requirement added to the path module.')
                st.rerun()
            elif add_req:
                st.error('Enter the custom activity or plan name.')
            gp=db_where('guided_practical_training','module_id = :mid',(('mid',mid),)) if table_exists('guided_practical_training') else pd.DataFrame()
            if not gp.empty:
                st.markdown('#### Trainer review queue')
                st.dataframe(gp[[c for c in ['user_id','sequence_no','activity_title','activity_date','status','trainer_decision'] if c in gp.columns]],use_container_width=True,hide_index=True)
                rows=(gp['activity_title'].astype(str)+' — '+gp['user_id'].astype(str)+' — '+gp['guided_practical_id'].astype(str)).tolist(); chosen=st.selectbox('Review guided practical report',rows,key='gp_review'); gid=chosen.rsplit(' — ',1)[-1]; rec=gp[gp['guided_practical_id'].astype(str).eq(gid)].iloc[0]
                st.write('Learner activity:',rec.get('learner_activity','')); st.write('Rules used:',rec.get('learner_rules_used','')); st.write('Observations:',rec.get('learner_observations','')); st.write('What was learned:',rec.get('learner_learning',''))
                with st.form('trainer_guided_review'):
                    obs=st.text_area('Trainer observations'); strengths=st.text_area('Strengths'); dev=st.text_area('Development areas'); tech=st.text_area('Technical observations'); improve=st.text_area('Required improvement'); decision=st.selectbox('Decision',['Satisfactory Training Progress','Additional Guided Training Required','Ready for Independent Practical']); declare=st.checkbox('I directly supervised/observed this training activity.'); submit=st.form_submit_button('Submit Trainer Review',type='primary')
                if submit:
                    if not declare: st.error('Trainer declaration is required.')
                    else: db_update('guided_practical_training','guided_practical_id',gid,{'trainer_observations':obs.strip(),'trainer_strengths':strengths.strip(),'trainer_development_areas':dev.strip(),'trainer_technical_observations':tech.strip(),'trainer_required_improvement':improve.strip(),'trainer_decision':decision,'trainer_declaration':'Yes','trainer_reviewed_on':now(),'status':'Reviewed','updated_on':now()}); audit('Guided Practical Reviewed',str(rec.get('activity_title','')),actor=actor,entity_type='Guided Practical',entity_id=gid,reason=decision); st.success('Trainer review recorded.'); st.rerun()
            if not gp.empty and table_exists('module_trainer_readiness'):
                st.markdown('#### Final Trainer Readiness Gate')
                learner_ids=sorted(set(gp.get('user_id',pd.Series(dtype=str)).astype(str).tolist()))
                learner_map={}
                for luid in learner_ids:
                    lu=_user(luid); learner_map[f"{lu.get('name',luid)} — {luid}"]=luid
                if learner_map:
                    ll=st.selectbox('Learner for final readiness',list(learner_map),key='final_gate_learner'); luid=learner_map[ll]
                    reviewed_count=len(gp[(gp.get('user_id',pd.Series(dtype=str)).astype(str).eq(luid)) & (gp.get('trainer_decision',pd.Series(dtype=str)).astype(str).isin(['Satisfactory Training Progress','Ready for Independent Practical']))])
                    st.caption(f'Reviewed satisfactory guided activities: {reviewed_count}/{int(gate.get("minimum_guided_practical") or 2)}')
                    with st.form('final_trainer_readiness'):
                        gate_decision=st.selectbox('Final development decision',['Not Ready — Additional Guided Training Required','Ready for Independent Practical'])
                        gate_remarks=st.text_area('Final readiness remarks *')
                        gate_declare=st.checkbox('I confirm the required guided practical development has been reviewed and this is my final readiness decision for this module.')
                        gate_submit=st.form_submit_button('Record Final Trainer Gate',type='primary')
                    if gate_submit:
                        if not gate_declare or not gate_remarks.strip(): st.error('Declaration and remarks are required.')
                        elif gate_decision=='Ready for Independent Practical' and reviewed_count<int(gate.get('minimum_guided_practical') or 2): st.error('The minimum guided practical requirement has not been completed.')
                        else:
                            ex=db_where('module_trainer_readiness','user_id = :uid AND module_id = :mid',(('uid',luid),('mid',mid)))
                            patch={'qualification_assignment_id':_assignment(luid).get('qualification_assignment_id',''),'module_id':mid,'user_id':luid,'trainer_id':_uid(actor),'decision':'Ready for Independent Practical' if gate_decision.startswith('Ready') else 'Not Ready','remarks':gate_remarks.strip(),'declaration':'Yes','decided_on':now(),'updated_on':now()}
                            if ex.empty: db_insert('module_trainer_readiness',{'trainer_readiness_id':uid('MTR'),**patch})
                            else: db_update('module_trainer_readiness','trainer_readiness_id',str(ex.iloc[-1].get('trainer_readiness_id')),patch)
                            _sync_module_progress(luid,mid,_assignment(luid).get('qualification_assignment_id','')); audit('Trainer Module Readiness Recorded',f'{luid}/{ml}: {patch["decision"]}',actor=actor,entity_type='module_trainer_readiness',entity_id=luid,reason=gate_remarks.strip()); st.success('Final Trainer readiness decision recorded.'); st.rerun()
            if table_exists('independent_practical_records'):
                requests=db_where('independent_practical_records','module_id = :mid',(('mid',mid),))
                requests=requests[requests.get('status',pd.Series(dtype=str)).astype(str).isin(['Requested','Assessor Assigned'])] if not requests.empty else requests
                if not requests.empty:
                    st.markdown('#### Independent Practical Assignment')
                    st.dataframe(requests[[c for c in ['independent_practical_id','user_id','activity_title','status','assessor_name'] if c in requests.columns]],use_container_width=True,hide_index=True)
                    reqmap={f"{r.get('activity_title','Independent Practical')} — {r.get('user_id','')} — {r.get('independent_practical_id','')}":str(r.get('independent_practical_id')) for _,r in requests.iterrows()}
                    rl=st.selectbox('Independent practical request',list(reqmap),key='ip_assign_req'); iid=reqmap[rl]; iprow=requests[requests['independent_practical_id'].astype(str).eq(iid)].iloc[-1]; learner_id=str(iprow.get('user_id','')); learner=_user(learner_id); scope=str(learner.get('trainee_path') or _module_name(mid))
                    from psb_app.pages.practical_witness import _eligible_witnesses
                    eligible=_eligible_witnesses(learner_id,scope,'General')
                    if not eligible: st.warning('No currently authorized assessor is eligible for this independent practical scope.')
                    else:
                        amap={f"{name} — {role} — {uidv}":uidv for uidv,name,role in eligible}; al=st.selectbox('Eligible authorized assessor',list(amap),key='ip_assessor'); assessor_id=amap[al]; assessor=_user(assessor_id)
                        if st.button('Assign Independent Practical Assessor',key='assign_ip_assessor',type='primary'):
                            db_update('independent_practical_records','independent_practical_id',iid,{'assessor_id':assessor_id,'assessor_name':assessor.get('name',''),'status':'Assessor Assigned','updated_on':now()}); create_notification(assessor_id,'Independent Practical Assessment Assigned',f'{learner.get("name",learner_id)} — {_module_name(mid)}','Assessment'); audit('Independent Practical Assessor Assigned',f'{iid} → {assessor.get("name",assessor_id)}',actor=actor,entity_type='independent_practical_records',entity_id=iid,reason='Eligible authorized assessor selected'); st.success('Assessor assigned.'); st.rerun()
    with tabs[6]:
        st.subheader('On Probation → Trainee')
        probs=users[users.get('role',pd.Series(dtype=str)).astype(str).eq('On Probation')] if not users.empty else pd.DataFrame()
        if role=='Trainer' and not probs.empty: probs=probs[probs.get('trainer_id',pd.Series('',index=probs.index)).astype(str).eq(_uid(actor))]
        if probs.empty: st.info('No probationary people are assigned for progression.')
        else:
            opts=(probs['name'].astype(str)+' — '+probs['user_id'].astype(str)).tolist(); pl=st.selectbox('Probationary person',opts); pid=pl.rsplit(' — ',1)[-1]; assn=_assignment(pid); state=_assignment_state(str(assn.get('qualification_assignment_id',''))) if assn else {}; target=st.selectbox('Department placement',['Survey NSC','Survey Inservice','Plan Appraisal'],index=['Survey NSC','Survey Inservice','Plan Appraisal'].index(state.get('target_department')) if state.get('target_department') in ['Survey NSC','Survey Inservice','Plan Appraisal'] else 0); recommendation=st.text_area('Trainer recommendation *'); tutor_comments=st.text_area('Trainer development note')
            if st.button('Submit Progression Recommendation',type='primary'):
                if not recommendation.strip(): st.error('Trainer recommendation is required.')
                elif not assn: st.error('A qualification path must be assigned before progression.')
                else:
                    existing=db_where('probation_transitions','user_id = :uid AND decision = :d',(('uid',pid),('d','Pending Approval')))
                    if not existing.empty: st.info('A progression recommendation is already awaiting approval.')
                    else:
                        tid=uid('PROG'); db_insert('probation_transitions',{'transition_id':tid,'user_id':pid,'qualification_assignment_id':assn.get('qualification_assignment_id'),'from_role':'On Probation','to_role':'Trainee','target_department':target,'trainer_recommendation':recommendation.strip(),'tutor_comments':tutor_comments.strip(),'decision':'Pending Approval','decided_by':'','decided_on':'','created_by':_uid(actor),'created_on':now()})
                        if table_exists('probation_progression_approvals'): db_insert('probation_progression_approvals',{'progression_approval_id':uid('PPA'),'transition_id':tid,'user_id':pid,'requested_by':_uid(actor),'requested_on':now(),'decision':'Pending','decision_remarks':'','decided_by':'','decided_on':'','updated_on':now()})
                        audit('Probation Progression Recommended',f'{pid} → Trainee / {target}',actor=actor,entity_type='probation_transitions',entity_id=tid,reason=recommendation.strip()); st.success('Progression recommendation submitted. The person remains On Probation until an authorized Management/GM/Admin decision is recorded.'); st.rerun()
    with tabs[7]:
        rows=[]
        for pname,cfg in PATHS.items():
            v=_active_path_version(cfg['id']); lv=_levels(v.get('path_version_id',''))
            for _,l in lv.iterrows():
                mods=_level_modules(str(l.get('level_id',''))); rows.append({'Path':pname,'Version':v.get('version_no','—'),'Level':l.get('level_name'),'Sequence':l.get('sequence_no'),'Modules':len(mods)})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True) if rows else st.info('No configured path levels yet.')
    with tabs[8]:
        from psb_app.pages.training import knowledge_page
        knowledge_page(actor)
