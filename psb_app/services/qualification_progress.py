from __future__ import annotations


def install_qualification_progress_patch() -> None:
    """Install curriculum-aware module progress rules.

    The original qualification workspace treated every module as if it required
    guided practical, a Trainer gate, an independent practical and competency.
    That is correct for practical/OJT modules, but it prevents pure theoretical
    modules (for example the Common Foundation curriculum) from ever completing.

    This patch keeps the existing practical controls unchanged in principle while
    allowing theory-only modules to complete on their controlled theory gate.
    """
    from psb_app.pages import qualification as q

    def _int_gate(gate: dict, key: str, default: int) -> int:
        raw = gate.get(key)
        if raw is None or str(raw).strip() == "":
            return default
        try:
            return int(raw)
        except Exception:
            return default

    def _save_snapshot(user_id: str, module_id: str, assignment_id: str, snapshot: dict) -> None:
        if not q.table_exists('qualification_module_progress'):
            return
        existing = q.db_where(
            'qualification_module_progress',
            'user_id = :uid AND module_id = :mid',
            (('uid', user_id), ('mid', module_id)),
        )
        if existing.empty:
            q.db_insert(
                'qualification_module_progress',
                {
                    'module_progress_id': q.uid('QMP'),
                    'qualification_assignment_id': assignment_id,
                    'module_id': module_id,
                    'user_id': user_id,
                    **snapshot,
                },
            )
        else:
            q.db_update(
                'qualification_module_progress',
                'module_progress_id',
                str(existing.iloc[-1].get('module_progress_id')),
                snapshot,
            )

    def _sync_module_progress(user_id: str, module_id: str, assignment_id: str = '') -> dict:
        module_df = q.db_where('qualification_modules', 'module_id = :mid', (('mid', module_id),))
        module = module_df.iloc[-1].to_dict() if not module_df.empty else {}
        module_type = str(module.get('module_type') or '').strip()
        practical_flag = str(module.get('practical_training_required') or '').strip().casefold()
        practical_required = module_type == 'Practical Training' or practical_flag in {'yes', 'true', '1'}

        theory_ok, theory_done, theory_total = q._theory_status(user_id, module_id)

        # Pure theoretical modules finish when all mandatory controlled theory
        # (materials/resources/attendance/MCQ as configured) has been completed.
        if not practical_required:
            complete = bool(theory_ok)
            snapshot = {
                'theory_status': 'Complete' if theory_ok else 'In Progress',
                'guided_practical_status': 'Not Required',
                'trainer_gate_status': 'Not Required',
                'independent_practical_status': 'Not Required',
                'competency_status': 'Not Required',
                'module_status': 'Complete' if complete else 'In Progress',
                'completion_percent': 100 if complete else 0,
                'completed_on': q.now() if complete else '',
                'updated_on': q.now(),
            }
            _save_snapshot(user_id, module_id, assignment_id, snapshot)
            return snapshot

        gate = q._module_gate(module_id)
        guided_done, trainer_satisfied = q._guided_status(user_id, module_id)
        minimum_guided = _int_gate(gate, 'minimum_guided_practical', 2)
        required_independent = _int_gate(gate, 'independent_practical_required', 1)
        independent_passed, _ = q._independent_status(user_id, module_id)
        competency_complete = q._competency_complete(user_id, module_id)
        req_guided_ok, req_independent_ok, _, _ = q._specific_practical_requirements_status(user_id, module_id)

        guided_ok = guided_done >= minimum_guided and req_guided_ok
        trainer_required = str(gate.get('trainer_satisfaction_required', 'Yes')).strip() != 'No'
        trainer_ok = bool(trainer_satisfied) if trainer_required else True
        independent_ok = independent_passed >= required_independent and req_independent_ok
        complete = bool(theory_ok and guided_ok and trainer_ok and independent_ok and competency_complete)

        checks = [bool(theory_ok), bool(guided_ok), bool(trainer_ok), bool(independent_ok), bool(competency_complete)]
        pct = int(round(100 * sum(checks) / len(checks)))
        snapshot = {
            'theory_status': 'Complete' if theory_ok else 'In Progress',
            'guided_practical_status': 'Complete' if guided_ok else ('Available' if theory_ok else 'Locked'),
            'trainer_gate_status': 'Ready' if trainer_ok else 'Pending',
            'independent_practical_status': 'Complete' if independent_ok else ('Available' if theory_ok and guided_ok and trainer_ok else 'Locked'),
            'competency_status': 'Complete' if competency_complete else 'Pending',
            'module_status': 'Complete' if complete else 'In Progress',
            'completion_percent': pct,
            'completed_on': q.now() if complete else '',
            'updated_on': q.now(),
        }
        _save_snapshot(user_id, module_id, assignment_id, snapshot)
        return snapshot

    q._sync_module_progress = _sync_module_progress
