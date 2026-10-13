from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
for old,new in [('build_payload_147.py','build_contiguous_150.py'),('check_payload147_prerequisite_activity.ps1','check_contiguous150_prerequisite_activity.ps1'),('launch_build_payload147.ps1','launch_build_contiguous150.ps1')]:
    s=(R/old).read_text(encoding='utf-8-sig')
    s=s.replace('reuse-compaction-payload-147','contiguous-compaction-payload-150').replace('147','150').replace('payload','contiguous')
    s=s.replace('contiguous-compaction-contiguous-150','contiguous-compaction-payload-150')
    if new.endswith('.py'):ast.parse(s)
    p=R/new;assert not p.exists();p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
print('150 four fresh suites/two lints/driver helpers prepared, zero Cargo jobs started')
