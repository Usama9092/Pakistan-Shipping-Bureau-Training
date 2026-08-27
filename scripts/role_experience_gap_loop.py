#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.navigation import ROLE_NAVIGATION
roles=ROLE_NAVIGATION
labels=lambda r:{l for _,ls,_ in roles.get(r,[]) for l in ls}
q=(ROOT/'psb_app/pages/qualification.py').read_text(encoding='utf-8')
t=(ROOT/'psb_app/pages/training.py').read_text(encoding='utf-8')
p=(ROOT/'psb_app/pages/practical_witness.py').read_text(encoding='utf-8')
checks={
 '01_current_role_model': set(roles)=={'GM','Management','Admin','Department Manager','Trainer','Trainee','On Probation','Surveyor','NSC Surveyor','In-Service Surveyor','Industrial Surveyor','Plan Appraiser','QMS Auditor','QMR','Rule Development Rep'},
 '02_no_tutor_role':'Tutor' not in roles and 'Tutor / Mentor' not in roles,
 '03_no_removed_roles':all(x not in roles for x in ['Lead Auditor','CRB Member','Job Coordinator','Principal Surveyor','Chief Plan Appraiser','Technical Manager']),
 '04_trainer_path_builder':'Qualification Workspace' in labels('Trainer') and 'trainer_paths_training_page' in (ROOT/'psb_app/main.py').read_text() and 'Knowledge Library' in q,
 '05_module_theory':'Theoretical Training inside Modules' in q and 'training_resources' in q and 'training_live_sessions' in q,
 '06_timed_mcq':'server-side timer' in t.lower() and '_stable_question_rows' in t and '_assessment_window_open' in t,
 '07_resource_completion':'training_resource_progress' in t and 'training_session_attendance' in q,
 '08_guided_practical':'guided_practical_training' in q and 'module_trainer_readiness' in q,
 '09_independent_assessment':'independent_practical_assessor_panel' in q and 'independent_practical_assessments' in q,
 '10_module_progress':'qualification_module_progress' in q and '_module_prereqs_complete' in q and '_level_complete' in q,
 '11_probation_approval':'Pending Approval' in q and 'Record Progression Decision' in q,
 '12_department_manager':'Department Qualification' in labels('Department Manager') and 'Authorization Cases' in labels('Department Manager'),
 '13_crb_case_based':'CRB Cases' in labels('Management') and 'crb_case_board_assignments' in q and 'CRB Member' not in roles,
 '14_management_authorization':'Authorization Decisions' in labels('Management') and 'Submit Final Authorization Decision' in q,
 '15_qms_unified':'QMS Auditor' in roles and 'Lead Auditor' not in roles,
 '16_rbac_central':'can_action' in q and not any(x in q for x in ["role not in {'Trainer','Admin'}","role not in {'Department Manager','Admin'}"]),
 '17_security_harness':all((ROOT/x).exists() for x in ['tests/browser_smoke.py','locustfile.py','tests/live_environment_smoke.py'])
}
report={'checks':checks,'passed':sum(checks.values()),'total':len(checks),'status':'PASS' if all(checks.values()) else 'FAIL'}
(ROOT/'ROLE_EXPERIENCE_GAP_LOOP.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2)); raise SystemExit(0 if report['status']=='PASS' else 1)
