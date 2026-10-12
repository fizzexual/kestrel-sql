$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\reuse138-publication-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before publication'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\reuse138-publication-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before publication'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\publish_reuse138.py' *> 'D:\Codex\Kestrel\work\publish-reuse138.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publication_wait_completed=$true;timed_performance_cases=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\reuse138-publication-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\publish-reuse138.log' -Tail 8
exit $taskExit
