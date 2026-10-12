from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
def adapt(text):
    return text.replace('perf-136','perf-138').replace('buffer136','reuse138').replace('candidate136.exe','candidate138.exe').replace('recovery136','recovery138').replace('adaptive-segment-buffer-136','reuse-compaction-input-138')
for old,new in [('audit_buffer136_legacy_wire.py','audit_reuse138_legacy_wire.py'),('check_buffer136_wire_activity.ps1','check_reuse138_wire_activity.ps1'),
                ('launch_wire_buffer136.ps1','launch_wire_reuse138.ps1'),('build_buffer136_recovery.ps1','build_reuse138_recovery.ps1'),
                ('run_buffer136_recovery.py','run_reuse138_recovery.py'),('check_buffer136_recovery_activity.ps1','check_reuse138_recovery_activity.ps1'),
                ('launch_recovery_buffer136.ps1','launch_recovery_reuse138.ps1')]:
    target=R/new; assert not target.exists()
    text=adapt((R/old).read_text(encoding='utf-8'))
    if new=='audit_reuse138_legacy_wire.py':
        text=text.replace('all16_fresh_stores_checked','all20_compaction_stores_checked').replace('candidate134','candidate138')
        old_receipts="            receipts={id:(reference['rows'](shape,run,5),gen) for id,run,gen in result['receipts']}"
        new_receipts="            declared_receipts=[[f'merge121:{run}',run,run+1] for run in range(32)] if shape in ['clustered','late'] else []\n            assert result['receipts']==declared_receipts\n            receipts={id:(reference['rows'](shape,run,5),run+1) for id,run,generation in declared_receipts}"
        assert text.count(old_receipts)==1; text=text.replace(old_receipts,new_receipts,1)
    if new.endswith('.py'):ast.parse(text,filename=new)
    target.write_text(text,encoding='utf-8',newline='\n')
print('138 wire/recovery controllers prepared; no engine/test bytes changed')
