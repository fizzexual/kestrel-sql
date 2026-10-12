$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\phase148-publication-proof.json'){throw 'Never blindly repeat publication after a commit'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase148-publication-v2-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before publication'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase148-publication-v2-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before publication'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\publish_prefix148.py' *> 'D:\Codex\Kestrel\work\phase148-publication.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publisher_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-publication-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-publication.log' -Tail 8
exit $taskExit
