$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\finish_extrema144_recovery.py' *> 'D:\Codex\Kestrel\work\recovery-extrema144-finish.log'
$taskExit=$LASTEXITCODE
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\extrema144-recovery-finish-actual-exits.json'){throw 'Do not overwrite recovery finish exit'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');recovery_actual_exit=$taskExit;actual_recovery_wait_completed=$true;timed_performance_cases=0;no_native_case_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-recovery-finish-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\recovery-extrema144-finish.log' -Tail 9
exit $taskExit
