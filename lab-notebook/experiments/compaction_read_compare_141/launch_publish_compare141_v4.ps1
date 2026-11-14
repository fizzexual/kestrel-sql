$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase141-publication-v4-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity held before publication completion'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase141-publication-v4-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held before publication completion'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\complete_publication141_v4.py' *> 'D:\Codex\Kestrel\work\phase141-publication-v4.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publisher_wait_completed=$true;completion_attempt=4} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-publication-v4-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-publication-v4.log' -Tail 12
exit $taskExit
