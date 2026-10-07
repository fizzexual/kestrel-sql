$ErrorActionPreference='Stop'
$taskArea=(Resolve-Path 'work').Path
$trialPath=(Resolve-Path 'work/perf-061').Path
$active=@(Get-CimInstance Win32_Process | Where-Object {($_.Name -in @('cargo.exe','rustc.exe','rustdoc.exe')) -and (($_.CommandLine -like '*kestrel-048-build*') -or ($_.CommandLine -like '*kestrel-060-*-control-build*'))} | Select-Object ProcessId,Name)
if ($active.Count -ne 0) {throw 'Task-owned compilation still active'}
$candidates=@(@{root='kestrel-048-build';child='debug'},@{root='kestrel-060-sdk-control-build';child='release'},@{root='kestrel-060-candidate-control-build';child='release'})
$validated=@()
$totalBytes=0
foreach ($candidate in $candidates) {
    $cacheRoot=(Resolve-Path -LiteralPath (Join-Path $taskArea $candidate.root)).Path
    if (-not $cacheRoot.StartsWith($taskArea+'\')) {throw 'Cache root outside workspace'}
    $tag=Join-Path $cacheRoot 'CACHEDIR.TAG'
    if (-not (Test-Path -LiteralPath $tag) -or (Get-Content -LiteralPath $tag -First 1) -ne 'Signature: 8a477f597d28d172789f06886806bc55') {throw 'Invalid Cargo signature'}
    $child=Join-Path $cacheRoot $candidate.child
    if (Test-Path -LiteralPath $child) {
        $absolute=(Resolve-Path -LiteralPath $child).Path
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
@{checked_utc=[DateTime]::UtcNow.ToString('o');active_compilers=$active;targets=$validated;total_bytes=$totalBytes;free_before=$freeBefore;source_binaries_all_reports_stores_and_published_artifacts_preserved=$true} | ConvertTo-Json -Depth 7 | Set-Content -Encoding utf8 (Join-Path $trialPath 'cache-plan.json')
foreach ($target in $validated) {Remove-Item -LiteralPath $target.absolute_path -Recurse -Force}
@{completed_utc=[DateTime]::UtcNow.ToString('o');directories_removed=$validated.Count;reclaimed_file_bytes=$totalBytes;free_before=$freeBefore;free_after=(Get-PSDrive C).Free} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $trialPath 'cache-result.json')
Get-Content -LiteralPath (Join-Path $trialPath 'cache-result.json')
