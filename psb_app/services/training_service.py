"""Extracted service boundary from the legacy runtime.
The module consumes the established runtime context for compatibility.
"""
from __future__ import annotations
from psb_app.legacy_runtime import (
    clean,
    db_all,
    db_where,
    now,
    pd,
    random,
    re,
    today,
    uid,
)

def calculate_training_progress(r: pd.Series) -> tuple[int, str, str]:
    """Calculate learner completion without making certificate issuance a prerequisite.

    Completion is based on the actual course requirements. Attendance/recording is
    required, and an assessment is required when configured. Learning materials
    contribute to progress but are not falsely treated as final completion on their own.
    """
    parts = []
    parts.append(r.get('live_attendance') in ['Present', 'Recording Viewed'])
    for key in ('slides_opened', 'video_opened', 'lms_completed'):
        parts.append(r.get(key) == 'Yes')
    assessment_required = clean(r.get('assessment_required', 'Yes')) not in ['No', 'False', '0']
    if assessment_required:
        parts.append(r.get('test_status') == 'Passed')
    else:
        parts.append(True)
    progress = int(round(sum((bool(x) for x in parts)) / max(len(parts), 1) * 100))
    complete = bool(parts[0]) and (not assessment_required or r.get('test_status') == 'Passed')
    status = 'Completed' if complete else 'In Progress' if progress > 0 else 'Pending'
    completed_on = today() if complete and (not clean(r.get('completed_on'))) else clean(r.get('completed_on'))
    return (progress, status, completed_on)

def training_complete_for_user(user_id: str) -> bool:
    assigned = db_where('training_records', 'user_id = :user_id', (('user_id', user_id),))
    return not assigned.empty and len(assigned[assigned['test_status'] != 'Passed']) == 0

def get_matrix_for_scope(scope: str) -> pd.Series | None:
    matrix = db_all('authorization_matrix')
    m = matrix[(matrix['scope'] == scope) & (matrix['active'] == 'Yes')] if not matrix.empty else pd.DataFrame()
    if m.empty:
        return None
    return m.iloc[0]

def _training_requirement_status(user_id: str, trainee_path: str, department_text: str='') -> tuple[int, int, list[str]]:
    """Return required/completed mandatory training counts without duplicating Training records."""
    reqs = db_all('training_requirements')
    records = db_all('training_records')
    if reqs.empty:
        return (0, 0, ['No training requirements are configured.'])
    reqs = reqs[reqs.get('active', 'Yes').astype(str).str.lower().isin(['yes', 'true', '1', 'active'])] if 'active' in reqs.columns else reqs
    mandatory = reqs[reqs.get('mandatory', 'No').astype(str).str.lower().isin(['yes', 'true', '1'])] if 'mandatory' in reqs.columns else reqs
    relevant = []
    dept_tokens = {x.strip().lower() for x in str(department_text).replace(';', ',').split(',') if x.strip()}
    for _, r in mandatory.iterrows():
        dept = str(r.get('department', 'All') or 'All').strip()
        role = str(r.get('role', 'All') or 'All').strip()
        path = str(r.get('trainee_path', 'All') or 'All').strip()
        dept_ok = dept.lower() in ('', 'all') or dept.lower() in dept_tokens
        path_ok = path.lower() in ('', 'all') or path.lower() == str(trainee_path or '').lower()
        if dept_ok and path_ok:
            relevant.append(r)
    if not relevant:
        return (0, 0, ['No mandatory training requirements apply to this employee and scope.'])
    completed = 0
    gaps = []
    for r in relevant:
        module_id = str(r.get('module_id', '') or '')
        title = str(r.get('requirement_name', module_id) or module_id)
        if records.empty:
            gaps.append(title)
            continue
        rr = records[(records.get('user_id', '').astype(str) == str(user_id)) & (records.get('training_id', '').astype(str) == module_id)].copy()
        passed = False
        if not rr.empty:
            passed = bool(((rr.get('test_status', '').astype(str).str.lower() == 'passed') | (rr.get('status', '').astype(str).str.lower() == 'completed') | (pd.to_numeric(rr.get('progress', 0), errors='coerce').fillna(0) >= 100)).any())
        if passed:
            completed += 1
        else:
            gaps.append(title)
    return (len(relevant), completed, gaps)

def readiness(user_id: str, scope: str) -> tuple[bool, list[str]]:
    """Calculate competency readiness from authoritative evidence sources."""
    matrix = get_matrix_for_scope(scope)
    if matrix is None:
        return (False, ['No authorization/competency matrix is defined for this scope.'])
    users = db_all('users')
    u = users[users['user_id'].astype(str) == str(user_id)].iloc[0] if not users.empty and (users['user_id'].astype(str) == str(user_id)).any() else None
    trainee_path = str(u.get('trainee_path', '') if u is not None else '')
    dept_text = str(u.get('department', '') if u is not None else '') + ',' + str(u.get('departments', '') if u is not None else '')
    gaps = []
    req_total, req_completed, training_gaps = _training_requirement_status(user_id, trainee_path, dept_text)
    if req_total and req_completed < req_total:
        gaps.append(f'Mandatory training incomplete: {req_completed}/{req_total} completed.')
        gaps.extend([f'Training gap: {g}' for g in training_gaps[:8]])
    elif req_total == 0 and training_gaps:
        gaps.extend(training_gaps)
    witness = db_all('witness_surveys')
    legacy_witness_count = len(witness[(witness['user_id'].astype(str) == str(user_id)) & (witness['scope'].astype(str) == str(scope)) & (witness['outcome'].astype(str) == 'Pass')]) if not witness.empty else 0
    professional = db_all('practical_assessments')
    professional_count = 0
    if not professional.empty:
        pf = professional[(professional['user_id'].astype(str) == str(user_id)) & (professional.get('witness_scope', pd.Series(dtype=str)).astype(str) == str(scope)) & (professional.get('outcome', pd.Series(dtype=str)).astype(str) == 'Competent / Requirement Satisfied')]
        professional_count = len(pf)
    # Once the professional workflow has evidence, it becomes authoritative for witness counts;
    # otherwise legacy witness rows remain backward-compatible for existing records.
    witness_count = professional_count if professional_count else legacy_witness_count
    required_witness = int(matrix.get('required_witness_count', 0) or 0)
    if witness_count < required_witness:
        gaps.append(f'Witness assessments incomplete: {witness_count}/{required_witness}.')

    # Configured practical requirement templates are stronger than a raw count because each
    # requirement can demand multiple verified observations. They feed the same readiness result.
    templates = db_all('practical_requirement_templates')
    if not templates.empty:
        active_templates = templates[templates.get('active', pd.Series(dtype=str)).astype(str).str.casefold().isin(['yes','active','true','1'])]
        scoped = active_templates[active_templates.get('scope', pd.Series(dtype=str)).astype(str).isin(['', 'All', str(scope)])]
        for _, req in scoped.iterrows():
            needed = int(req.get('required_observations', 1) or 1)
            rid = str(req.get('requirement_id',''))
            if professional.empty:
                completed = 0
            else:
                completed = len(professional[(professional['user_id'].astype(str) == str(user_id)) & (professional.get('requirement_id', pd.Series(dtype=str)).astype(str) == rid) & (professional.get('outcome', pd.Series(dtype=str)).astype(str) == 'Competent / Requirement Satisfied')])
            if completed < needed:
                gaps.append(f"Practical requirement incomplete: {req.get('title','Requirement')} {completed}/{needed} verified.")
    sup = db_all('supervised_activities')
    passed_kinds = ['Supervised Survey', 'Independent Audit', 'Supervised Rule Exercise']
    sup_count = len(sup[(sup['user_id'].astype(str) == str(user_id)) & (sup['scope'].astype(str) == str(scope)) & sup['activity_kind'].astype(str).isin(passed_kinds) & (sup['outcome'].astype(str) == 'Pass')]) if not sup.empty else 0
    required_sup = int(matrix.get('required_supervised_count', 0) or 0)
    if sup_count < required_sup:
        gaps.append(f'Supervised activities incomplete: {sup_count}/{required_sup}.')
    joint_count = len(sup[(sup['user_id'].astype(str) == str(user_id)) & (sup['scope'].astype(str) == str(scope)) & (sup['activity_kind'].astype(str) == 'Joint Plan Review') & (sup['outcome'].astype(str) == 'Pass')]) if not sup.empty else 0
    required_joint = int(matrix.get('required_joint_plan_count', 0) or 0)
    if joint_count < required_joint:
        gaps.append(f'Joint plan reviews incomplete: {joint_count}/{required_joint}.')
    indep_count = len(sup[(sup['user_id'].astype(str) == str(user_id)) & (sup['scope'].astype(str) == str(scope)) & (sup['activity_kind'].astype(str) == 'Independent Plan Review') & (sup['outcome'].astype(str) == 'Pass')]) if not sup.empty else 0
    required_indep = int(matrix.get('required_independent_plan_count', 0) or 0)
    if indep_count < required_indep:
        gaps.append(f'Independent plan reviews incomplete: {indep_count}/{required_indep}.')
    plans = db_all('development_plans')
    if not plans.empty:
        open_plans = plans[(plans['user_id'].astype(str) == str(user_id)) & (plans.get('competency_scope', '').astype(str) == str(scope)) & plans.get('status', '').astype(str).isin(['Draft', 'Active', 'At Risk', 'On Hold'])]
        if not open_plans.empty:
            gaps.append(f'{len(open_plans)} open development-plan item(s) remain for this scope.')
    return (len(gaps) == 0, gaps)

def generate_mcqs(training_id: str, text_value: str, count: int) -> pd.DataFrame:
    """Generate grounded professional MCQ drafts from controlled training material.

    If an OpenAI-compatible endpoint is configured through PSB_AI_MCQ_ENDPOINT,
    PSB_AI_MCQ_API_KEY and PSB_AI_MCQ_MODEL, the service asks that model for a
    strict JSON question set grounded only in the supplied source. The Trainer
    must still review and explicitly publish the drafts. If no model is
    configured (or the provider fails), a deterministic local grounded generator
    is used so development/demo environments remain functional without secrets.
    """
    source = clean(text_value)
    if not source or int(count or 0) <= 0:
        return pd.DataFrame()

    def _normalize(rows):
        out=[]
        for item in rows or []:
            try:
                q=clean(item.get('question',''))
                opts=[clean(item.get(k,'')) for k in ('option_a','option_b','option_c','option_d')]
                ans=clean(item.get('correct_answer',''))
                if not q or any(not x for x in opts) or ans not in opts:
                    continue
                out.append({'question_id':uid('Q'),'training_id':training_id,'question':q,'option_a':opts[0],'option_b':opts[1],'option_c':opts[2],'option_d':opts[3],'correct_answer':ans,'marks':int(item.get('marks') or 1),'generated_on':now()})
            except Exception:
                continue
        return pd.DataFrame(out[:int(count)])

    # Optional state-of-the-art provider. No learner content is sent anywhere
    # unless the deployment operator explicitly configures these environment vars.
    try:
        import os, json as _json, urllib.request
        endpoint=clean(os.getenv('PSB_AI_MCQ_ENDPOINT',''))
        api_key=clean(os.getenv('PSB_AI_MCQ_API_KEY',''))
        model=clean(os.getenv('PSB_AI_MCQ_MODEL',''))
        if endpoint and api_key and model:
            linked_files=db_where('files','linked_table = :lt AND linked_id = :lid',(('lt','trainings'),('lid',training_id)))
            classifications=set(linked_files.get('information_classification',pd.Series(dtype=str)).fillna('Internal').astype(str).tolist()) if not linked_files.empty else {'Internal'}
            sensitive=bool(classifications & {'Confidential','Restricted Technical'})
            allow_sensitive=os.getenv('PSB_ALLOW_EXTERNAL_AI_FOR_SENSITIVE','false').strip().lower() in {'1','true','yes','on'}
            if sensitive and not allow_sensitive:
                raise RuntimeError('External AI processing is blocked for Confidential/Restricted Technical training material.')
            prompt=(
                'You are creating a professional maritime qualification MCQ assessment. '
                'Use ONLY the controlled source text below. Do not invent requirements. '
                f'Create exactly {int(count)} single-best-answer questions. Mix knowledge, application and scenario reasoning. '
                'Return ONLY a JSON array. Each object must contain question, option_a, option_b, option_c, option_d, '
                'correct_answer (exactly one option text), and marks=1. Avoid trick wording and duplicated questions.\n\n'
                'CONTROLLED SOURCE:\n'+source[:50000]
            )
            payload={'model':model,'messages':[{'role':'system','content':'Generate auditable, source-grounded professional assessments.'},{'role':'user','content':prompt}],'temperature':0.2}
            req=urllib.request.Request(endpoint,data=_json.dumps(payload).encode('utf-8'),headers={'Authorization':f'Bearer {api_key}','Content-Type':'application/json'},method='POST')
            with urllib.request.urlopen(req,timeout=45) as resp:
                body=_json.loads(resp.read().decode('utf-8'))
            content=body.get('choices',[{}])[0].get('message',{}).get('content','')
            content=content.strip()
            if content.startswith('```'):
                content=re.sub(r'^```(?:json)?\s*|\s*```$','',content,flags=re.I|re.S)
            parsed=_json.loads(content)
            ai=_normalize(parsed)
            if len(ai)>=min(5,int(count)):
                ai.attrs['generation_method']='Configured AI model ('+model+')'
                return ai
    except Exception:
        pass

    # Deterministic grounded fallback. It creates contextual questions from
    # sentences in the supplied controlled material and never fabricates facts.
    stop={'training','system','should','shall','which','there','their','about','through','during','after','before','within','using','based','these','those','where','under','requirements','procedure','document','classification','society','survey','surveyor','appraisal','management','development'}
    keys=[]
    for w in re.findall(r'\b[A-Za-z][A-Za-z\-]{4,}\b',source):
        x=w.lower(); t=x.title()
        if x not in stop and t not in keys: keys.append(t)
    sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',source.replace('\n',' ')) if 45<=len(s.strip())<=300]
    if len(keys)<4 or not sentences:
        return pd.DataFrame()
    # stable order for same source/training to support auditable regeneration
    import hashlib
    seed=int(hashlib.sha256((training_id+'|'+source).encode('utf-8')).hexdigest()[:12],16)
    rng=random.Random(seed)
    rng.shuffle(sentences)
    rows=[]
    for sentence in sentences:
        if len(rows)>=int(count): break
        candidates=[k for k in keys if re.search(rf'\b{re.escape(k)}\b',sentence,re.I)]
        if not candidates: continue
        ans=candidates[0]
        distractors=[k for k in keys if k.casefold()!=ans.casefold()]
        if len(distractors)<3: continue
        opts=rng.sample(distractors,3)+[ans]; rng.shuffle(opts)
        rows.append({'question':re.sub(rf'\b{re.escape(ans)}\b','__________',sentence,flags=re.I,count=1),'option_a':opts[0],'option_b':opts[1],'option_c':opts[2],'option_d':opts[3],'correct_answer':ans,'marks':1})
    local=_normalize(rows)
    local.attrs['generation_method']='Controlled local grounded generator'
    return local

