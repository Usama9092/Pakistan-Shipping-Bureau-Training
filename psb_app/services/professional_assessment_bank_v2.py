"""Fast, idempotent production expansion of professional assessment banks."""
from __future__ import annotations

import hashlib
import json

import pandas as pd

from core.database_gateway import exec_sql, query_sql
from psb_app.services.professional_assessment_bank import (
    ASSESSMENT_MINUTES,
    SUPPLEMENTS,
    TARGET_BANK,
    _ensure_supplement,
    _generated_rows,
    _now,
    _uid,
)

_RAN = False


def _active_courses() -> pd.DataFrame:
    return query_sql('''select * from trainings
        where (trainer_name='Yahya Hafiz' or trainer_id='USR-557C91FF')
          and coalesce(status,'') not in ('Archived','Inactive')
          and coalesce(assessment_required,'Yes')='Yes'
        order by schedule_date,schedule_time,training_id''')


def _bulk_insert_questions(rows: list[dict]) -> None:
    for start in range(0, len(rows), 400):
        chunk = rows[start:start + 400]
        payload = json.dumps(chunk, ensure_ascii=False)
        exec_sql('''insert into question_bank
            (question_id,training_id,question,option_a,option_b,option_c,option_d,correct_answer,marks,generated_on)
            select x->>'question_id',x->>'training_id',x->>'question',x->>'option_a',x->>'option_b',
                   x->>'option_c',x->>'option_d',x->>'correct_answer',coalesce((x->>'marks')::int,1),x->>'generated_on'
            from jsonb_array_elements(cast(:payload as jsonb)) x
            on conflict (question_id) do nothing''', {'payload': payload})


def _bulk_insert_drafts(rows: list[dict]) -> None:
    if not rows:
        return
    for start in range(0, len(rows), 400):
        chunk = rows[start:start + 400]
        payload = json.dumps(chunk, ensure_ascii=False)
        try:
            exec_sql('''insert into training_mcq_drafts
                (draft_id,training_id,question,option_a,option_b,option_c,option_d,correct_answer,marks,status,
                 source_fingerprint,generation_method,generated_by,generated_on,reviewed_by,reviewed_on,published_on,updated_on)
                select x->>'draft_id',x->>'training_id',x->>'question',x->>'option_a',x->>'option_b',
                       x->>'option_c',x->>'option_d',x->>'correct_answer',1,'Published',x->>'source_fingerprint',
                       'Source-grounded professional bank expansion','System Curriculum QA',x->>'generated_on',
                       'Yahya Hafiz',x->>'generated_on',x->>'generated_on',x->>'generated_on'
                from jsonb_array_elements(cast(:payload as jsonb)) x
                on conflict (draft_id) do nothing''', {'payload': payload})
        except Exception:
            return


def ensure_professional_assessment_banks_v2() -> dict:
    global _RAN
    if _RAN:
        return {'processed': 0, 'added': 0, 'remaining_under_50': 0}
    _RAN = True

    courses = _active_courses()
    if courses.empty:
        return {'processed': 0, 'added': 0, 'remaining_under_50': 0}

    # Keep assessment policy consistent across all current Yahya qualification courses.
    exec_sql('''update trainings set minimum_mcqs=:target,updated_on=:now
        where (trainer_name='Yahya Hafiz' or trainer_id='USR-557C91FF')
          and coalesce(status,'') not in ('Archived','Inactive') and coalesce(assessment_required,'Yes')='Yes' ''',
        {'target': TARGET_BANK, 'now': _now()})
    exec_sql('''update training_assessment_configs c set duration_minutes=:minutes,questions_per_attempt=:target,
            randomize_questions='Yes',randomize_answers='Yes',show_result_immediately='Yes',show_correct_answers='No',updated_on=:now
        from trainings t where t.training_id=c.training_id and c.active='Yes'
          and (t.trainer_name='Yahya Hafiz' or t.trainer_id='USR-557C91FF')
          and coalesce(t.status,'') not in ('Archived','Inactive') and coalesce(t.assessment_required,'Yes')='Yes' ''',
        {'minutes': ASSESSMENT_MINUTES, 'target': TARGET_BANK, 'now': _now()})

    counts = query_sql('''select t.training_id,count(q.question_id) qcount
        from trainings t left join question_bank q on q.training_id=t.training_id
        where (t.trainer_name='Yahya Hafiz' or t.trainer_id='USR-557C91FF')
          and coalesce(t.status,'') not in ('Archived','Inactive') and coalesce(t.assessment_required,'Yes')='Yes'
        group by t.training_id''')
    under = set(counts.loc[counts['qcount'] < TARGET_BANK, 'training_id'].astype(str).tolist())
    if not under:
        return {'processed': len(courses), 'added': 0, 'remaining_under_50': 0}

    # Add controlled source supplements only for affected legacy source gaps.
    for tid, spec in SUPPLEMENTS.items():
        if tid in under:
            _ensure_supplement(tid, spec)

    files = query_sql('''select f.linked_id training_id,f.file_name,f.extracted_text,f.sequence_no,f.created_on
        from files f join trainings t on t.training_id=f.linked_id
        where f.linked_table='trainings'
          and (t.trainer_name='Yahya Hafiz' or t.trainer_id='USR-557C91FF')
          and coalesce(t.status,'') not in ('Archived','Inactive')''')
    existing = query_sql('''select q.* from question_bank q join trainings t on t.training_id=q.training_id
        where (t.trainer_name='Yahya Hafiz' or t.trainer_id='USR-557C91FF')
          and coalesce(t.status,'') not in ('Archived','Inactive')''')

    excluded = ('answer','solved','exam','result','certificate','attendance','evaluation_form','attestation')
    source_by_tid: dict[str, str] = {}
    if not files.empty:
        for tid, group in files.groupby('training_id'):
            parts: list[str] = []
            for _, row in group.sort_values(['sequence_no','created_on'], na_position='last').iterrows():
                name = str(row.get('file_name') or '').casefold()
                if any(token in name for token in excluded):
                    continue
                text = str(row.get('extracted_text') or '').strip()
                if len(text) >= 100:
                    parts.append(text)
                    if sum(len(x) for x in parts) >= 120000:
                        break
            source_by_tid[str(tid)] = '\n\n'.join(parts)[:120000]

    existing_by_tid: dict[str, pd.DataFrame] = {}
    if not existing.empty:
        for tid, group in existing.groupby('training_id'):
            existing_by_tid[str(tid)] = group.copy()

    all_new: list[dict] = []
    all_drafts: list[dict] = []
    source_gaps = 0
    for tid in sorted(under):
        current = existing_by_tid.get(tid, pd.DataFrame())
        current_count = len(current)
        source = source_by_tid.get(tid, '')
        if len(source) < 500:
            source_gaps += 1
            continue
        existing_questions = set(current['question'].astype(str).tolist()) if not current.empty else set()
        generated = _generated_rows(tid, source, TARGET_BANK - current_count, existing_questions)
        if not generated:
            source_gaps += 1
            continue
        fingerprint = hashlib.sha256(source.encode('utf-8')).hexdigest()
        all_new.extend(generated)
        for row in generated:
            all_drafts.append({
                'draft_id': _uid('QDRAFT'), 'training_id': tid, 'question': row['question'],
                'option_a': row['option_a'], 'option_b': row['option_b'], 'option_c': row['option_c'],
                'option_d': row['option_d'], 'correct_answer': row['correct_answer'],
                'source_fingerprint': fingerprint, 'generated_on': row['generated_on'],
            })

    _bulk_insert_questions(all_new)
    _bulk_insert_drafts(all_drafts)

    remaining = query_sql('''select count(*) n from (
        select t.training_id,count(q.question_id) qcount
        from trainings t left join question_bank q on q.training_id=t.training_id
        where (t.trainer_name='Yahya Hafiz' or t.trainer_id='USR-557C91FF')
          and coalesce(t.status,'') not in ('Archived','Inactive') and coalesce(t.assessment_required,'Yes')='Yes'
        group by t.training_id having count(q.question_id)<:target) x''', {'target': TARGET_BANK})
    return {'processed': len(courses), 'added': len(all_new),
            'remaining_under_50': int(remaining.iloc[0]['n']) if not remaining.empty else 0,
            'source_gaps': source_gaps}
