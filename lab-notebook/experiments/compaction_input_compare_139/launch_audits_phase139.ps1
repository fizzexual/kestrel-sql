$ErrorActionPreference='Stop'
$taskExitProof=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-actual-exits.json' -Raw | ConvertFrom-Json
if($taskExitProof.cohort_actual_exit -ne 0 -or -not $taskExitProof.actual_controller_wait_completed){throw 'Actual cohort completion not verified'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\phase139-audit-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before audit'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase139-audit-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before audit'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_phase_compare_139.py' *> 'D:\Codex\Kestrel\work\phase139-audit.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');audit_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-audit-actual-exits.json' -Encoding utf8
if($taskExit -ne 0){Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-audit.log' -Tail 12;exit $taskExit}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_lifecycle_receipts_139.py' *> 'D:\Codex\Kestrel\work\phase139-lifecycle-audit.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');lifecycle_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-lifecycle-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-audit.log','D:\Codex\Kestrel\work\phase139-lifecycle-audit.log' -Tail 8
exit $taskExit
