from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_gap3_service_modules_exist_and_runtime_reduced():
    legacy=ROOT/"psb_app"/"legacy_runtime.py"
    assert legacy.exists()
    assert len(legacy.read_text(encoding="utf-8").splitlines()) < 800
    for name in ["auth_service.py","policy_service.py","training_service.py","certificate_service.py","governance_service.py","admin_service.py","ui_helpers.py"]:
        assert (ROOT/"psb_app"/"services"/name).exists()

