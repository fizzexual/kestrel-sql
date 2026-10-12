$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\build_coalesce140_recovery.ps1' *> 'D:\Codex\Kestrel\work\build-recovery140.log'
$taskOk=$?
$taskExit=if($taskOk){0}else{1}
@{utc=(Get-Date).ToUniversalTime().ToString('o');recovery_build_actual_exit=$taskExit;actual_recovery_build_wait_completed=$true;passed_test_suites_repeated=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\coalesce140-recovery-build-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-recovery140.log' -Tail 7
exit $taskExit
