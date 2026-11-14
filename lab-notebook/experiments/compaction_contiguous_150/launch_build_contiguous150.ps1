$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\contiguous150-build-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/timed work held before150 build'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\build_contiguous_150.py' *> 'D:\Codex\Kestrel\work\build-contiguous-150.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');build_actual_exit=$taskExit;actual_build_controller_wait_completed=$true;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\contiguous150-build-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-contiguous-150.log' -Tail 12
exit $taskExit
