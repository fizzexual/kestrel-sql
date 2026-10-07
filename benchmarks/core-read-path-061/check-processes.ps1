$ErrorActionPreference='Stop'
$taskPath=(Resolve-Path 'work/perf-061').Path
$names=@('kestrel.exe','kestrel-stress.exe','group-probe.exe','performance-probe.exe','scan-profile.exe','publication-probe.exe','receipt-seed.exe','source-pipeline-typed.exe','publication_fault_probe.exe','live_retry_probe.exe','source_fault_probe.exe','cargo.exe','rustc.exe','rustdoc.exe')
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in $names) -and ($_.CommandLine -like '*perf-061*')} | Select-Object ProcessId,Name,CommandLine)
@{checked_utc=[DateTime]::UtcNow.ToString('o');task_directory=$taskPath;active_processes=$active;task_owned_only=$true;unrelated_processes_modified=$false} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $taskPath 'post-qualification-process-check.json')
if ($active.Count -ne 0) {throw 'Task-owned processes remain active; investigate before publication'}
Get-Content -LiteralPath (Join-Path $taskPath 'post-qualification-process-check.json')
