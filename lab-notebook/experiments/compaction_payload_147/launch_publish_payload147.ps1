$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
if((Test-Path -LiteralPath (Join-Path $taskRoot 'payload147-publication-proof.json')) -or (Test-Path -LiteralPath (Join-Path $taskRoot 'payload147-publication-actual-exits.json'))){throw 'Publisher already attempted; inspect partial state'}
& (Join-Path $taskRoot 'guard_cleanup_20261010.ps1') -Phase prepreserve *> (Join-Path $taskRoot 'payload147-publication-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/timed work held before147 publisher'}
& (Join-Path $taskRoot 'check_global_build_activity.ps1') *> (Join-Path $taskRoot 'payload147-publication-global.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held before147 publisher'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'publish_payload147.py') *> (Join-Path $taskRoot 'payload147-publication.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publisher_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'payload147-publication-actual-exits.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot 'payload147-publication.log') -Tail 7
exit $taskExit
