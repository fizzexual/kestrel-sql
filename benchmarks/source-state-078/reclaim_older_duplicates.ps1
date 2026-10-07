$taskWorkspace='C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work'
$taskPlan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'reclamation-older-plan.json') -Raw -Encoding utf8 | ConvertFrom-Json
$taskExpected=@((Join-Path $taskWorkspace 'perf-072\build-cache'),(Join-Path $taskWorkspace 'perf-072\rust-temp'),(Join-Path $taskWorkspace 'perf-073\build-cache'),(Join-Path $taskWorkspace 'perf-073\rust-temp'))
if (@($taskPlan.targets).Count -ne 4) { throw 'Expected exactly four verified directories' }
foreach ($taskArchive in $taskPlan.archives) { if ((Get-FileHash -LiteralPath $taskArchive.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskArchive.sha256) { throw 'Preserved archive changed' } }
foreach ($taskTarget in $taskPlan.targets) {
    $taskResolved=(Resolve-Path -LiteralPath $taskTarget.target).Path
    if ($taskExpected -notcontains $taskResolved -or -not $taskResolved.StartsWith($taskWorkspace+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'Duplicate outside exact allowed targets' }
    if ((Get-Item -LiteralPath $taskResolved).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse target rejected' }
    $taskItems=@(Get-ChildItem -LiteralPath $taskResolved -Recurse -Force)
    if (@($taskItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -ne 0) { throw 'Reparse descendant rejected' }
    if (@($taskItems | Where-Object { -not $_.PSIsContainer }).Count -ne @($taskTarget.files).Count) { throw 'Inventory mismatch' }
    foreach ($taskFile in $taskTarget.files) {
        $taskFileResolved=(Resolve-Path -LiteralPath $taskFile.path).Path
        if (-not $taskFileResolved.StartsWith($taskResolved+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'File outside exact duplicate target' }
        if ((Get-Item -LiteralPath $taskFileResolved).Length -ne $taskFile.bytes -or (Get-FileHash -LiteralPath $taskFileResolved -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskFile.sha256) { throw 'Duplicate changed after archive verification' }
    }
}
$taskFiles=0; $taskBytes=0
foreach ($taskTarget in $taskPlan.targets) { $taskFiles+=@($taskTarget.files).Count; $taskBytes+=$taskTarget.logical_bytes; Remove-Item -LiteralPath $taskTarget.target -Recurse -Force }
$taskResult=@{removed_utc=(Get-Date).ToUniversalTime().ToString('o');removed_files=$taskFiles;removed_logical_bytes=$taskBytes;free_bytes_after=(Get-PSDrive -Name C).Free;only_verified_archived_duplicates=$true;all_full_private_local_archives_and_raw_source_evidence_retained=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'reclamation-older-result.json') -Encoding utf8
$taskResult | ConvertTo-Json -Compress
