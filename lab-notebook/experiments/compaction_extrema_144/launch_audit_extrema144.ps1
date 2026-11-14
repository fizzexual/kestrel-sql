$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\extrema144-preaudit-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard hold before144 independent stores'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\extrema144-preaudit-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build hold before144 independent stores'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_extrema144_stores.py' *> 'D:\Codex\Kestrel\work\audit-extrema144.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');audit_actual_exit=$taskExit;actual_auditor_wait_completed=$true;timed_cases_declared=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-audit-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\audit-extrema144.log' -Tail 10
exit $taskExit
