from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
pairs=[('audit_payload147_legacy_wire.py','audit_contiguous150_legacy_wire.py'),('check_payload147_wire_activity.ps1','check_contiguous150_wire_activity.ps1'),
    ('launch_wire_payload147.ps1','launch_wire_contiguous150.ps1'),('build_payload147_recovery.ps1','build_contiguous150_recovery.ps1'),
    ('run_payload147_recovery.py','run_contiguous150_recovery.py'),('check_payload147_recovery_activity.ps1','check_contiguous150_recovery_activity.ps1'),
    ('launch_recovery_payload147.ps1','launch_recovery_contiguous150.ps1')]
for old,new in pairs:
    s=(R/old).read_text(encoding='utf-8-sig').replace('reuse-compaction-payload-147','contiguous-compaction-payload-150').replace('147','150').replace('payload','contiguous')
    s=s.replace('contiguous-compaction-contiguous-150','contiguous-compaction-payload-150')
    if new.endswith('.py'):ast.parse(s)
    p=R/new;assert not p.exists();p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
print('150 fresh wire/recovery controls prepared; no passed test suite repeated')
