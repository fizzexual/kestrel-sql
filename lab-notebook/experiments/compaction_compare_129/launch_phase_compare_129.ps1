$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\append_phase129_declared.py' *> 'D:\Codex\Kestrel\work\append-phase129-declared.log'
if($LASTEXITCODE -ne 0){throw 'Checked checkpoint append failed before timers'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\run_phase_compare_129.py' *> 'D:\Codex\Kestrel\work\run-phase-compare-128.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');cohort_actual_exit=$taskExit;actual_controller_wait_completed=$true;controller='run_phase_compare_129.py'} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase129-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\run-phase-compare-128.log' -Tail 6
exit $taskExit
