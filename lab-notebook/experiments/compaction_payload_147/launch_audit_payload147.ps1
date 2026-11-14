$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
$taskBuild=Get-Content -LiteralPath (Join-Path $taskRoot 'payload147-build-actual-exits.json') -Raw | ConvertFrom-Json
if($taskBuild.build_actual_exit -ne 0 -or -not $taskBuild.actual_build_controller_wait_completed){throw 'Actual completed build required'}
if(Test-Path -LiteralPath (Join-Path $taskRoot 'payload147-audit-actual-exits.json')){throw 'Auditor already attempted; inspect actual outcome'}
& (Join-Path $taskRoot 'guard_cleanup_20261010.ps1') -Phase preaudit *> (Join-Path $taskRoot 'payload147-audit-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/timed work held before independent147 audit'}
& (Join-Path $taskRoot 'check_global_build_activity.ps1') *> (Join-Path $taskRoot 'payload147-audit-global.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held before independent147 audit'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'audit_payload147_stores.py') *> (Join-Path $taskRoot 'payload147-audit.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');audit_actual_exit=$taskExit;actual_auditor_wait_completed=$true;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'payload147-audit-actual-exits.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot 'payload147-audit.log') -Tail 10
exit $taskExit
