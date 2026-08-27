from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core.practical_witness_policy import WITNESS_ROLES, SENIOR_WITNESS_ROLES, is_witness_role, is_senior_witness_role, workspace_modes_for_role

from psb_app.common import (
    SCOPES,
    JOB_TYPES,
    actor_get,
    audit,
    can_action,
    db_all,
    db_insert,
    db_update,
    db_where,
    create_notification,
    now,
    table,
    today,
    uid,
)

COMPLETE_OUTCOMES = {'Competent / Requirement Satisfied'}
DEVELOPMENT_OUTCOMES = {'Satisfactory Progress', 'More Practice Required', 'Unsatisfactory'}
ASSESSMENT_OPTIONS = ['Not Observed', 'Needs Development', 'Satisfactory', 'Competent']
SURVEY_CRITERIA = [
    'Preparation & planning', 'Rules & procedures', 'Technical execution',
    'Deficiency identification', 'Objective evidence', 'Reporting',
    'Professional judgement', 'Communication'
]
PLAN_CRITERIA = [
    'Drawing review', 'Rule identification', 'Technical calculations',
    'Deficiency/comment preparation', 'Rule interpretation',
    'Communication with designer', 'Final recommendation', 'Document control'
]


def _scope_discipline(scope: str) -> str:
    text = str(scope or '').casefold()
    if 'hull' in text:
        return 'Hull'
    if 'machinery' in text:
        return 'Machinery'
    if 'electrical' in text:
        return 'Electrical'
    if 'industrial' in text:
        return 'Industrial'
    if 'plan' in text:
        return 'Plan Appraisal'
    if 'audit' in text:
        return 'QMS / Audit'
    if 'rule' in text:
        return 'Rule Development'
    return 'General'


def _jloads(value, default=None):
    try:
        return json.loads(str(value or ''))
    except Exception:
        return default if default is not None else {}


def _requirements_for(user_id: str, scope: str | None = None) -> pd.DataFrame:
    reqs = db_all('practical_requirement_templates')
    if reqs.empty:
        return reqs
    reqs = reqs[reqs.get('active', pd.Series(dtype=str)).astype(str).str.casefold().isin(['yes', 'active', 'true', '1'])].copy()
    users = db_all('users')
    user = users[users['user_id'].astype(str) == str(user_id)] if not users.empty else pd.DataFrame()
    if not user.empty:
        r = user.iloc[0]
        role = str(r.get('role', ''))
        path = str(r.get('trainee_path', ''))
        if 'target_role' in reqs.columns:
            mask = reqs['target_role'].fillna('').astype(str).isin(['', 'All', role])
            reqs = reqs[mask]
        if path and 'trainee_path' in reqs.columns:
            mask = reqs['trainee_path'].fillna('').astype(str).isin(['', 'All', path])
            reqs = reqs[mask]
    if scope and 'scope' in reqs.columns:
        reqs = reqs[reqs['scope'].fillna('').astype(str).isin(['', 'All', scope])]
    return reqs


def _activity_counts(user_id: str, requirement_id: str) -> dict:
    acts = db_where('practical_activities', 'user_id = :uid and requirement_id = :rid', (('uid', user_id), ('rid', requirement_id)))
    ass = db_where('practical_assessments', 'user_id = :uid and requirement_id = :rid', (('uid', user_id), ('rid', requirement_id)))
    verified = 0
    if not ass.empty:
        verified = int(ass.get('outcome', pd.Series(dtype=str)).astype(str).isin(COMPLETE_OUTCOMES).sum())
    return {
        'activities': len(acts),
        'verified': verified,
        'awaiting': int(acts.get('status', pd.Series(dtype=str)).astype(str).isin(['Evidence Ready', 'Awaiting Witness']).sum()) if not acts.empty else 0,
        'more_practice': int(ass.get('outcome', pd.Series(dtype=str)).astype(str).isin(DEVELOPMENT_OUTCOMES).sum()) if not ass.empty else 0,
    }


def _witness_eligibility(candidate: pd.Series, person_id: str, scope: str, discipline: str) -> tuple[bool, list[str], str]:
    reasons = []
    cid = str(candidate.get('user_id', ''))
    role = str(candidate.get('role', ''))
    if not cid or cid == str(person_id):
        reasons.append('A person cannot witness their own assessment.')
    if str(candidate.get('status', 'Active')).casefold() not in {'active', 'enabled'}:
        reasons.append('Witness account is not active.')
    if not is_witness_role(role):
        reasons.append('Role is not eligible to perform witness assessments.')

    auth_id = ''
    auths = db_where('authorization_requests', 'user_id = :uid', (('uid', cid),))
    if not auths.empty:
        valid = auths[
            auths.get('status', pd.Series(dtype=str)).astype(str).isin(['Management Approved', 'Approved', 'Authorized', 'Active'])
        ].copy()
        if 'scope' in valid.columns:
            exact = valid[valid['scope'].astype(str) == str(scope)]
            if not exact.empty:
                auth_id = str(exact.iloc[0].get('authorization_id', ''))
        if not auth_id and not is_senior_witness_role(role):
            reasons.append('No active authorization exists for the required scope.')
    elif not is_senior_witness_role(role):
        reasons.append('No active authorization exists for the witness.')

    if is_senior_witness_role(role) and not auth_id:
        tas = db_where('technical_authorities', 'user_id = :uid', (('uid', cid),))
        if tas.empty or not tas.get('active', pd.Series(dtype=str)).astype(str).str.casefold().isin(['yes', 'active', 'true', '1']).any():
            reasons.append('Senior witness has no active technical authority appointment.')
        else:
            auth_id = str(tas.iloc[0].get('authority_id', ''))

    restrictions = db_where('authorization_restrictions', 'user_id = :uid', (('uid', cid),))
    if not restrictions.empty:
        blocking = restrictions[
            restrictions.get('status', pd.Series(dtype=str)).astype(str).str.casefold().isin(['active', 'open'])
        ]
        if not blocking.empty:
            reasons.append('An active authorization restriction blocks witness eligibility.')

    # Discipline is independently checked against explicit technical authority/authorization scope.
    if discipline and discipline not in {'General', 'QMS / Audit'}:
        scope_text = f"{scope} {candidate.get('assigned_duty','')} {candidate.get('competency_level','')}".casefold()
        if discipline.casefold() not in scope_text and role not in SENIOR_WITNESS_ROLES:
            # Exact authorization match above is sufficient even when the friendly discipline word is not repeated.
            if not auth_id:
                reasons.append(f'Witness is not authorized for {discipline} discipline.')

    return (not reasons, reasons, auth_id)


def _eligible_witnesses(person_id: str, scope: str, discipline: str, eligible_roles: set[str] | None = None) -> list[tuple[str, str, str]]:
    users = db_all('users')
    if users.empty:
        return []
    rows = []
    for _, candidate in users.iterrows():
        if eligible_roles and str(candidate.get('role','')) not in eligible_roles:
            continue
        ok, _, auth_id = _witness_eligibility(candidate, person_id, scope, discipline)
        if ok:
            rows.append((str(candidate.get('user_id', '')), str(candidate.get('name', '')), auth_id))
    return rows


def _progress_rows(user_id: str) -> tuple[pd.DataFrame, dict]:
    reqs = _requirements_for(user_id)
    rows = []
    totals = {'required': 0, 'verified': 0, 'awaiting': 0, 'more_practice': 0, 'not_started': 0}
    for _, req in reqs.iterrows():
        rid = str(req.get('requirement_id', ''))
        needed = max(1, int(req.get('required_observations', 1) or 1))
        c = _activity_counts(user_id, rid)
        verified = min(c['verified'], needed)
        totals['required'] += needed
        totals['verified'] += verified
        totals['awaiting'] += c['awaiting']
        totals['more_practice'] += c['more_practice']
        if c['activities'] == 0:
            totals['not_started'] += needed
        if verified >= needed:
            status = 'Complete'
        elif c['awaiting']:
            status = 'Awaiting Witness'
        elif c['more_practice']:
            status = 'More Practice'
        elif c['activities']:
            status = 'In Progress'
        else:
            status = 'Not Started'
        rows.append({
            'Requirement': req.get('title', ''), 'Scope': req.get('scope', ''), 'Required': needed,
            'Completed': c['activities'], 'Verified': verified, 'Status': status,
            'Requirement ID': rid,
        })
    return pd.DataFrame(rows), totals


def _my_practical(actor: dict):
    uidv = actor_get(actor, 'user_id')
    st.subheader('My Practical & Witness')
    st.caption('Complete practical requirements, link evidence from real work, and track witness verification. Verified evidence flows into Competency and Authorization readiness automatically.')
    progress, totals = _progress_rows(uidv)
    required = totals['required']
    pct = int(round((totals['verified'] / required) * 100)) if required else 0
    cols = st.columns(5)
    cols[0].metric('Overall Progress', f'{pct}%')
    cols[1].metric('Verified', totals['verified'])
    cols[2].metric('Awaiting Witness', totals['awaiting'])
    cols[3].metric('More Practice', totals['more_practice'])
    cols[4].metric('Not Started', totals['not_started'])
    st.progress(min(100, max(0, pct)) / 100.0)

    st.markdown('### What you need to do next')
    attention = []
    if totals['more_practice']:
        attention.append(f"🔴 {totals['more_practice']} assessment(s) require more practical exposure or development.")
    if totals['awaiting']:
        attention.append(f"🟠 {totals['awaiting']} completed activity/activities are awaiting witness verification.")
    if totals['not_started']:
        attention.append(f"🟠 {totals['not_started']} required observation(s) have not started.")
    if not attention:
        attention.append('🟢 No practical/witness action is currently overdue.')
    for item in attention:
        st.write(item)

    st.markdown('### Practical Requirements')
    if progress.empty:
        st.info('No practical requirement templates are currently assigned to your role/scope. Your Department Manager can configure them in Department Qualification.')
        return
    table(progress.drop(columns=['Requirement ID']), max_rows=200)

    labels = [f"{r['Requirement']} — {r['Scope']} — {r['Requirement ID']}" for _, r in progress.iterrows()]
    selected = st.selectbox('Open requirement', labels, key='pw_my_requirement')
    rid = selected.rsplit(' — ', 1)[-1]
    reqs = db_where('practical_requirement_templates', 'requirement_id = :rid', (('rid', rid),))
    if reqs.empty:
        return
    req = reqs.iloc[0]
    counts = _activity_counts(uidv, rid)
    st.markdown(f"#### {req.get('title','Requirement')}")
    st.write(req.get('description', ''))
    st.caption(f"Required verified observations: {int(req.get('required_observations', 1) or 1)} • Verified: {counts['verified']} • Discipline: {req.get('discipline','General')}")

    acts = db_where('practical_activities', 'user_id = :uid and requirement_id = :rid', (('uid', uidv), ('rid', rid)))
    if not acts.empty:
        st.markdown('##### Previous attempts / activities')
        table(acts[[c for c in ['activity_id','source_type','job_id','vessel_or_project','activity_date','proposed_witness_name','status'] if c in acts.columns]].sort_values('activity_date', ascending=False), max_rows=50)

    if can_action(actor, 'Practical / Witness', 'Create', 'Own'):
        st.markdown('##### Start / Request Practical Activity')
        jobs = db_where('job_requests', 'assigned_user_id = :uid', (('uid', uidv),))
        source_type = st.radio('Activity source', ['Assigned PSB Job', 'Training / Simulation', 'Other Approved Activity'], horizontal=True, key='pw_source')
        job_id = ''
        vessel = ''
        location = ''
        activity_date = date.today()
        if source_type == 'Assigned PSB Job' and not jobs.empty:
            job_labels = [f"{r.get('job_id','')} — {r.get('job_title','')} — {r.get('vessel_name','')}" for _, r in jobs.iterrows()]
            job_sel = st.selectbox('Select Job', job_labels, key='pw_job')
            job_id = job_sel.split(' — ', 1)[0]
            jr = jobs[jobs['job_id'].astype(str) == job_id].iloc[0]
            vessel = str(jr.get('vessel_name', ''))
            location = str(jr.get('location', ''))
            try:
                activity_date = pd.to_datetime(str(jr.get('planned_date',''))).date()
            except Exception:
                activity_date = date.today()
            st.info(f"Job context: {jr.get('job_type','')} • {vessel or 'No vessel'} • {location or 'No location'}")
        else:
            vessel = st.text_input('Vessel / Project / Simulation', key='pw_vessel')
            location = st.text_input('Location', key='pw_location')
            activity_date = st.date_input('Activity date', value=date.today(), key='pw_date')

        scope = str(req.get('scope') or '')
        discipline = str(req.get('discipline') or _scope_discipline(scope))
        configured_roles = set(_jloads(req.get('eligible_witness_roles',''), []))
        witnesses = _eligible_witnesses(uidv, scope, discipline, configured_roles or None)
        if witnesses:
            witness_label = st.selectbox('Proposed Witness — eligible people only', [f'{name} — {wid}' for wid, name, _ in witnesses], key='pw_witness')
            witness_id = witness_label.rsplit(' — ', 1)[-1]
            witness_name = witness_label.rsplit(' — ', 1)[0]
            witness_auth = next((a for w, _, a in witnesses if w == witness_id), '')
            st.success('Witness eligibility verified against role, authorization/technical authority, restriction and scope controls.')
        else:
            witness_id = witness_name = witness_auth = ''
            st.warning('No eligible witness is currently available for this requirement. Contact Technical Management.')

        notes = st.text_area('Activity notes / learning objective', key='pw_activity_notes')
        if st.button('Request Practical Activity', type='primary', disabled=not bool(witness_id), key='pw_request'):
            aid = uid('PRACT')
            db_insert('practical_activities', {
                'activity_id': aid, 'requirement_id': rid, 'user_id': uidv, 'name': actor_get(actor, 'name'),
                'source_type': source_type, 'job_id': job_id, 'vessel_or_project': vessel,
                'job_type': str(req.get('job_type') or ''), 'scope': scope, 'discipline': discipline,
                'activity_date': str(activity_date), 'location': location, 'proposed_witness_id': witness_id,
                'proposed_witness_name': witness_name, 'witness_authorization_id': witness_auth,
                'status': 'Scheduled', 'notes': notes, 'created_by': actor_get(actor, 'name'),
                'created_on': now(), 'updated_on': now(),
            })
            audit('Practical Activity Requested', f'{aid} / {req.get("title", "")}', actor=actor, entity_type='practical_activities', entity_id=aid, reason='Practical requirement activity requested')
            st.success(f'Practical activity {aid} requested.')
            st.rerun()

    # Evidence linking is contextual and does not duplicate files.
    if not acts.empty:
        st.markdown('##### Link Existing Evidence')
        aid = st.selectbox('Activity', acts['activity_id'].astype(str).tolist(), key='pw_evidence_activity')
        files = db_all('files')
        job_id = str(acts[acts['activity_id'].astype(str) == aid].iloc[0].get('job_id', ''))
        linked = files[(files.get('linked_id', pd.Series(dtype=str)).astype(str).isin([aid, job_id]))] if not files.empty else pd.DataFrame()
        if linked.empty:
            st.info('No contextual files are currently linked to this activity/job. Upload evidence in the source Job/Training record rather than duplicating it here.')
        else:
            f_labels = [f"{r.get('file_name','')} — {r.get('file_id','')}" for _, r in linked.iterrows()]
            fsel = st.selectbox('Existing evidence', f_labels, key='pw_existing_evidence')
            fid = fsel.rsplit(' — ', 1)[-1]
            if st.button('Link Evidence', key='pw_link_evidence'):
                exists = db_where('practical_evidence_links', 'activity_id = :aid and file_id = :fid', (('aid', aid), ('fid', fid)))
                if exists.empty:
                    db_insert('practical_evidence_links', {
                        'link_id': uid('PEV'), 'activity_id': aid, 'user_id': uidv, 'source_table': 'files',
                        'source_record_id': fid, 'file_id': fid, 'evidence_type': 'Contextual Evidence',
                        'linked_by': actor_get(actor, 'name'), 'linked_on': now(), 'notes': '',
                    })
                db_update('practical_activities', 'activity_id', aid, {'status': 'Evidence Ready', 'updated_on': now()})
                st.success('Existing evidence linked without duplicating the source document.')
                st.rerun()


def _witness_workspace(actor: dict):
    uidv = actor_get(actor, 'user_id')
    st.subheader('My Witness Assessments')
    st.caption('Only activities explicitly assigned to you as witness are shown. Eligibility is revalidated before an assessment can be submitted.')
    acts = db_all('practical_activities')
    if acts.empty or 'proposed_witness_id' not in acts.columns:
        st.info('No witness assessments are assigned to you.')
        return
    acts = acts[acts['proposed_witness_id'].astype(str) == uidv].copy()
    if acts.empty:
        st.info('No witness assessments are assigned to you.')
        return
    due = 0
    evidence_ready = int(acts.get('status', pd.Series(dtype=str)).astype(str).eq('Evidence Ready').sum())
    completed = int(acts.get('status', pd.Series(dtype=str)).astype(str).eq('Assessed').sum())
    scheduled = int(acts.get('status', pd.Series(dtype=str)).astype(str).isin(['Scheduled','Requested']).sum())
    cols = st.columns(4)
    cols[0].metric('Needs Action', evidence_ready + due)
    cols[1].metric('Scheduled', scheduled)
    cols[2].metric('Evidence Submitted', evidence_ready)
    cols[3].metric('Completed', completed)
    table(acts[[c for c in ['activity_id','name','scope','vessel_or_project','job_id','activity_date','status'] if c in acts.columns]].sort_values('activity_date', ascending=False), max_rows=100)

    labels = [f"{r.get('name','')} — {r.get('scope','')} — {r.get('activity_id','')}" for _, r in acts.iterrows()]
    selected = st.selectbox('Open witness assessment', labels, key='witness_assessment_select')
    aid = selected.rsplit(' — ', 1)[-1]
    act = acts[acts['activity_id'].astype(str) == aid].iloc[0]
    users = db_all('users')
    candidate = users[users['user_id'].astype(str) == uidv]
    if candidate.empty:
        st.error('Witness user profile could not be resolved.')
        return
    ok, reasons, auth_id = _witness_eligibility(candidate.iloc[0], str(act.get('user_id','')), str(act.get('scope','')), str(act.get('discipline','')))
    if not ok:
        st.error('Witness eligibility check failed. Assessment is locked.')
        for reason in reasons:
            st.write('• ' + reason)
        return

    st.success('Witness eligibility verified.')
    tabs = st.tabs(['Overview', 'Assessment', 'Evidence', 'Findings', 'Decision', 'History'])
    with tabs[0]:
        a,b,c = st.columns(3)
        a.metric('Person', str(act.get('name','')))
        b.metric('Scope', str(act.get('scope','')))
        c.metric('Discipline', str(act.get('discipline','')))
        st.write(f"**Activity:** {act.get('vessel_or_project','')}  ")
        st.write(f"**Job:** {act.get('job_id','—')}  ")
        st.write(f"**Date:** {act.get('activity_date','—')}  ")
        st.write(f"**Location:** {act.get('location','—')}  ")
        st.write(f"**Witness authority:** {auth_id or act.get('witness_authorization_id','—')}")
    reqs = db_where('practical_requirement_templates', 'requirement_id = :rid', (('rid', str(act.get('requirement_id',''))),))
    req = reqs.iloc[0] if not reqs.empty else pd.Series(dtype=object)
    criteria = _jloads(req.get('criteria_json', ''), []) or (PLAN_CRITERIA if 'plan' in str(act.get('scope','')).casefold() else SURVEY_CRITERIA)
    scores = {}
    with tabs[1]:
        st.caption('Assess against defined criteria. A simple Pass/Fail decision is intentionally not used.')
        for idx, criterion in enumerate(criteria):
            scores[str(criterion)] = st.radio(str(criterion), ASSESSMENT_OPTIONS, horizontal=True, key=f'witness_crit_{aid}_{idx}')
    with tabs[2]:
        links = db_where('practical_evidence_links', 'activity_id = :aid', (('aid', aid),))
        if links.empty:
            st.warning('No evidence has been linked yet. Assess only what you directly observed and what can be objectively supported.')
        else:
            table(links[[c for c in ['evidence_type','source_table','source_record_id','file_id','linked_by','linked_on'] if c in links.columns]], max_rows=100)
    with tabs[3]:
        strengths = st.text_area('Strengths', key=f'wit_strengths_{aid}')
        development = st.text_area('Development Areas', key=f'wit_dev_{aid}')
        observations = st.text_area('Technical Observations', key=f'wit_obs_{aid}')
        follow_up = st.text_area('Required Follow-up', key=f'wit_follow_{aid}')
    with tabs[4]:
        outcome = st.selectbox('Assessment Outcome', [
            'Competent / Requirement Satisfied', 'Satisfactory Progress', 'More Practice Required',
            'Unsatisfactory', 'Assessment Invalid / Could Not Observe'
        ], key=f'wit_outcome_{aid}')
        declarations = {
            'observed': st.checkbox('I directly observed sufficient elements of this activity.', key=f'd1_{aid}'),
            'authorized': st.checkbox('I am authorized within the relevant technical scope.', key=f'd2_{aid}'),
            'objective': st.checkbox('I assessed the person objectively against the defined criteria.', key=f'd3_{aid}'),
            'conflict_disclosed': st.checkbox('I have disclosed any relevant conflict of interest.', key=f'd4_{aid}'),
        }
        compliance_issue = st.checkbox('A separate compliance/nonconformity issue was observed during this activity.', key=f'wit_compliance_{aid}')
        compliance_description = st.text_area('Compliance issue description', key=f'wit_compliance_desc_{aid}', disabled=not compliance_issue)
        compliance_severity = st.selectbox('Compliance severity', ['Low','Medium','High','Critical'], index=1, key=f'wit_compliance_sev_{aid}', disabled=not compliance_issue)
        if st.button('Submit Witness Assessment', type='primary', disabled=not all(declarations.values()), key=f'wit_submit_{aid}'):
            if not can_action(actor, 'Practical / Witness', 'Review', 'Assigned') and not can_action(actor, 'Practical / Witness', 'Review', 'Department') and not can_action(actor, 'Practical / Witness', 'Review', 'Organization-wide'):
                st.error('You do not have witness-review permission.')
            else:
                ass_id = uid('PASS')
                db_insert('practical_assessments', {
                    'assessment_id': ass_id, 'activity_id': aid, 'requirement_id': str(act.get('requirement_id','')),
                    'user_id': str(act.get('user_id','')), 'name': str(act.get('name','')), 'witness_id': uidv,
                    'witness_name': actor_get(actor, 'name'), 'witness_authorization_id': auth_id or str(act.get('witness_authorization_id','')),
                    'witness_scope': str(act.get('scope','')), 'assessed_on': now(), 'criteria_scores_json': json.dumps(scores),
                    'strengths': strengths, 'development_areas': development, 'technical_observations': observations,
                    'follow_up': follow_up, 'outcome': outcome, 'declaration_json': json.dumps(declarations),
                    'status': 'Submitted', 'amendment_of': '', 'created_on': now(), 'updated_on': now(),
                })
                next_status = 'Assessed' if outcome in COMPLETE_OUTCOMES else 'More Practice' if outcome in DEVELOPMENT_OUTCOMES else 'Closed'
                db_update('practical_activities', 'activity_id', aid, {'status': next_status, 'updated_on': now()})
                audit('Witness Assessment Submitted', f'{ass_id} / {outcome}', actor=actor, entity_type='practical_assessments', entity_id=ass_id, reason='Controlled practical witness assessment')
                if compliance_issue and compliance_description.strip():
                    ncr_scope = next((sc for sc in ['Assigned','Department','Organization-wide'] if can_action(actor, 'NCR / Corrective Action', 'Create', sc)), None)
                    if ncr_scope:
                        ncr_id = uid('NCR')
                        db_insert('competency_ncrs', {
                            'ncr_id': ncr_id, 'user_id': str(act.get('user_id','')), 'name': str(act.get('name','')),
                            'source': 'Practical / Witness', 'source_record_id': ass_id, 'scope': str(act.get('scope','')),
                            'ncr_type': 'Compliance Observation', 'category': 'Witness Assessment',
                            'description': compliance_description.strip(), 'severity': compliance_severity,
                            'likelihood': 2, 'risk_score': {'Low':2,'Medium':4,'High':6,'Critical':8}.get(compliance_severity,4),
                            'priority': compliance_severity, 'impact_on_authorization': 'Review Required', 'status': 'Open',
                            'incident_date': str(act.get('activity_date') or today()), 'containment_action': '', 'root_cause': '',
                            'corrective_action': '', 'owner_id': '', 'owner_name': '', 'due_date': str(date.today()+timedelta(days=30)),
                            'verification_status': 'Pending', 'raised_by': actor_get(actor,'name'), 'raised_on': now(), 'updated_on': now(),
                        })
                        audit('NCR Raised From Witness Assessment', f'{ncr_id} linked to {ass_id}', actor=actor, entity_type='competency_ncrs', entity_id=ncr_id, reason='Compliance issue observed during witness assessment')
                    else:
                        # Lack of NCR permission must not turn a development assessment into an unauthorized write.
                        managers = db_all('users')
                        managers = managers[managers.get('role', pd.Series(dtype=str)).astype(str).isin(['Department Manager','QMR'])] if not managers.empty else pd.DataFrame()
                        for _, manager in managers.head(5).iterrows():
                            create_notification(str(manager.get('user_id','')), 'Witness compliance issue requires NCR review', f'{act.get("name","")} / {act.get("scope","")} / assessment {ass_id}: {compliance_description.strip()}', 'Action Required')

                if outcome in {'More Practice Required', 'Unsatisfactory', 'Satisfactory Progress'}:
                    # The assessment remains the authoritative source of the development need.
                    # Notify the assigned Trainer, who also owns mentoring/development support and can
                    # promote the witness feedback into the existing Development Plan.
                    people = db_where('users', 'user_id = :uid', (('uid', str(act.get('user_id',''))),))
                    if not people.empty:
                        person = people.iloc[0]
                        tutor_id = str(person.get('trainer_id') or person.get('tutor_id') or person.get('mentor_id') or '')
                        if tutor_id:
                            create_notification(tutor_id, 'Practical development action required', f'{act.get("name","")} / {act.get("scope","")}: {follow_up or development or outcome}', 'Action Required')
                    create_notification(str(act.get('user_id','')), 'Practical assessment follow-up', f'{act.get("scope","")}: {follow_up or development or outcome}', 'Action Required')
                st.success('Witness assessment submitted. Competency readiness now consumes this verified practical evidence.')
                st.rerun()
    with tabs[5]:
        history = db_where('practical_assessments', 'activity_id = :aid', (('aid', aid),))
        if history.empty:
            st.info('No prior assessment history.')
        else:
            table(history[[c for c in ['assessment_id','witness_name','assessed_on','outcome','status','amendment_of'] if c in history.columns]].sort_values('assessed_on', ascending=False), max_rows=100)


def _trainer_development_view(actor: dict):
    st.subheader('Assigned Learner Practical Development')
    users = db_all('users')
    uidv = actor_get(actor, 'user_id')
    assigned = users[
        (users.get('trainer_id', pd.Series(dtype=str)).astype(str) == uidv)
    ] if not users.empty else pd.DataFrame()
    if assigned.empty:
        st.info('No trainees are currently assigned to you.')
        return
    person_label = st.selectbox('Assigned Learner', [f"{r.get('name','')} — {r.get('user_id','')}" for _, r in assigned.iterrows()], key='trainer_practical_person')
    person_id = person_label.rsplit(' — ', 1)[-1]
    person = assigned[assigned['user_id'].astype(str) == person_id].iloc[0]
    progress, totals = _progress_rows(person_id)
    required = totals['required']
    pct = int(round(100 * totals['verified']/required)) if required else 0
    st.metric('Overall Practical Progress', f'{pct}%')
    if not progress.empty:
        table(progress.drop(columns=['Requirement ID']), max_rows=100)
    recent = db_where('practical_assessments', 'user_id = :uid', (('uid', person_id),))
    if not recent.empty:
        development = recent[recent.get('outcome', pd.Series(dtype=str)).astype(str).isin(DEVELOPMENT_OUTCOMES)]
        if not development.empty:
            st.warning('Development attention is required based on witness feedback.')
            table(development[[c for c in ['assessment_id','assessed_on','witness_name','outcome','development_areas','follow_up'] if c in development.columns]].sort_values('assessed_on', ascending=False), max_rows=20)
            st.caption('Witness feedback remains authoritative here. Promote it into Development Plans only when you accept it as a formal development action.')
            assessment_ids = development['assessment_id'].astype(str).tolist() if 'assessment_id' in development.columns else []
            if assessment_ids:
                ass_id = st.selectbox('Witness assessment to add to Development Plan', assessment_ids, key='tutor_dev_assessment')
                ass_row = development[development['assessment_id'].astype(str) == ass_id].iloc[0]
                if st.button('Add to Development Plan', type='primary', key='tutor_add_dev_plan'):
                    existing = db_where('development_plans', 'user_id = :uid and source_gap = :src', (('uid', person_id), ('src', f'Witness Assessment {ass_id}')))
                    if existing.empty:
                        db_insert('development_plans', {
                            'plan_id': uid('DEV'), 'user_id': person_id, 'name': str(person.get('name','')),
                            'trainee_path': str(person.get('trainee_path','')), 'mentor_id': uidv, 'mentor_name': actor_get(actor,'name'),
                            'competency_scope': str(ass_row.get('witness_scope','')), 'month_no': date.today().month,
                            'activity': str(ass_row.get('follow_up') or 'Additional practical exposure required'),
                            'target_date': str(date.today()+timedelta(days=30)), 'status': 'Active',
                            'mentor_comments': str(ass_row.get('development_areas') or ass_row.get('technical_observations') or ''),
                            'plan_group_id': '', 'plan_title': 'Practical Development', 'objective': 'Close witness-assessment development need',
                            'development_type': 'Practical / Witness', 'priority': 'High', 'owner_id': person_id, 'owner_name': str(person.get('name','')),
                            'progress_percent': 0, 'evidence_required': 'Yes', 'evidence_status': 'Pending', 'review_date': str(date.today()+timedelta(days=30)),
                            'source_gap': f'Witness Assessment {ass_id}', 'success_criteria': 'Subsequent practical assessment demonstrates competency',
                            'created_on': now(), 'updated_on': now(), 'updated_by': actor_get(actor,'name'),
                        })
                        audit('Witness Development Action Added', f'{ass_id} added to Development Plans', actor=actor, entity_type='development_plans', entity_id=ass_id, reason='Trainer accepted witness follow-up')
                        st.success('Development action added without duplicating witness evidence.')
                    else:
                        st.info('This witness assessment is already linked to a Development Plan action.')


def _governance(actor: dict):
    st.subheader('Practical / Witness Governance')
    st.caption('Configure practical requirements once, monitor witness capacity, assignments, exceptions and readiness. The assessment evidence remains in the practical records and is consumed by Competency/Authorization.')
    reqs = db_all('practical_requirement_templates')
    acts = db_all('practical_activities')
    ass = db_all('practical_assessments')
    users = db_all('users')
    cols = st.columns(6)
    cols[0].metric('Requirements', len(reqs))
    cols[1].metric('Active Activities', int(acts.get('status', pd.Series(dtype=str)).astype(str).isin(['Requested','Scheduled','Evidence Ready']).sum()) if not acts.empty else 0)
    cols[2].metric('Pending Assessment', int(acts.get('status', pd.Series(dtype=str)).astype(str).eq('Evidence Ready').sum()) if not acts.empty else 0)
    cols[3].metric('More Practice', int(ass.get('outcome', pd.Series(dtype=str)).astype(str).isin(DEVELOPMENT_OUTCOMES).sum()) if not ass.empty else 0)
    cols[4].metric('Witness Pool', int(users.get('role', pd.Series(dtype=str)).astype(str).isin(WITNESS_ROLES).sum()) if not users.empty else 0)
    cols[5].metric('Eligibility Exceptions', 0)

    tabs = st.tabs(['Overview', 'Requirements', 'People', 'Witnesses', 'Assignments', 'Exceptions', 'Analytics'])
    with tabs[0]:
        if not acts.empty:
            table(acts[[c for c in ['activity_id','name','scope','discipline','proposed_witness_name','activity_date','status'] if c in acts.columns]].sort_values('activity_date', ascending=False), max_rows=150)
        else:
            st.info('No practical activities have been opened.')
    with tabs[1]:
        if not reqs.empty:
            table(reqs[[c for c in ['requirement_code','title','target_role','trainee_path','scope','discipline','required_observations','active'] if c in reqs.columns]], max_rows=200)
        st.markdown('#### Add / Update Requirement Library')
        if can_action(actor, 'Practical / Witness', 'Review', 'Organization-wide'):
            with st.form('practical_requirement_create', clear_on_submit=True):
                code = st.text_input('Requirement Code', placeholder='PR-MACH-003')
                title = st.text_input('Requirement Title', placeholder='Machinery Survey')
                description = st.text_area('Requirement / Expected Demonstration')
                target_role = st.selectbox('Target Role', ['All','Trainee','On Probation','Surveyor','NSC Surveyor','In-Service Surveyor','Industrial Surveyor','Plan Appraiser'])
                trainee_path = st.text_input('Trainee Path', placeholder='All or exact trainee path', value='All')
                scope = st.selectbox('Scope', ['All'] + SCOPES)
                job_type = st.selectbox('Job Type', JOB_TYPES)
                discipline = st.text_input('Discipline', value=_scope_discipline(scope))
                observations = st.number_input('Required Verified Observations', 1, 20, 3)
                criteria_default = PLAN_CRITERIA if 'plan' in scope.casefold() else SURVEY_CRITERIA
                criteria = st.text_area('Assessment Criteria — one per line', value='\n'.join(criteria_default))
                eligible_roles = st.multiselect('Eligible Witness Roles', sorted(WITNESS_ROLES), default=sorted(SENIOR_WITNESS_ROLES))
                save = st.form_submit_button('Save Requirement', type='primary')
            if save and code.strip() and title.strip():
                existing = db_where('practical_requirement_templates', 'requirement_code = :code', (('code', code.strip()),))
                payload = {
                    'requirement_code': code.strip(), 'title': title.strip(), 'description': description,
                    'target_role': target_role, 'trainee_path': trainee_path or 'All', 'scope': scope,
                    'job_type': job_type, 'discipline': discipline or _scope_discipline(scope),
                    'required_observations': int(observations),
                    'criteria_json': json.dumps([x.strip() for x in criteria.splitlines() if x.strip()]),
                    'eligible_witness_roles': json.dumps(eligible_roles), 'active': 'Yes',
                    'updated_on': now(),
                }
                if existing.empty:
                    payload.update({'requirement_id': uid('PREQ'), 'created_by': actor_get(actor,'name'), 'created_on': now()})
                    db_insert('practical_requirement_templates', payload)
                else:
                    db_update('practical_requirement_templates', 'requirement_id', str(existing.iloc[0]['requirement_id']), payload)
                audit('Practical Requirement Saved', code.strip(), actor=actor, entity_type='practical_requirement_templates', entity_id=code.strip(), reason='Requirement library governance')
                st.success('Requirement saved.')
                st.rerun()
    with tabs[2]:
        people_rows=[]
        if not users.empty:
            for _, u in users.iterrows():
                if str(u.get('role','')) not in {'Trainee','On Probation','Surveyor','NSC Surveyor','In-Service Surveyor','Industrial Surveyor','Plan Appraiser'}:
                    continue
                _, t = _progress_rows(str(u.get('user_id','')))
                req=t['required']; pct=int(round(100*t['verified']/req)) if req else 0
                people_rows.append({'Employee':u.get('name',''),'Role':u.get('role',''),'Progress':f'{pct}%','Verified':t['verified'],'Required':req,'Awaiting':t['awaiting'],'More Practice':t['more_practice']})
        table(pd.DataFrame(people_rows), max_rows=250) if people_rows else st.info('No people are currently within practical development scope.')
    with tabs[3]:
        witness_rows=[]
        if not users.empty:
            for _, w in users[users.get('role', pd.Series(dtype=str)).astype(str).isin(WITNESS_ROLES)].iterrows():
                wid=str(w.get('user_id',''))
                assigned = acts[acts.get('proposed_witness_id', pd.Series(dtype=str)).astype(str)==wid] if not acts.empty else pd.DataFrame()
                witness_rows.append({'Witness':w.get('name',''),'Role':w.get('role',''),'Active Assignments':int(assigned.get('status',pd.Series(dtype=str)).astype(str).isin(['Scheduled','Evidence Ready']).sum()) if not assigned.empty else 0,'Completed':int(assigned.get('status',pd.Series(dtype=str)).astype(str).eq('Assessed').sum()) if not assigned.empty else 0,'Status':'High Load' if len(assigned)>=6 else 'Available'})
        table(pd.DataFrame(witness_rows), max_rows=150) if witness_rows else st.info('No eligible witness roles are configured.')
    with tabs[4]:
        if not acts.empty:
            table(acts[[c for c in ['activity_id','name','scope','discipline','proposed_witness_name','activity_date','status'] if c in acts.columns]], max_rows=200)
    with tabs[5]:
        invalid=[]
        if not acts.empty and not users.empty:
            for _, a in acts.iterrows():
                wid=str(a.get('proposed_witness_id',''))
                candidate=users[users['user_id'].astype(str)==wid]
                if candidate.empty:
                    invalid.append({'Activity':a.get('activity_id',''),'Person':a.get('name',''),'Issue':'Assigned witness no longer exists'})
                    continue
                ok,reasons,_=_witness_eligibility(candidate.iloc[0],str(a.get('user_id','')),str(a.get('scope','')),str(a.get('discipline','')))
                if not ok:
                    invalid.append({'Activity':a.get('activity_id',''),'Person':a.get('name',''),'Issue':'; '.join(reasons)})
        table(pd.DataFrame(invalid), max_rows=100) if invalid else st.success('No witness eligibility exceptions detected.')
    with tabs[6]:
        if not ass.empty:
            summary=ass.groupby('outcome',dropna=False).size().reset_index(name='Count')
            table(summary, max_rows=30)
        else:
            st.info('Assessment analytics will appear after witness decisions are recorded.')


def practical_page(actor: dict):
    """Role-aware practical training and witness assessment workspace."""
    st.header('Practical / Witness')
    role = actor_get(actor, 'role')
    choices = workspace_modes_for_role(role)
    if not choices:
        st.info('No practical/witness workspace is configured for this role.')
        return
    selected = st.segmented_control('Workspace', choices, default=choices[0], key='practical_workspace_mode') if len(choices)>1 else choices[0]
    if selected == 'My Practical & Witness':
        _my_practical(actor)
    elif selected == 'My Witness Assessments':
        _witness_workspace(actor)
    elif selected == 'Assigned Learner Progress':
        _trainer_development_view(actor)
    else:
        _governance(actor)


def my_witness_assessments_page(actor: dict):
    st.header('My Assessments')
    from psb_app.pages.qualification import independent_practical_assessor_panel
    independent_practical_assessor_panel(actor)
    st.divider()
    st.subheader('Practical / Witness Assessments')
    _witness_workspace(actor)


def practical_governance_page(actor: dict):
    st.header('Practical / Witness Governance')
    _governance(actor)
