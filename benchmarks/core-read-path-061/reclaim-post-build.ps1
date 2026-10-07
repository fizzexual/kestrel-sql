$ErrorActionPreference='Stop'
$trialPath=(Resolve-Path 'work/perf-061').Path
$taskArea=(Resolve-Path 'work/perf-061/lab/work').Path
$matrix=Get-Content -LiteralPath (Join-Path $trialPath 'matrix.json') -Raw | ConvertFrom-Json
if (-not $matrix.complete) {throw 'Timings still running'}
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.CommandLine -like '*perf-061*') -and ($_.Name -in @('cargo.exe','rustc.exe','rustdoc.exe','group-probe.exe','kestrel-stress.exe'))} | Select-Object ProcessId,Name)
if ($active.Count -ne 0) {throw 'Task-owned benchmark/compiler children still active'}
$frozen=Join-Path $trialPath 'fault-binaries'
$drivers=@('publication_fault_probe.exe','live_retry_probe.exe','source_fault_probe.exe')
foreach ($driver in $drivers) {
    $cached=Join-Path $taskArea ('kestrel-061-fault-build/release/examples/'+$driver)
    if ((Get-FileHash -LiteralPath $cached -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath (Join-Path $frozen $driver) -Algorithm SHA256).Hash) {throw 'Frozen fault driver differs'}
}
$validated=@()
$totalBytes=0
foreach ($rootName in @('kestrel-061-build','kestrel-061-fault-build')) {
    $cacheRoot=(Resolve-Path -LiteralPath (Join-Path $taskArea $rootName)).Path
    if (-not $cacheRoot.StartsWith($taskArea+'\')) {throw 'Cache root outside workspace'}
    $tag=Join-Path $cacheRoot 'CACHEDIR.TAG'
    if (-not (Test-Path -LiteralPath $tag) -or (Get-Content -LiteralPath $tag -First 1) -ne 'Signature: 8a477f597d28d172789f06886806bc55') {throw 'Invalid Cargo cache signature'}
    foreach ($childName in @('debug','release')) {
        $absolute=(Resolve-Path -LiteralPath (Join-Path $cacheRoot $childName)).Path
        if (-not $absolute.StartsWith($cacheRoot+'\') -or -not $absolute.StartsWith($taskArea+'\')) {throw 'Unsafe cache path'}
        $files=@()
        $bytes=0
        foreach ($file in (Get-ChildItem -LiteralPath $absolute -Recurse -File)) {
            $files+=@{path=$file.FullName.Substring($absolute.Length+1);bytes=$file.Length}
            $bytes+=$file.Length
        }
        $validated+=@{absolute_path=$absolute;cargo_signature_verified=$true;bytes=$bytes;files=$files}
        $totalBytes+=$bytes
    }
}
$freeBefore=(Get-PSDrive C).Free
@{checked_utc=[DateTime]::UtcNow.ToString('o');active_task_processes=$active;targets=$validated;total_bytes=$totalBytes;free_before=$freeBefore;all_source_frozen_binaries_fixtures_logs_and_raw_samples_preserved=$true} | ConvertTo-Json -Depth 7 | Set-Content -Encoding utf8 (Join-Path $trialPath 'post-build-cache-plan.json')
foreach ($target in $validated) {Remove-Item -LiteralPath $target.absolute_path -Recurse -Force}
@{completed_utc=[DateTime]::UtcNow.ToString('o');directories_removed=$validated.Count;reclaimed_file_bytes=$totalBytes;free_before=$freeBefore;free_after=(Get-PSDrive C).Free;before_service_timing=$true} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $trialPath 'post-build-cache-result.json')
Get-Content -LiteralPath (Join-Path $trialPath 'post-build-cache-result.json')
