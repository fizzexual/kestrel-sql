$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\phase148-prefix-audit-actual-exits.json'){throw 'Never repeat an existing prefix audit'}
& 'D:\Codex\Kestrel\work\wait_prefix148_audit_quiet.ps1' *> 'D:\Codex\Kestrel\work\phase148-prefix-audit-quiet.log'
if(-not $? -or $LASTEXITCODE -ne 0){throw 'Quiet guard held; no auditor started'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\phase148-prefix-audit-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before audit'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase148-prefix-audit-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before audit'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_prefix148.py' *> 'D:\Codex\Kestrel\work\phase148-prefix-audit.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');prefix_audit_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-prefix-audit-actual-exits.json' -Encoding utf8
if($taskExit -ne 0){Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-prefix-audit.log' -Tail 12;exit $taskExit}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_prefix148_lifecycle.py' *> 'D:\Codex\Kestrel\work\phase148-prefix-lifecycle.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');prefix_lifecycle_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-prefix-lifecycle-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-prefix-audit.log','D:\Codex\Kestrel\work\phase148-prefix-lifecycle.log' -Tail 4
exit $taskExit
