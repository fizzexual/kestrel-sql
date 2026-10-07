$taskWorkspace='C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work'
$taskPlan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cache-reclamation-plan.json') -Raw -Encoding utf8 | ConvertFrom-Json
$taskExpected=@((Join-Path $taskWorkspace 'perf-074\build-cache'),(Join-Path $taskWorkspace 'perf-075\build-cache'))
if (@($taskPlan.targets).Count -ne 2) { throw 'Expected exactly two regenerable caches' }
foreach ($taskArchive in $taskPlan.archives) {
    if ((Get-FileHash -LiteralPath $taskArchive.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskArchive.sha256) { throw 'Preserved archive changed' }
}
foreach ($taskTarget in $taskPlan.targets) {
    $taskResolved=(Resolve-Path -LiteralPath $taskTarget.target).Path
    if ($taskExpected -notcontains $taskResolved -or -not $taskResolved.StartsWith($taskWorkspace+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'Cache outside exact allowed targets' }
    if ((Get-Item -LiteralPath $taskResolved).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse target rejected' }
    $taskItems=@(Get-ChildItem -LiteralPath $taskResolved -Recurse -Force)
    if (@($taskItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -ne 0) { throw 'Reparse descendant rejected' }
    if (@($taskItems | Where-Object { -not $_.PSIsContainer }).Count -ne @($taskTarget.files).Count) { throw 'Inventory mismatch' }
    foreach ($taskFile in $taskTarget.files) {
        $taskFileResolved=(Resolve-Path -LiteralPath $taskFile.path).Path
        if (-not $taskFileResolved.StartsWith($taskResolved+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'File outside exact cache' }
        if ((Get-Item -LiteralPath $taskFileResolved).Length -ne $taskFile.bytes -or (Get-FileHash -LiteralPath $taskFileResolved -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskFile.sha256) { throw 'Cache changed after verification' }
    }
}
foreach ($taskTarget in $taskPlan.targets) { Remove-Item -LiteralPath $taskTarget.target -Recurse -Force }
$taskResult=@{removed_utc=(Get-Date).ToUniversalTime().ToString('o');removed_cache_files=(@($taskPlan.targets[0].files).Count+@($taskPlan.targets[1].files).Count);removed_logical_bytes=($taskPlan.targets[0].logical_bytes+$taskPlan.targets[1].logical_bytes);free_bytes_after=(Get-PSDrive -Name C).Free;only_regenerable_completed_caches=$true;all_preserved_evidence_unchanged=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'cache-reclamation-result.json') -Encoding utf8
$taskResult | ConvertTo-Json -Compress
