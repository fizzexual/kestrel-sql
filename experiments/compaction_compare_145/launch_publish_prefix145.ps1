$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
if(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-publication-proof.json')){throw 'Publication already committed; inspect rather than repeat'}
$taskOther=& (Join-Path $taskRoot 'inspect_current_kestrel_jobs.ps1') | ConvertFrom-Json -DateKind String
if(@($taskOther.relevant_processes | Where-Object {$_.timed -or $_.deployment -or $_.reset}).Count){throw 'Timed/reset work active; no publication'}
& (Join-Path $taskRoot 'guard_cleanup_20261010.ps1') -Phase prepreserve *> (Join-Path $taskRoot 'phase145-publication-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before publication'}
& (Join-Path $taskRoot 'check_global_build_activity.ps1') *> (Join-Path $taskRoot 'phase145-publication-global.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before publication'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'publish_prefix145.py') *> (Join-Path $taskRoot 'phase145-publication.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');publication_actual_exit=$taskExit;actual_publisher_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'phase145-publication-actual-exits.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-publication.log') -Tail 6
exit $taskExit
