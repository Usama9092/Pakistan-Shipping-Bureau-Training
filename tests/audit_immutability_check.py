from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'database'/'migrations'/'007_audit_immutability.sql').read_text()
assert 'before update or delete on audit_trail' in s.lower()
print('audit immutability migration present')
