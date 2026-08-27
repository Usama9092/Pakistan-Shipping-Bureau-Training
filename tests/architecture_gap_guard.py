from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
app=(ROOT/'psb_app').glob('**/*.py')
text='\n'.join(p.read_text(errors='ignore') for p in app)
assert not re.search(r"if\s+role\s+(?:in|not in|==)\s*[{\[]", text), 'page-level role gates remain'
assert 'survey_report_review_page' not in text
assert 'plan_review_quality_page' not in text
assert not __import__('re').search(r"'temp_password'\s*:", text)
print({'architecture_gap_guard':'passed'})
