$ErrorActionPreference='Stop'
$phase=$args[0]
if ($phase -notin @('pre-timing','post-timing')) { throw 'Expected timing phase' }
$trialRoot=(Resolve-Path 'work/perf-066').Path
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('encoder-probe.exe','baseline-publication.exe','candidate-publication.exe','kestrel.exe','kestrel-stress.exe','cargo.exe','rustc.exe','rustdoc.exe')) -and ($_.CommandLine -like '*letys*')} | Select-Object ProcessId,Name,CommandLine)
@{checked_utc=[DateTime]::UtcNow.ToString('o');task_directory=$trialRoot;active_processes=$active;task_owned_only=$true;unrelated_processes_modified=$false} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $trialRoot ($phase+'-process-check.json'))
if ($active.Count -ne 0) {throw 'Task-owned heavy or database process still active'}
Get-Content -LiteralPath (Join-Path $trialRoot ($phase+'-process-check.json'))
