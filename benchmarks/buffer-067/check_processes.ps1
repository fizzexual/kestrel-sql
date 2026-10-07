param([string]$Phase='post-timing')
$ErrorActionPreference='Stop'
$trialRoot=(Resolve-Path 'work/perf-067').Path
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('baseline-publication.exe','candidate-publication.exe','baseline-byte.exe','candidate-byte.exe','kestrel.exe','kestrel-stress.exe','group-probe.exe','publication_fault_probe.exe','source-pipeline-typed.exe','source_fault_probe.exe','cargo.exe','rustc.exe','rustdoc.exe')) -and ($_.CommandLine -like '*letys*')} | Select-Object ProcessId,Name,CommandLine)
@{checked_utc=[DateTime]::UtcNow.ToString('o');phase=$Phase;task_directory=$trialRoot;active_processes=$active;task_owned_only=$true;unrelated_processes_modified=$false} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $trialRoot ($Phase+'-process-check.json'))
if ($active.Count -ne 0) {throw 'Task-owned process still active'}
Get-Content -LiteralPath (Join-Path $trialRoot ($Phase+'-process-check.json'))
