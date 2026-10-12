$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\payload147-source-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/timed work held147 source preparation'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\declare_prepare_payload_147.py' *> 'D:\Codex\Kestrel\work\payload147-source-preparation.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preparation_actual_exit=$taskExit;actual_preparation_wait_completed=$true;builds_started=0;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\payload147-source-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\payload147-source-preparation.log' -Tail 12
exit $taskExit
