"""Source-backed controlled publication of the qualification curriculum.

This startup job intentionally bypasses user/actor-scoped repository helpers. It
reads and writes through the persistent database gateway because publication is a
system maintenance task, not a user-scoped page action.

Rules:
- never publish the historical duplicate foam course;
- require at least one learning item;
- require the configured minimum MCQs when assessment is required;
- generate missing MCQs only from the course's own extracted controlled files;
- exclude exam/answer/result/certificate/attendance files from MCQ source text;
- preserve all learner records, completions, attestations and authorizations.
"""
from __future__ import annotations

import hashlib
import random
import re
import uuid

import pandas as pd

from core.database_gateway import exec_sql, query_sql

_RAN = False
_EXCLUDE_SOURCE_TOKENS = (
    'answer', 'solved', 'exam', 'result', 'certificate', 'attendance',
    'evaluation_form', 'attestation', 'issued_certificate',
)
_STOP = {
    'training','system','should','shall','which','there','their','about','through',
    'during','after','before','within','using','based','these','those','where','under',
    'requirements','procedure','document','classification','society','survey',
    'surveyor','appraisal','management','development','information','equipment',
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _clean(value) -> str:
    if value is None:
        return ''
    try:
        if pd.isna(value):
            return ''
    except Exception:
        pass
    return str(value)


def _course_source(training_id: str, files: pd.DataFrame) -> str:
    if files.empty:
        return ''
    rows = files[(files['linked_table'].astype(str) == 'trainings') & (files['linked_id'].astype(str) == training_id)].copy()
    if rows.empty:
        return ''
    parts: list[str] = []
    for _, row in rows.sort_values('sequence_no').iterrows():
        name = _clean(row.get('file_name')).casefold()
        if any(token in name for token in _EXCLUDE_SOURCE_TOKENS):
            continue
        text_value = _clean(row.get('extracted_text')).strip()
        if len(text_value) >= 120:
            parts.append(text_value)
        if sum(len(x) for x in parts) >= 50000:
            break
    return '\n\n'.join(parts)[:50000]


def _generate_grounded_mcqs(training_id: str, source: str, count: int) -> list[dict]:
    """Deterministic source-only generator used for broad curriculum preparation.

    This never introduces facts that are absent from the controlled course source.
    Trainer review remains available in the normal course-control workspace.
    """
    source = _clean(source)
    if len(source) < 500 or count <= 0:
        return []
    keys: list[str] = []
    for word in re.findall(r'\b[A-Za-z][A-Za-z\-]{4,}\b', source):
        lowered = word.casefold()
        display = word.strip()
        if lowered not in _STOP and display.casefold() not in {x.casefold() for x in keys}:
            keys.append(display)
        if len(keys) >= 220:
            break
    sentences = [
        s.strip() for s in re.split(r'(?<=[.!?])\s+', source.replace('\n', ' '))
        if 55 <= len(s.strip()) <= 280
    ]
    if len(keys) < 4 or not sentences:
        return []
    seed = int(hashlib.sha256((training_id + '|' + source).encode('utf-8')).hexdigest()[:12], 16)
    rng = random.Random(seed)
    rng.shuffle(sentences)
    rows: list[dict] = []
    seen: set[str] = set()
    for sentence in sentences:
        if len(rows) >= count:
            break
        candidates = [k for k in keys if re.search(rf'\b{re.escape(k)}\b', sentence, re.I)]
        if not candidates:
            continue
        # Prefer a meaningful technical term rather than a generic word.
        candidates.sort(key=lambda x: (-len(x), x.casefold()))
        answer = candidates[0]
        question = re.sub(rf'\b{re.escape(answer)}\b', '__________', sentence, flags=re.I, count=1)
        if question in seen:
            continue
        distractors = [k for k in keys if k.casefold() != answer.casefold() and len(k) >= 5]
        if len(distractors) < 3:
            continue
        options = rng.sample(distractors, 3) + [answer]
        rng.shuffle(options)
        rows.append({
            'question': question,
            'option_a': options[0], 'option_b': options[1],
            'option_c': options[2], 'option_d': options[3],
            'correct_answer': answer, 'marks': 1,
        })
        seen.add(question)
    return rows


def _learning_item_count(training: dict, training_id: str, files: pd.DataFrame, resources: pd.DataFrame) -> int:
    file_count = int(((files['linked_table'].astype(str) == 'trainings') & (files['linked_id'].astype(str) == training_id)).sum()) if not files.empty else 0
    resource_count = int(((resources['training_id'].astype(str) == training_id) & (resources['active'].astype(str) == 'Yes')).sum()) if not resources.empty else 0
    links = sum(bool(_clean(training.get(field))) for field in ('slides_link','video_link','reference_link','scorm_package_link'))
    return file_count + resource_count + links


def _ensure_assessment_config(training: dict) -> None:
    tid = _clean(training.get('training_id'))
    title = _clean(training.get('title'))
    passing = int(training.get('passing_marks') or 70)
    attempts = int(training.get('max_attempts') or 2)
    duration = 20 if int(training.get('minimum_mcqs') or 5) <= 10 else 30
    existing = query_sql('select assessment_config_id from training_assessment_configs where training_id=:tid order by created_on desc limit 1', {'tid': tid})
    params = {
        'title': f'{title} Assessment', 'duration': duration, 'passing': passing,
        'attempts': attempts, 'now': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), 'tid': tid,
    }
    if existing.empty:
        params['id'] = _uid('ACFG')
        exec_sql('''insert into training_assessment_configs
            (assessment_config_id,training_id,title,duration_minutes,passing_score,max_attempts,
             randomize_questions,randomize_answers,show_result_immediately,show_correct_answers,
             active,created_by,created_on,updated_on)
            values (:id,:tid,:title,:duration,:passing,:attempts,'Yes','Yes','Yes','No','Yes',
                    'System Curriculum Publisher',:now,:now)''', params)
    else:
        params['id'] = _clean(existing.iloc[-1]['assessment_config_id'])
        exec_sql('''update training_assessment_configs set title=:title,duration_minutes=:duration,
            passing_score=:passing,max_attempts=:attempts,randomize_questions='Yes',randomize_answers='Yes',
            show_result_immediately='Yes',show_correct_answers='No',active='Yes',updated_on=:now
            where assessment_config_id=:id''', params)


def prepare_and_publish_source_backed_curriculum() -> dict:
    global _RAN
    if _RAN:
        return {'processed':0,'published':0,'questions_added':0,'remaining_draft':0}
    _RAN = True

    drafts = query_sql("select * from trainings where content_status='Draft' order by training_id")
    if drafts.empty:
        return {'processed':0,'published':0,'questions_added':0,'remaining_draft':0}
    files = query_sql("select * from files where linked_table='trainings'")
    try:
        resources = query_sql("select * from training_resources")
    except Exception:
        resources = pd.DataFrame(columns=['training_id','active'])
    questions_added = 0
    published = 0
    now_value = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

    for _, tr_row in drafts.iterrows():
        tr = tr_row.to_dict()
        tid = _clean(tr.get('training_id'))
        if tid == 'TRN-55932C55':
            exec_sql("update trainings set status='Archived',content_status='Archived',enrollment_open='No',updated_on=:now where training_id=:tid", {'now':now_value,'tid':tid})
            continue

        # A newly scaffolded controlled course has no publishable content until
        # the Trainer uploads a document/resource or records an approved link.
        # Skip it before per-course database queries; otherwise a curriculum
        # import with many Draft placeholders makes the first login needlessly
        # wait on two or more network round trips per course.
        learning_items = _learning_item_count(tr, tid, files, resources)
        source = _course_source(tid, files)
        if learning_items == 0 and not source:
            continue

        current = query_sql('select question_id,question from question_bank where training_id=:tid', {'tid':tid})
        minimum = int(tr.get('minimum_mcqs') or 5)
        target = max(minimum, 10)
        if len(current) < minimum and len(source) >= 500:
            existing = set(current['question'].astype(str).str.strip().tolist()) if not current.empty else set()
            for q in _generate_grounded_mcqs(tid, source, target):
                if q['question'] in existing:
                    continue
                exec_sql('''insert into question_bank
                    (question_id,training_id,question,option_a,option_b,option_c,option_d,correct_answer,marks,generated_on)
                    values (:qid,:tid,:question,:a,:b,:c,:d,:answer,:marks,:now)''', {
                    'qid':_uid('Q'),'tid':tid,'question':q['question'],'a':q['option_a'],'b':q['option_b'],
                    'c':q['option_c'],'d':q['option_d'],'answer':q['correct_answer'],'marks':q['marks'],'now':now_value,
                })
                existing.add(q['question'])
                questions_added += 1

        q_count = int(query_sql('select count(*) n from question_bank where training_id=:tid', {'tid':tid}).iloc[0]['n'])
        assessment_required = _clean(tr.get('assessment_required') or 'Yes') == 'Yes'
        ready = learning_items > 0 and ((not assessment_required) or q_count >= minimum)
        if not ready:
            continue
        passing = int(tr.get('passing_marks') or 70)
        attempts = int(tr.get('max_attempts') or 2)
        exec_sql('''update trainings set content_status='Published',
            status=case when coalesce(status,'')='' then 'Active' else status end,
            trainer_name=case when coalesce(trainer_name,'')='' then 'Yahya Hafiz' else trainer_name end,
            passing_marks=:passing,max_attempts=:attempts,certificate_required='Yes',attestation_required='Yes',updated_on=:now
            where training_id=:tid''', {'passing':passing,'attempts':attempts,'now':now_value,'tid':tid})
        _ensure_assessment_config({**tr,'passing_marks':passing,'max_attempts':attempts})
        published += 1

    remaining = int(query_sql("select count(*) n from trainings where content_status='Draft'").iloc[0]['n'])
    return {'processed':len(drafts),'published':published,'questions_added':questions_added,'remaining_draft':remaining}
