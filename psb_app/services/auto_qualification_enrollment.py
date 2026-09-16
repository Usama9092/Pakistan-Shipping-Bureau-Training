from __future__ import annotations

from psb_app.common import db_all, db_insert, db_update, db_where, now, table_exists, today, uid

ROLE_PATHS = {
    'NSC Surveyor': ('QP-NSC', 'NSC Surveyor', 'Survey NSC'),
    'In-Service Surveyor': ('QP-IS', 'In-Service Surveyor', 'Survey Inservice'),
    'Plan Appraiser': ('QP-PA', 'Plan Appraiser', 'Plan Appraisal'),
}


def ensure_auto_qualification_enrollment() -> int:
    """Enroll direct technical roles when a valid Trainer is already assigned.

    This is intentionally conservative: it only creates a qualification assignment
    when the employee has one of the direct technical roles above, has an assigned
    active Trainer, and has no active qualification assignment. It never replaces
    an existing path and never guesses a Trainer for the employee.
    """
    required = {
        'users', 'qualification_assignments', 'qualification_assignment_state',
        'qualification_path_versions', 'qualification_path_levels', 'training_records',
    }
    if not all(table_exists(t) for t in required):
        return 0

    from psb_app.pages import qualification as q

    users = db_all('users')
    if users.empty:
        return 0

    created = 0
    for _, person in users.iterrows():
        role = str(person.get('role') or '').strip()
        if role not in ROLE_PATHS:
            continue
        status = str(person.get('status') or person.get('account_status') or 'Active').strip().casefold()
        if status not in {'active', 'enabled'}:
            continue

        user_id = str(person.get('user_id') or '').strip()
        if not user_id:
            continue
        active = db_where(
            'qualification_assignments',
            'user_id = :uid AND status = :status',
            (('uid', user_id), ('status', 'Active')),
        )
        if not active.empty:
            continue

        trainer_id = str(person.get('trainer_id') or '').strip()
        if not trainer_id:
            continue
        trainer = db_where('users', 'user_id = :uid', (('uid', trainer_id),))
        if trainer.empty:
            continue
        trow = trainer.iloc[-1]
        trainer_status = str(trow.get('status') or trow.get('account_status') or 'Active').strip().casefold()
        if trainer_status not in {'active', 'enabled'} or str(trow.get('role') or '').strip() != 'Trainer':
            continue

        path_id, path_name, department = ROLE_PATHS[role]
        version = db_where(
            'qualification_path_versions',
            'path_id = :pid AND status = :status',
            (('pid', path_id), ('status', 'Active')),
        )
        if version.empty:
            continue
        version = version.sort_values('effective_from').iloc[-1]
        version_id = str(version.get('path_version_id') or '')
        levels = db_where('qualification_path_levels', 'path_version_id = :vid', (('vid', version_id),))
        if levels.empty:
            continue
        first = levels.sort_values('sequence_no').iloc[0]
        first_level_id = str(first.get('level_id') or '')

        assignment_id = uid('QASG')
        db_insert('qualification_assignments', {
            'qualification_assignment_id': assignment_id,
            'user_id': user_id,
            'path_id': path_id,
            'trainer_id': trainer_id,
            'tutor_id': str(person.get('tutor_id') or person.get('mentor_id') or ''),
            'status': 'Active',
            'assigned_by': 'system-role-enrollment',
            'assigned_on': now(),
            'updated_on': now(),
        })
        db_insert('qualification_assignment_state', {
            'state_id': uid('QSTATE'),
            'qualification_assignment_id': assignment_id,
            'path_version_id': version_id,
            'starting_level_id': first_level_id,
            'current_level_id': first_level_id,
            'target_department': department,
            'person_stage': 'Qualification',
            'skip_reason': '',
            'skip_evidence_ref': '',
            'status': 'Active',
            'updated_by': 'system-role-enrollment',
            'updated_on': now(),
        })
        db_update('users', 'user_id', user_id, {
            'trainee_path': path_name,
            'primary_department': department,
            'trainer_name': str(trow.get('name') or person.get('trainer_name') or ''),
        })

        if table_exists('user_assignments'):
            existing_trainer = db_where(
                'user_assignments',
                'user_id = :uid AND assignment_type = :atype AND status = :status',
                (('uid', user_id), ('atype', 'Trainer'), ('status', 'Active')),
            )
            if existing_trainer.empty:
                db_insert('user_assignments', {
                    'assignment_id': uid('UASN'), 'user_id': user_id,
                    'assignment_type': 'Trainer', 'assigned_user_id': trainer_id,
                    'assigned_user_name': str(trow.get('name') or ''),
                    'effective_from': today(), 'effective_to': '', 'status': 'Active',
                    'created_by': 'system-role-enrollment', 'created_on': now(),
                })

        q._ensure_path_training_records(
            user_id,
            str(person.get('name') or user_id),
            role,
            path_name,
            path_id,
        )
        created += 1

    return created
