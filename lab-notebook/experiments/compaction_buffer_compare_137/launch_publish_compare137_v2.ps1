$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase137-publication-v2-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before publication completion'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase137-publication-v2-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before publication completion'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\complete_publication137_v2.py' *> 'D:\Codex\Kestrel\work\publish-compare137-v2.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publication_wait_completed=$true;completion_attempt=2} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase137-publication-v2-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\publish-compare137-v2.log' -Tail 8
exit $taskExit
