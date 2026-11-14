"""Prepare actual144 prerequisite controls without changing candidate engine bytes."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
for old,new in [('build_coalesce_140.py','build_extrema_144.py'),('check_coalesce140_prerequisite_activity.ps1','check_extrema144_prerequisite_activity.ps1'),('launch_build_coalesce140.ps1','launch_build_extrema144.ps1')]:
    target=R/new;assert not target.exists(),new
    text=(R/old).read_text().replace('build_coalesce_140','build_extrema_144').replace('coalesced-compaction-read-140','reuse-publish-extrema-144').replace('perf-140','perf-144').replace('coalesce140','extrema144').replace('candidate140.exe','candidate144.exe').replace('build-coalesce140','build-extrema144').replace('Untimed140','Untimed144')
    if new.endswith('.py'):
        text=text.replace("record['fresh_tests']==88", "record['fresh_tests']==86")
        ast.parse(text)
    target.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
print('144 serial normal/fault debug/release suites and strict lints prepared; no Cargo or timer started',flush=True)
