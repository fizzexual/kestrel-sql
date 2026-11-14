$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\buffer136-wire-preaudit-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Preaudit guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build activity'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_buffer136_legacy_wire.py' *> 'D:\Codex\Kestrel\work\audit-buffer136-wire.log'
$taskExit=$LASTEXITCODE
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\buffer136-wire-actual-exits.json'){throw 'Do not overwrite wire exit'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');wire_actual_exit=$taskExit;actual_wire_wait_completed=$true;performance_cases_declared=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\buffer136-wire-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\audit-buffer136-wire.log' -Tail 8
exit $taskExit
