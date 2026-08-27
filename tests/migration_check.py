from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
ms=ROOT/'database'/'migrations'
files=sorted(ms.glob('*.sql'))
versions=[]
for f in files:
    m=re.match(r'(\d+)_',f.name)
    if m: versions.append(int(m.group(1)))
assert versions == list(range(1,max(versions)+1)), versions
print({'migration_check':'passed','versions':versions})
