param([string]$Phase)
if ($Phase -notin @('pre-build','pre-qualification','post-qualification')) { throw 'Unknown process check phase' }
$taskActive=@(Get-CimInstance Win32_Process | Where-Object { ($_.ExecutablePath -like '*\letys\work\*' -or $_.ExecutablePath -like '*\letys\outputs\kestrel-sql\*') -and ($_.Name -like '*.exe') } | Select-Object ProcessId,Name,ExecutablePath,CommandLine)
$taskResult=@{checked_utc=(Get-Date).ToUniversalTime().ToString('o');active_processes=$taskActive;free_bytes=(Get-PSDrive -Name C).Free}
$taskResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot ($Phase+'-process-check.json')) -Encoding utf8
if ($taskActive.Count -ne 0) { throw 'Owned native workload still active' }
$taskResult | ConvertTo-Json -Depth 5 -Compress
