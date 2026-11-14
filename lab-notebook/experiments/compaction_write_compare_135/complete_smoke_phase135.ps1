$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\phase135-preparation-v2-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Task/reset preparation held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase135-preparation-v2-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build busy'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\complete_preparation_135.py'
if($LASTEXITCODE -ne 0){throw 'Preparation completion failed'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\smoke_phase_compare_135.py' *> 'D:\Codex\Kestrel\work\smoke-phase-compare-135.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preflight_actual_exit=$taskExit;actual_preflight_wait_completed=$true;timed_cases_unstarted=216} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase135-preflight-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\smoke-phase-compare-135.log' -Tail 8
exit $taskExit
