param([string]$Phase)
$ErrorActionPreference='Stop'
if($Phase -notin @('pre-smoke','pre-timing','post-timing')){throw 'Unknown phase'}
$taskActive=@(Get-CimInstance Win32_Process | Where-Object { ($_.ExecutablePath -like 'D:\Codex\Kestrel\work\*' -or $_.ExecutablePath -like 'D:\Codex\Kestrel\outputs\kestrel-sql\*' -or $_.ExecutablePath -like '*\letys\work\*') -or ($_.Name -match '^(rustc|cargo|clippy-driver)\.exe$' -and $_.CommandLine -match 'Kestrel|letys') } | Select-Object ProcessId,Name,ExecutablePath)
$taskResult=@{checked_utc=(Get-Date).ToUniversalTime().ToString('o');active_processes=$taskActive;free_bytes=(Get-PSDrive -Name D).Free;physical_workspace='D:\Codex\Kestrel'}
$taskResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot ($Phase+'-process-check.json')) -Encoding utf8
if($taskActive.Count -ne 0){throw 'Task native workload/compiler still active'}
$taskResult | ConvertTo-Json -Depth 5 -Compress
