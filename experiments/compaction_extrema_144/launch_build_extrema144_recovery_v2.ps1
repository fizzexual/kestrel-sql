$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\build_extrema144_recovery_v2.ps1' *> 'D:\Codex\Kestrel\work\build-recovery144-v2.log'
$taskSucceeded=$?
$taskExit=if($taskSucceeded){0}else{1}
@{utc=(Get-Date).ToUniversalTime().ToString('o');recovery_build_actual_exit=$taskExit;actual_recovery_build_wait_completed=$true;fresh_tests_repeated=0;timed_qualification_cases=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-recovery-build-v2-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-recovery144-v2.log' -Tail 10
exit $taskExit
