$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
if((Test-Path -LiteralPath (Join-Path $taskRoot 'payload147-publication-proof.json')) -or (Test-Path -LiteralPath (Join-Path $taskRoot 'payload147-publication-v2-actual-exits.json'))){throw 'V2 publication already attempted; inspect'}
& (Join-Path $taskRoot 'guard_cleanup_20261010.ps1') -Phase prepreserve *> (Join-Path $taskRoot 'payload147-publication-v2-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/timed work held v2 publication'}
& (Join-Path $taskRoot 'check_global_build_activity.ps1') *> (Join-Path $taskRoot 'payload147-publication-v2-global.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held v2 publication'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'complete_payload147_publication_v2.py') *> (Join-Path $taskRoot 'payload147-publication-v2.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publisher_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'payload147-publication-v2-actual-exits.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot 'payload147-publication-v2.log') -Tail 7
exit $taskExit
