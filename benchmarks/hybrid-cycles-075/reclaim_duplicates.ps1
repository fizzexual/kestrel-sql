$taskWorkspace='C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work'
$taskExpectedTarget=Join-Path $taskWorkspace 'perf-073\fixtures'
$taskPlan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'fixture-reclamation-plan.json') -Raw -Encoding utf8 | ConvertFrom-Json
$taskResolved=(Resolve-Path -LiteralPath $taskPlan.target).Path
if ($taskResolved -ne $taskExpectedTarget -or -not $taskResolved.StartsWith($taskWorkspace+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside the exact duplicate fixture directory' }
if ((Get-Item -LiteralPath $taskResolved).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse target rejected' }
$taskItems=@(Get-ChildItem -LiteralPath $taskResolved -Recurse -Force)
if (@($taskItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -ne 0) { throw 'Reparse descendant rejected' }
if (@($taskItems | Where-Object { -not $_.PSIsContainer }).Count -ne 6420 -or @($taskPlan.files).Count -ne 6420) { throw 'Inventory mismatch' }
if ((Get-FileHash -LiteralPath $taskPlan.archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPlan.archive_sha256) { throw 'Preserved full archive differs' }
foreach ($taskFile in $taskPlan.files) {
    $taskFileResolved=(Resolve-Path -LiteralPath $taskFile.path).Path
    if (-not $taskFileResolved.StartsWith($taskResolved+'\',[System.StringComparison]::OrdinalIgnoreCase)) { throw 'File outside checked target' }
    if ((Get-Item -LiteralPath $taskFileResolved).Length -ne $taskFile.bytes -or (Get-FileHash -LiteralPath $taskFileResolved -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskFile.sha256) { throw 'Duplicate changed after verification' }
}
Remove-Item -LiteralPath $taskResolved -Recurse -Force
$taskResult=@{removed_utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskResolved;removed_duplicate_files=6420;removed_logical_bytes=$taskPlan.total_bytes;free_bytes_after=(Get-PSDrive -Name C).Free;full_archive_unchanged=$true;only_duplicate_073_cases=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'fixture-reclamation-result.json') -Encoding utf8
$taskResult | ConvertTo-Json -Compress
