from pathlib import Path
import json
from core.navigation import ROLE_NAVIGATION
from core.view_context import context_for
ROOT=Path(__file__).resolve().parents[1]

def labels(role): return {x for _,items,_ in ROLE_NAVIGATION[role] for x in items}

def test_person_roles_use_merged_qualification_workspace():
    for role in ['Surveyor','Industrial Surveyor','Plan Appraiser','Trainee','On Probation']:
        assert 'My Qualification' in labels(role)
        assert 'Revalidation' not in labels(role)
        assert 'My Jobs' not in labels(role)

def test_trainer_combines_training_and_development():
    assert labels('Trainer') == {'Qualification Workspace'}

def test_department_manager_is_department_scoped():
    assert context_for('Department Manager','Department Qualification')=='Department'

def test_my_views_are_explicit_contexts():
    assert context_for('Surveyor','My Qualification')=='Own'
    assert context_for('Trainer','Qualification Workspace')=='Assigned'
    assert 'CRB Member' not in ROLE_NAVIGATION
