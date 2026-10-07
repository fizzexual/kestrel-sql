$ErrorActionPreference='Stop'
$workRoot=(Resolve-Path -LiteralPath './work').Path
$trialRoot=(Resolve-Path -LiteralPath './work/perf-064').Path
$plan=Get-Content -LiteralPath (Join-Path $trialRoot 'prior-store-archive-plan.json') -Raw | ConvertFrom-Json
$permitted=@((Join-Path (Join-Path $workRoot 'perf-062') 'service-fixtures'),(Join-Path (Join-Path $workRoot 'perf-063') 'service-fixtures'),(Join-Path (Join-Path $workRoot 'perf-063') 'recovery-fixtures'))
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('released-016.exe','clean-core-061.exe','kestrel.exe','kestrel-stress.exe','cargo.exe','rustc.exe')) -and ($_.CommandLine -like '*letys*')} | Select-Object ProcessId,Name)
if ($active.Count -ne 0) {throw 'Task-owned process still active'}
foreach ($entry in $plan.directories) {
    $target=(Resolve-Path -LiteralPath $entry.directory).Path
    if ($target -notin $permitted -or -not $target.StartsWith($workRoot+'\') -or -not $entry.each_file_size_crc_sha256_matches_local_and_published_archive) {throw 'Unexpected archive target or missing verification'}
}
$freeBefore=(Get-PSDrive C).Free
foreach ($entry in $plan.directories) {Remove-Item -LiteralPath $entry.directory -Recurse -Force}
@{completed_utc=[DateTime]::UtcNow.ToString('o');directories_removed=@($plan.directories.directory);all_full_stores_in_verified_local_and_private_archives=$true;raw_timings_sources_binaries_failures_and_original_results_unchanged=$true;free_before=$freeBefore;free_after=(Get-PSDrive C).Free;uncompressed_bytes_reclaimed=($plan.directories | Measure-Object -Property uncompressed_bytes -Sum).Sum} | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 (Join-Path $trialRoot 'prior-store-archive-result.json')
Get-Content -LiteralPath (Join-Path $trialRoot 'prior-store-archive-result.json')
