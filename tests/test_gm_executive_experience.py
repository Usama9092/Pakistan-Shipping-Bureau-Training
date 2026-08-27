from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_gm_role_has_clean_current_phase_navigation():
    from core.navigation import ROLE_NAVIGATION
    labels=[label for _,items,_ in ROLE_NAVIGATION['GM'] for label in items]
    assert labels == ['GM Capability','CRB Cases','Authorization Decisions','Certificates','GM Notifications']
    for removed in ['GM Operations','GM Quality','GM Reports & Analytics']:
        assert removed not in labels

def test_gm_practical_bridge_migration_still_exists():
    assert (ROOT/'database/migrations/036_unified_gm_practical_bridge.sql').exists()
