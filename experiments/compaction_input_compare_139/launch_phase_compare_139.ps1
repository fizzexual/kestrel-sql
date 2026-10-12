$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\append_phase139_declared.py' *> 'D:\Codex\Kestrel\work\append-phase139-declared.log'
if($LASTEXITCODE -ne 0){throw 'Checkpoint failed before timing'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase pretime *> 'D:\Codex\Kestrel\work\phase139-pretime-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Task/reset pretime guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase139-pretime-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build before timing'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\run_phase_compare_139.py' *> 'D:\Codex\Kestrel\work\run-phase-compare-139.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');cohort_actual_exit=$taskExit;actual_controller_wait_completed=$true;controller='run_phase_compare_139.py'} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\run-phase-compare-139.log' -Tail 6
exit $taskExit
