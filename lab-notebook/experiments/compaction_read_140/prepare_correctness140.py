from pathlib import Path
import ast,hashlib,json
R=Path('D:/Codex/Kestrel/work'); W=R/'perf-140'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'independent-wire-audit.json')['all36_compaction_stores_checked']
assert load(R/'coalesce140-audit-actual-exits.json')['audit_actual_exit']==0
names=['audit_reuse138_legacy_wire.py','check_reuse138_wire_activity.ps1','launch_wire_reuse138.ps1',
 'build_reuse138_recovery.ps1','run_reuse138_recovery.py','check_reuse138_recovery_activity.ps1',
 'launch_recovery_reuse138.ps1','launch_build_recovery138.ps1']
proof=[]
for old in names:
    new=old.replace('reuse138','coalesce140').replace('recovery138','recovery140')
    text=(R/old).read_text(encoding='utf-8').replace('perf-138','perf-140').replace('reuse138','coalesce140').replace('recovery138','recovery140').replace('candidate138','candidate140').replace('reuse-compaction-input-138','coalesced-compaction-read-140').replace('all20_compaction_stores_checked','all36_compaction_stores_checked')
    target=R/new;assert not target.exists()
    if new.endswith('.py'):ast.parse(text,filename=new)
    target.write_text(text,encoding='utf-8',newline='\n')
    proof.append({'source':old,'actual':new,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(W/'wire-recovery-source-derivation.json').write_text(json.dumps({'actual_sources':proof,'engine_bytes_unchanged':True,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
print('140 wire/recovery controllers prepared from actual138 sources; no engine bytes or passed tests changed')
