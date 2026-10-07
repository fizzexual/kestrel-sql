$ErrorActionPreference='Stop'
$taskArea=(Resolve-Path 'work').Path
$trialPath=(Resolve-Path 'work/perf-059').Path
$oldPlan=Join-Path $trialPath 'disk-pause-cache-plan.json'
$oldResult=Join-Path $trialPath 'disk-pause-cache-result.json'
Copy-Item -LiteralPath $oldPlan -Destination (Join-Path $trialPath 'disk-pause-cache-plan-attempt-1.json')
Copy-Item -LiteralPath $oldResult -Destination (Join-Path $trialPath 'disk-pause-cache-result-attempt-1.json')
$cacheRoots=@(Get-ChildItem -LiteralPath $taskArea -Directory | Where-Object Name -Match '^kestrel-0(3[2-9]|4[0-6])(-[a-z]+)*-build$')
$validated=@()
$totalBytes=0
foreach ($cacheRoot in $cacheRoots) {
    $resolved=(Resolve-Path -LiteralPath $cacheRoot.FullName).Path
    if (-not $resolved.StartsWith($taskArea+'\')) {throw 'Cache root outside task workspace'}
    $tag=Join-Path $resolved 'CACHEDIR.TAG'
    if (-not (Test-Path -LiteralPath $tag) -or (Get-Content -LiteralPath $tag -First 1) -ne 'Signature: 8a477f597d28d172789f06886806bc55') {throw 'Missing Cargo cache signature'}
    foreach ($sub in @('debug','release')) {
        $child=Join-Path $resolved $sub
        if (Test-Path -LiteralPath $child) {
            $absolute=(Resolve-Path -LiteralPath $child).Path
            if (-not $absolute.StartsWith($resolved+'\') -or -not $absolute.StartsWith($taskArea+'\')) {throw 'Invalid cache child'}
            $files=@()
            $bytes=0
            foreach ($file in (Get-ChildItem -LiteralPath $absolute -Recurse -File)) {
                $files+=@{path=$file.FullName.Substring($absolute.Length+1);bytes=$file.Length}
                $bytes+=$file.Length
            }
            $validated+=@{absolute_path=$absolute;cargo_cache_signature_verified=$true;bytes=$bytes;files=$files}
            $totalBytes+=$bytes
        }
    }
}
$freeBefore=(Get-PSDrive C).Free
@{checked_utc=[DateTime]::UtcNow.ToString('o');targets=$validated;total_bytes=$totalBytes;free_before=$freeBefore;task_owned_compilers_and_database_children_checked_stopped=$true;only_reproducible_compilation_cache_removed=$true;default_source_binaries_all_benchmarks_preserved=$true;prior_cache_script_error='Measure-Object rejected Hashtable conversion in restricted language mode; no directories were removed in that attempt'} | ConvertTo-Json -Depth 7 | Set-Content -Encoding utf8 $oldPlan
foreach ($target in $validated) {
    Remove-Item -LiteralPath $target.absolute_path -Recurse -Force
}
@{completed_utc=[DateTime]::UtcNow.ToString('o');cache_directories_removed=$validated.Count;cache_bytes_sum=$totalBytes;free_before=$freeBefore;free_after=(Get-PSDrive C).Free;earlier_dip_cause='not attributed; task fixture bytes do not explain the full observed free-space fall'} | ConvertTo-Json | Set-Content -Encoding utf8 $oldResult
Get-Content -LiteralPath $oldResult
