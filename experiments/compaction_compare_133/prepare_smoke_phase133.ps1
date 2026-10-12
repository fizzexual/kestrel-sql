$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\phase133-preparation-guard.log'
if(-not $?){throw 'Task/reset work busy'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase133-preparation-global.log'
if($LASTEXITCODE -eq 3){throw 'Visible global build busy'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\append_prefix132_closed.py'
if($LASTEXITCODE -ne 0){throw '132 final checkpoint failed'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\prepare_phase_compare_133.py'
if($LASTEXITCODE -ne 0){throw '133 declaration/preparation failed'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\smoke_phase_compare_133.py' *> 'D:\Codex\Kestrel\work\smoke-phase-compare-133.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preflight_actual_exit=$taskExit;actual_preflight_wait_completed=$true;timed_cases_unstarted=216} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase133-preflight-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\smoke-phase-compare-133.log' -Tail 7
exit $taskExit
