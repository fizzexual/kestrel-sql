$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\wait_write134_audit_quiet.ps1'
if(-not $? -or $LASTEXITCODE -ne 0){throw 'Continuous quiet not established'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\write134-final-preaudit-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Preaudit guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build activity'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_write134_stores.py' *> 'D:\Codex\Kestrel\work\audit-write134.log'
$taskExit=$LASTEXITCODE
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\write134-audit-actual-exits.json'){throw 'Do not overwrite audit exit'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');audit_actual_exit=$taskExit;actual_audit_wait_completed=$true;controller='audit_write134_stores.py';timed_cases_declared=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\write134-audit-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\audit-write134.log' -Tail 8
exit $taskExit
