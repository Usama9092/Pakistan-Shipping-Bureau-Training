from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_staging_gate_contract_exists():
    assert (ROOT/'scripts/staging_release_gate.py').exists()
    text=(ROOT/'scripts/staging_release_gate.py').read_text()
    assert '--live' in text and 'STAGING_APP_URL' in text and 'SUPABASE_URL' in text

def test_staging_sql_matrix_exists():
    p=ROOT/'database/rls_behavioral_tests.sql'
    assert p.exists()
    text=p.read_text().lower()
    for term in ['surveyor','trainer','department manager','crb','management']:
        assert term in text
