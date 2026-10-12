$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\phase139-preflight-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before preflight'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase139-preflight-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before preflight'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\smoke_phase_compare_139.py' *> 'D:\Codex\Kestrel\work\phase139-preflight.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preflight_actual_exit=$taskExit;actual_preflight_wait_completed=$true;timed_cohort_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-preflight-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-preflight.log' -Tail 8
exit $taskExit
