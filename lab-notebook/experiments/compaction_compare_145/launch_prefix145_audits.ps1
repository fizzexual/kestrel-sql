$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
$taskActual=Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json') -Raw | ConvertFrom-Json
if($taskActual.cohort_actual_exit -ne 1 -or -not $taskActual.actual_controller_wait_completed){throw 'Actual rejected controller wait required'}
$taskQuiet=Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-prefix-audit-quiet-proof.json') -Raw | ConvertFrom-Json -DateKind String
if(-not $taskQuiet.complete -or $taskQuiet.continuous_observed_clear_seconds -lt 120 -or ((Get-Date).ToUniversalTime()-[datetime]$taskQuiet.utc).TotalSeconds -gt 60){throw 'Fresh120 continuous observed quiet required'}
if(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-prefix-audit-actual-exits.json')){throw 'Prefix auditor already attempted; inspect actual exit'}
& (Join-Path $taskRoot 'guard_cleanup_20261010.ps1') -Phase preaudit *> (Join-Path $taskRoot 'phase145-prefix-audit-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before prefix audit'}
& (Join-Path $taskRoot 'check_global_build_activity.ps1') *> (Join-Path $taskRoot 'phase145-prefix-audit-global.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global activity held before prefix audit'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'audit_prefix145.py') *> (Join-Path $taskRoot 'phase145-prefix-audit.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');prefix_audit_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'phase145-prefix-audit-actual-exits.json') -Encoding utf8
if($taskExit -ne 0){Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-prefix-audit.log') -Tail 10;exit $taskExit}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'audit_prefix145_lifecycle.py') *> (Join-Path $taskRoot 'phase145-prefix-lifecycle.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');lifecycle_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'phase145-prefix-lifecycle-actual-exits.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-prefix-audit.log'),(Join-Path $taskRoot 'phase145-prefix-lifecycle.log') -Tail 4
exit $taskExit
