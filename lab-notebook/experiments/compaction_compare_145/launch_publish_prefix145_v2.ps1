$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
if((Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-publication-proof.json')) -or (Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-publication-actual-exits.json'))){throw 'Publisher already attempted; inspect rather than repeat'}
& (Join-Path $taskRoot 'guard_cleanup_20261010.ps1') -Phase prepreserve *> (Join-Path $taskRoot 'phase145-publication-v2-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before publication'}
& (Join-Path $taskRoot 'check_global_build_activity.ps1') *> (Join-Path $taskRoot 'phase145-publication-v2-global.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before publication'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'publish_prefix145.py') *> (Join-Path $taskRoot 'phase145-publication.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publisher_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'phase145-publication-actual-exits.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-publication.log') -Tail 6
exit $taskExit
