$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path 'work').Path
$trialRoot=(Resolve-Path 'work/perf-062').Path
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('cargo.exe','rustc.exe','rustdoc.exe','kestrel-stress.exe','group-probe.exe')) -and (($_.CommandLine -like '*kestrel-048*') -or ($_.CommandLine -like '*perf-062*'))} | Select-Object ProcessId,Name)
if ($active.Count -ne 0) {throw 'Task-owned process still active'}
$targets=@()
$total=0
foreach ($name in @('kestrel-048-build','kestrel-048-fault-build')) {
    $cacheRoot=(Resolve-Path -LiteralPath (Join-Path $taskRoot $name)).Path
    if (-not $cacheRoot.StartsWith($taskRoot+'\')) {throw 'Cache outside workspace'}
    if ((Get-Content -LiteralPath (Join-Path $cacheRoot 'CACHEDIR.TAG') -First 1) -ne 'Signature: 8a477f597d28d172789f06886806bc55') {throw 'Invalid cache signature'}
    $target=(Resolve-Path -LiteralPath (Join-Path $cacheRoot 'release')).Path
    if (-not $target.StartsWith($cacheRoot+'\') -or -not $target.StartsWith($taskRoot+'\')) {throw 'Unsafe target'}
    $files=@()
    $rescued=@()
    $bytes=0
    foreach ($f in (Get-ChildItem -LiteralPath $target -Recurse -File)) {
        $rel=$f.FullName.Substring($target.Length+1)
        $files+=@{path=$rel;bytes=$f.Length}
        $bytes+=$f.Length
        if ($f.Extension -eq '.exe') {
            $destination=Join-Path $trialRoot ('old-cache-binaries/'+$name+'/'+$rel)
            New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $f.FullName -Destination $destination
            $originalHash=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
            if ($originalHash -ne (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash) {throw 'Rescued executable differs'}
            $rescued+=@{path=$destination;bytes=$f.Length;sha256=$originalHash}
        }
    }
    $targets+=@{absolute_path=$target;cache_signature_verified=$true;bytes=$bytes;files=$files;all_cached_executables_rescued=$rescued}
    $total+=$bytes
}
$freeBefore=(Get-PSDrive C).Free
@{checked_utc=[DateTime]::UtcNow.ToString('o');active_processes=$active;targets=$targets;cache_file_bytes=$total;free_before=$freeBefore;no_database_stores_sources_or_logs_removed=$true} | ConvertTo-Json -Depth 7 | Set-Content -Encoding utf8 (Join-Path $trialRoot 'cache-plan.json')
foreach ($target in $targets) {Remove-Item -LiteralPath $target.absolute_path -Recurse -Force}
@{completed_utc=[DateTime]::UtcNow.ToString('o');cache_directories_removed=$targets.Count;cache_file_bytes_removed=$total;free_before=$freeBefore;free_after=(Get-PSDrive C).Free;all_cached_executables_rescued_for_forensics_only=$true;before_any_062_timing=$true} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $trialRoot 'cache-result.json')
Get-Content -LiteralPath (Join-Path $trialRoot 'cache-result.json')
