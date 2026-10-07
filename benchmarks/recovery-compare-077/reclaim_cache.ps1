$taskWorkspace='C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work'
$taskExpected=Join-Path $taskWorkspace 'perf-076\build-cache'
$taskPlan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cache-reclamation-plan.json') -Raw -Encoding utf8 | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $taskPlan.archive.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPlan.archive.sha256) { throw 'Preserved archive changed' }
$taskResolved=(Resolve-Path -LiteralPath $taskPlan.target).Path
if ($taskResolved -ne $taskExpected -or -not $taskResolved.StartsWith($taskWorkspace+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'Cache outside exact allowed target' }
if ((Get-Item -LiteralPath $taskResolved).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse target rejected' }
$taskItems=@(Get-ChildItem -LiteralPath $taskResolved -Recurse -Force)
if (@($taskItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -ne 0) { throw 'Reparse descendant rejected' }
if (@($taskItems | Where-Object { -not $_.PSIsContainer }).Count -ne @($taskPlan.files).Count) { throw 'Cache inventory changed' }
foreach ($taskFile in $taskPlan.files) {
    $taskFileResolved=(Resolve-Path -LiteralPath $taskFile.path).Path
    if (-not $taskFileResolved.StartsWith($taskResolved+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'File outside exact cache' }
    if ((Get-Item -LiteralPath $taskFileResolved).Length -ne $taskFile.bytes -or (Get-FileHash -LiteralPath $taskFileResolved -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskFile.sha256) { throw 'Cache changed after verification' }
}
Remove-Item -LiteralPath $taskResolved -Recurse -Force
$taskResult=@{removed_utc=(Get-Date).ToUniversalTime().ToString('o');removed_cache_files=@($taskPlan.files).Count;removed_logical_bytes=$taskPlan.logical_bytes;free_bytes_after=(Get-PSDrive -Name C).Free;only_completed_regenerable_cache=$true;all_fixtures_archives_raw_source_inputs_binaries_retained=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'cache-reclamation-result.json') -Encoding utf8
$taskResult | ConvertTo-Json -Compress
