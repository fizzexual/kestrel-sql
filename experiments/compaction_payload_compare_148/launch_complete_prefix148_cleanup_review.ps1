$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase148-cleanup-review-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Task/reset guard held before source review save'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase148-cleanup-review-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before source review save'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\complete_prefix148_cleanup_review.py' *> 'D:\Codex\Kestrel\work\phase148-cleanup-review.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');actual_exit=$taskExit;actual_review_save_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-cleanup-review-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-cleanup-review.log' -Tail 5
exit $taskExit
