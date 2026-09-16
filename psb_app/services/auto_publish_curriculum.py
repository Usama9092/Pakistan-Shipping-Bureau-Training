"""One-time source-backed preparation of controlled curriculum courses.

Only Draft courses with credible learning material are published. Missing MCQs are
created from the course's own extracted controlled material using the existing
training-service generator. Exam/answer/result/certificate files are excluded from
MCQ source text. The function is idempotent because it only acts on Draft courses
and only fills missing questions/configuration.
"""
from __future__ import annotations

from psb_app.common import (
    clean, db_all, db_insert, db_update, now, pd, table_exists, uid,
)
from psb_app.services.training_service import generate_mcqs

_RAN = False
_EXCLUDE_SOURCE_TOKENS = (
    'answer', 'solved', 'exam', 'result', 'certificate', 'attendance',
    'evaluation_form', 'attestation', 'issued_certificate',
)


def _course_source(training_id: str, files: pd.DataFrame) -> str:
    if files.empty:
        return ''
    rows = files[
        files.get('linked_table', pd.Series(dtype=str)).astype(str).eq('trainings')
        & files.get('linked_id', pd.Series(dtype=str)).astype(str).eq(training_id)
    ].copy()
    if rows.empty:
        return ''
    parts = []
    for _, row in rows.iterrows():
        name = clean(row.get('file_name')).casefold()
        if any(token in name for token in _EXCLUDE_SOURCE_TOKENS):
            continue
        text = clean(row.get('extracted_text')).strip()
        if len(text) >= 120:
            parts.append(text)
        if sum(len(x) for x in parts) >= 50000:
            break
    return '\n\n'.join(parts)[:50000]


def _learning_item_count(training: dict, training_id: str, files: pd.DataFrame, resources: pd.DataFrame) -> int:
    file_count = 0
    if not files.empty:
        file_count = int((
            files.get('linked_table', pd.Series(dtype=str)).astype(str).eq('trainings')
            & files.get('linked_id', pd.Series(dtype=str)).astype(str).eq(training_id)
        ).sum())
    resource_count = 0
    if not resources.empty:
        resource_count = int((
            resources.get('training_id', pd.Series(dtype=str)).astype(str).eq(training_id)
            & resources.get('active', pd.Series(dtype=str)).astype(str).eq('Yes')
        ).sum())
    links = sum(bool(clean(training.get(field))) for field in (
        'slides_link', 'video_link', 'reference_link', 'scorm_package_link'
    ))
    return file_count + resource_count + links


def _ensure_assessment_config(training: dict) -> None:
    if not table_exists('training_assessment_configs'):
        return
    tid = clean(training.get('training_id'))
    configs = db_all('training_assessment_configs')
    existing = configs[configs.get('training_id', pd.Series(dtype=str)).astype(str).eq(tid)] if not configs.empty else pd.DataFrame()
    passing = int(training.get('passing_marks') or 70)
    attempts = int(training.get('max_attempts') or 2)
    duration = 20 if int(training.get('minimum_mcqs') or 5) <= 10 else 30
    payload = {
        'title': f"{clean(training.get('title'))} Assessment",
        'duration_minutes': duration,
        'passing_score': passing,
        'max_attempts': attempts,
        'randomize_questions': 'Yes',
        'randomize_answers': 'Yes',
        'show_result_immediately': 'Yes',
        'show_correct_answers': 'No',
        'active': 'Yes',
        'updated_on': now(),
    }
    if existing.empty:
        db_insert('training_assessment_configs', {
            'assessment_config_id': uid('ACFG'), 'training_id': tid,
            'created_by': 'System Curriculum Publisher', 'created_on': now(), **payload,
        })
    else:
        db_update('training_assessment_configs', 'assessment_config_id', clean(existing.iloc[-1].get('assessment_config_id')), payload)


def prepare_and_publish_source_backed_curriculum() -> dict:
    global _RAN
    if _RAN:
        return {'processed': 0, 'published': 0, 'questions_added': 0, 'remaining_draft': 0}
    _RAN = True
    if not table_exists('trainings') or not table_exists('question_bank'):
        return {'processed': 0, 'published': 0, 'questions_added': 0, 'remaining_draft': 0}

    trainings = db_all('trainings')
    files = db_all('files') if table_exists('files') else pd.DataFrame()
    resources = db_all('training_resources') if table_exists('training_resources') else pd.DataFrame()
    qbank = db_all('question_bank')
    drafts = trainings[trainings.get('content_status', pd.Series(dtype=str)).astype(str).eq('Draft')].copy()
    published = 0
    questions_added = 0

    for _, tr_row in drafts.iterrows():
        tr = tr_row.to_dict()
        tid = clean(tr.get('training_id'))
        # Historical duplicate retained for audit but not released as another course.
        if tid == 'TRN-55932C55':
            db_update('trainings', 'training_id', tid, {'status': 'Archived', 'enrollment_open': 'No', 'updated_on': now()})
            continue
        source = _course_source(tid, files)
        current = qbank[qbank.get('training_id', pd.Series(dtype=str)).astype(str).eq(tid)] if not qbank.empty else pd.DataFrame()
        minimum = int(tr.get('minimum_mcqs') or 5)
        target = max(minimum, 10)
        if len(current) < minimum and len(source) >= 500:
            generated = generate_mcqs(tid, source, target)
            if not generated.empty:
                existing_questions = set(current.get('question', pd.Series(dtype=str)).astype(str).str.strip().tolist()) if not current.empty else set()
                for _, q in generated.iterrows():
                    question = clean(q.get('question')).strip()
                    if not question or question in existing_questions:
                        continue
                    db_insert('question_bank', {
                        'question_id': clean(q.get('question_id')) or uid('Q'),
                        'training_id': tid,
                        'question': question,
                        'option_a': clean(q.get('option_a')),
                        'option_b': clean(q.get('option_b')),
                        'option_c': clean(q.get('option_c')),
                        'option_d': clean(q.get('option_d')),
                        'correct_answer': clean(q.get('correct_answer')),
                        'marks': int(q.get('marks') or 1),
                        'generated_on': now(),
                    })
                    existing_questions.add(question)
                    questions_added += 1
        # Refresh count after insertions.
        latest_q = db_all('question_bank')
        q_count = len(latest_q[latest_q.get('training_id', pd.Series(dtype=str)).astype(str).eq(tid)]) if not latest_q.empty else 0
        learning_items = _learning_item_count(tr, tid, files, resources)
        assessment_required = clean(tr.get('assessment_required') or 'Yes') == 'Yes'
        ready = learning_items > 0 and ((not assessment_required) or q_count >= minimum)
        if ready:
            patch = {
                'content_status': 'Published',
                'status': clean(tr.get('status')) or 'Active',
                'trainer_name': clean(tr.get('trainer_name')) or 'Yahya Hafiz',
                'passing_marks': int(tr.get('passing_marks') or 70),
                'max_attempts': int(tr.get('max_attempts') or 2),
                'certificate_required': 'Yes',
                'attestation_required': 'Yes',
                'updated_on': now(),
            }
            db_update('trainings', 'training_id', tid, patch)
            _ensure_assessment_config({**tr, **patch})
            published += 1

    refreshed = db_all('trainings')
    remaining = int((refreshed.get('content_status', pd.Series(dtype=str)).astype(str) == 'Draft').sum()) if not refreshed.empty else 0
    return {'processed': len(drafts), 'published': published, 'questions_added': questions_added, 'remaining_draft': remaining}
