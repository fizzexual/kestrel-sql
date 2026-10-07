$ErrorActionPreference='Stop'
$trialRoot=(Resolve-Path 'work/perf-066').Path
$ownedRoot=(Resolve-Path 'work/perf-064/lab/work').Path
$proof=Get-Content -LiteralPath (Join-Path $trialRoot 'cache-preflight.json') -Raw | ConvertFrom-Json
if (-not $proof.passed) {throw 'Missing frozen-evidence proof'}
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('cargo.exe','rustc.exe','rustdoc.exe','encoder-probe.exe','kestrel-stress.exe','kestrel.exe','baseline-publication.exe','candidate-publication.exe')) -and ($_.CommandLine -like '*letys*')} | Select-Object ProcessId,Name)
if ($active.Count -ne 0) {throw 'Task-owned process still active'}
$targets=@();$total=0
foreach ($name in @('kestrel-064-build','kestrel-064-fault-build')) {
    $cacheRoot=(Resolve-Path -LiteralPath (Join-Path $ownedRoot $name)).Path
    if (-not $cacheRoot.StartsWith($ownedRoot+'\')) {throw 'Cache root outside task'}
    if ((Get-Content -LiteralPath (Join-Path $cacheRoot 'CACHEDIR.TAG') -First 1) -ne 'Signature: 8a477f597d28d172789f06886806bc55') {throw 'Invalid Cargo cache signature'}
    $target=(Resolve-Path -LiteralPath (Join-Path $cacheRoot 'debug')).Path
    if ($target -ne (Join-Path $cacheRoot 'debug') -or -not $target.StartsWith($ownedRoot+'\')) {throw 'Unsafe absolute deletion target'}
    $files=@();$bytes=0
    foreach ($file in (Get-ChildItem -LiteralPath $target -Recurse -File)) {
        $files+=@{path=$file.FullName.Substring($target.Length+1);bytes=$file.Length};$bytes+=$file.Length
    }
    $targets+=@{absolute_path=$target;cache_signature_verified=$true;bytes=$bytes;files=$files};$total+=$bytes
}
$freeBefore=(Get-PSDrive C).Free
@{checked_utc=[DateTime]::UtcNow.ToString('o');active_processes=$active;targets=$targets;cache_file_bytes=$total;free_before=$freeBefore;after_all065_and066_timing=$true;no_sources_logs_inputs_stores_release_libraries_or_frozen_executables_removed=$true} | ConvertTo-Json -Depth 7 | Set-Content -Encoding utf8 (Join-Path $trialRoot 'cache-plan.json')
foreach ($target in $targets) {Remove-Item -LiteralPath $target.absolute_path -Recurse -Force}
@{completed_utc=[DateTime]::UtcNow.ToString('o');directories_removed=$targets.Count;cache_file_bytes_removed=$total;free_before=$freeBefore;free_after=(Get-PSDrive C).Free;only_tagged_debug_caches_removed=$true;all_measured_frozen_binaries_and_data_retained=$true} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $trialRoot 'cache-result.json')
Get-Content -LiteralPath (Join-Path $trialRoot 'cache-result.json')
