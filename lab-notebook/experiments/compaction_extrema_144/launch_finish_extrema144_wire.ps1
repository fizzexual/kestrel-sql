$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\extrema144-wire-finish-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before finishing wire prefix'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\finish_extrema144_wire.py' *> 'D:\Codex\Kestrel\work\finish-extrema144-wire.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');wire_actual_exit=$taskExit;actual_wire_wait_completed=$true;performance_cases_declared=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-wire-finish-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\finish-extrema144-wire.log' -Tail 10
exit $taskExit
