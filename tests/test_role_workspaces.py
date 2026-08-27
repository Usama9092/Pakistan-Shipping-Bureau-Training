from core.navigation import ROLE_NAVIGATION

def _labels(role): return {x for _,items,_ in ROLE_NAVIGATION[role] for x in items}
REQUIRED={
 'Trainer':{'Qualification Workspace'},
 'Department Manager':{'Department Qualification','My Assessments','Authorization Cases'},
 'Surveyor':{'My Qualification','My Assessments','My Certificates'},
 'Industrial Surveyor':{'My Qualification','My Assessments','My Certificates'},
 'Plan Appraiser':{'My Qualification','My Assessments','My Certificates'},
 'Trainee':{'My Qualification','My Development','My Certificates'},
 'On Probation':{'My Qualification','My Development','My Certificates'},
}
def test_required_role_workspaces_present():
    for role,required in REQUIRED.items():
        missing=sorted(required-_labels(role)); assert not missing,f'{role} missing {missing}'
