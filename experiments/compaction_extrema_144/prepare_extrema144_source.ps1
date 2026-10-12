$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\extrema144-source-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/timed job hold before source-only144 preparation'}
# Ordinary global builds may coexist with bounded source editing. This launches
# no Cargo job or timer. All actual timed supervisors were checked first.
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\declare_prepare_extrema_144.py' *> 'D:\Codex\Kestrel\work\extrema144-source-preparation.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preparation_actual_exit=$taskExit;actual_preparation_wait_completed=$true;builds_started=0;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-source-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-source-preparation.log' -Tail 12
exit $taskExit
