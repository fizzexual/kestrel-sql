$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase149-checkpoint-review-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Task/reset guard held before checkpoint source review save'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase149-checkpoint-review-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before checkpoint source review save'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\save_compare149_checkpoint_review.py' *> 'D:\Codex\Kestrel\work\phase149-checkpoint-review.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');actual_exit=$taskExit;actual_review_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase149-checkpoint-review-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase149-checkpoint-review.log' -Tail 4
exit $taskExit
