$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\write134-recovery-v2-preaudit-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Recovery preaudit guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build activity'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\run_write134_recovery_v2.py' *> 'D:\Codex\Kestrel\work\recovery-write134-v2.log'
$taskExit=$LASTEXITCODE
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\write134-recovery-v2-actual-exits.json'){throw 'Do not overwrite recovery exit'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');recovery_actual_exit=$taskExit;actual_recovery_wait_completed=$true;timed_performance_cases=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\write134-recovery-v2-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\recovery-write134-v2.log' -Tail 9
exit $taskExit
