$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\phase132-preparation-guard.log'
if(-not $?){throw 'Task/reset work busy'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase132-preparation-global.log'
if($LASTEXITCODE -eq 3){throw 'Visible global build busy'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\append_phase131_closed.py'
if($LASTEXITCODE -ne 0){throw '131 final checkpoint failed'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\prepare_phase_compare_132.py'
if($LASTEXITCODE -ne 0){throw 'New132 declaration/preparation failed'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\smoke_phase_compare_132.py' *> 'D:\Codex\Kestrel\work\smoke-phase-compare-132.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preflight_actual_exit=$taskExit;actual_preflight_wait_completed=$true;timed_cases_unstarted=216} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase132-preflight-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\smoke-phase-compare-132.log' -Tail 7
exit $taskExit
