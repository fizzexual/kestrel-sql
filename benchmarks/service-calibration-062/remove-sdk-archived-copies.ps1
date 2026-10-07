$ErrorActionPreference='Stop'
$trialRoot=(Resolve-Path 'work/perf-062').Path
$oldRoot=(Resolve-Path 'work/perf-059').Path
$plan=Get-Content -LiteralPath (Join-Path $trialRoot 'sdk-store-archive-plan.json') -Raw | ConvertFrom-Json
$target=(Resolve-Path -LiteralPath $plan.directory).Path
if ($target -ne (Join-Path $oldRoot 'service-fixtures') -or -not $target.StartsWith($oldRoot+'\')) {throw 'Target outside explicitly verified old stores'}
if (-not $plan.each_file_size_crc_and_sha256_matches_local_and_published_archive) {throw 'Archive verification missing'}
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('kestrel.exe','kestrel-stress.exe','released-016.exe','clean-core-061.exe','group-probe.exe','cargo.exe','rustc.exe')) -and (($_.CommandLine -like '*perf-059*') -or ($_.CommandLine -like '*perf-062*'))} | Select-Object ProcessId,Name)
if ($active.Count -ne 0) {throw 'Task-owned process still active'}
$freeBefore=(Get-PSDrive C).Free
Remove-Item -LiteralPath $target -Recurse -Force
@{completed_utc=[DateTime]::UtcNow.ToString('o');directory_removed=$target;original_059_stores_preserved_in_verified_local_and_private_archives=$true;raw_timings_sources_binaries_and_failures_unchanged=$true;free_before=$freeBefore;free_after=(Get-PSDrive C).Free;uncompressed_file_bytes_reclaimed=$plan.uncompressed_bytes} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $trialRoot 'sdk-store-archive-result.json')
Get-Content -LiteralPath (Join-Path $trialRoot 'sdk-store-archive-result.json')
