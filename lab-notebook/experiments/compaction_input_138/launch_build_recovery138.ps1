$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\build_reuse138_recovery.ps1' *> 'D:\Codex\Kestrel\work\build-recovery138.log'
$taskOk=$?
$taskExit=if($taskOk){0}else{1}
@{utc=(Get-Date).ToUniversalTime().ToString('o');recovery_build_actual_exit=$taskExit;actual_recovery_build_wait_completed=$true;passed_test_suites_repeated=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\reuse138-recovery-build-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-recovery138.log' -Tail 7
exit $taskExit
