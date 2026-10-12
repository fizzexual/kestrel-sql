$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase141-publication-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity held before publication'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase141-publication-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held before publication'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\publish_compare141.py' *> 'D:\Codex\Kestrel\work\phase141-publication.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publisher_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-publication-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-publication.log' -Tail 12
exit $taskExit
