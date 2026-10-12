"""Prepare full rejected-prefix audits; never resume or retime148."""
from pathlib import Path
import ast,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-148';P=R.parent/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,s):
    assert not p.exists(),p
    if p.suffix=='.py':ast.parse(s)
    p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
assert load(R/'phase148-actual-exits.json')['cohort_actual_exit']==1
failed=load(W/'cohort-failure.json');assert failed['completed']==10 and failed['unstarted_indices']==list(range(10,216))
source=(P/'experiments/compaction_compare_145/audit_prefix145.py').read_text(encoding='utf-8')
source=source.replace('145','148').replace('118','10').replace('3866624','327680').replace('92798976','7864320')
source=source.replace('len(workers) == 2','len(workers) == 3')
source=source.replace("'release017_qualified':False", "'failed_preflight_quiet_worker_exit_not_separately_saved':True,'release017_qualified':False")
write(R/'audit_prefix148.py',source)
quiet=(P/'experiments/compaction_compare_145/wait_prefix145_audit_quiet.ps1').read_text(encoding='utf-8').replace('145','148')
write(R/'wait_prefix148_audit_quiet.ps1',quiet)
launch='''$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit-actual-exits.json'){throw 'Never repeat an existing prefix audit'}
& 'D:\\Codex\\Kestrel\\work\\wait_prefix148_audit_quiet.ps1' *> 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit-quiet.log'
if(-not $? -or $LASTEXITCODE -ne 0){throw 'Quiet guard held; no auditor started'}
& 'D:\\Codex\\Kestrel\\work\\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before audit'}
& 'D:\\Codex\\Kestrel\\work\\check_global_build_activity.ps1' *> 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before audit'}
& 'C:\\Users\\Frizer\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' 'D:\\Codex\\Kestrel\\work\\audit_prefix148.py' *> 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');prefix_audit_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit-actual-exits.json' -Encoding utf8
if($taskExit -ne 0){Get-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit.log' -Tail 12;exit $taskExit}
& 'C:\\Users\\Frizer\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' 'D:\\Codex\\Kestrel\\work\\audit_prefix148_lifecycle.py' *> 'D:\\Codex\\Kestrel\\work\\phase148-prefix-lifecycle.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');prefix_lifecycle_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\phase148-prefix-lifecycle-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\phase148-prefix-audit.log','D:\\Codex\\Kestrel\\work\\phase148-prefix-lifecycle.log' -Tail 4
exit $taskExit
'''
write(R/'launch_prefix148_audits.ps1',launch)
print('Full ten-case prefix audits prepared; all206 unstarted cases preserved')
