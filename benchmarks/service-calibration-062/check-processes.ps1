$ErrorActionPreference='Stop'
$trialRoot=(Resolve-Path 'work/perf-062').Path
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('released-016.exe','clean-core-061.exe','kestrel.exe','kestrel-stress.exe','group-probe.exe','cargo.exe','rustc.exe')) -and ($_.CommandLine -like '*perf-062*')} | Select-Object ProcessId,Name,CommandLine)
@{checked_utc=[DateTime]::UtcNow.ToString('o');task_directory=$trialRoot;active_processes=$active;task_owned_only=$true;unrelated_processes_modified=$false} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $trialRoot 'post-qualification-process-check.json')
if ($active.Count -ne 0) {throw 'Task-owned process still active'}
Get-Content -LiteralPath (Join-Path $trialRoot 'post-qualification-process-check.json')
