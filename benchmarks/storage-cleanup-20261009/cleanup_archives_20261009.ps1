param()
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:\Codex\Kestrel'
$taskOutputs = 'D:\Codex\Kestrel\outputs'
$taskEvidence = 'D:\Codex\Kestrel\work\storage-cleanup-20261009-0841'
$taskGh = 'C:\Users\Frizer\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe'
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests

function Save-New([string]$Name, [object]$Value) {
    $taskDestination = Join-Path $taskEvidence $Name
    if (Test-Path -LiteralPath $taskDestination) { throw "Evidence already exists: $Name" }
    $Value | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $taskDestination -Encoding utf8
}

function Assert-CleanupIdle {
    if ((Get-OtherWork).Count) { throw 'Task work active; cleanup stopped' }
    $taskState = Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json
    if ($taskState.phase -ne 'waiting-for-full-codex-exit') { throw 'Reset phase changed; cleanup stopped' }
    $taskResetWorker = Get-CimInstance Win32_Process -Filter 'ProcessId=23176'
    if (-not $taskResetWorker -or $taskResetWorker.CreationDate.ToUniversalTime().ToString('o') -ne '2026-10-08T10:33:01.5395400Z') { throw 'Reset identity changed' }
    $taskResetOwner = Invoke-CimMethod -InputObject $taskResetWorker -MethodName GetOwnerSid
    if ($taskResetOwner.Sid -ne [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) { throw 'Reset owner changed' }
}

function Get-PrivateApi([string]$Endpoint) {
    $taskResponse = & $taskGh api $Endpoint
    if ($LASTEXITCODE -ne 0) { throw "Private GitHub API failed: $Endpoint" }
    return ($taskResponse | ConvertFrom-Json -DateKind String)
}

function Assert-ExactFile([object]$Entry) {
    $taskFullPath = [IO.Path]::GetFullPath($Entry.path)
    $taskName = [IO.Path]::GetFileName($taskFullPath)
    if ($taskFullPath -ne $Entry.path.Replace('/', '\') -or [IO.Path]::GetDirectoryName($taskFullPath) -ne $taskOutputs) { throw 'Noncanonical/out-of-scope file' }
    if ($taskName -notmatch '^kestrel-sql[-a-zA-Z0-9.]*\.zip$' -or $taskName -ne $Entry.asset.name) { throw 'Unexpected package name' }
    if ($taskName -like 'kestrel-sql-0.3.16*' -or $taskName -like 'kestrel-sql-development-061-*') { throw 'Protected current/active archive selected' }
    $taskItem = Get-Item -LiteralPath $taskFullPath -Force
    if ($taskItem.PSIsContainer -or ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -or (Resolve-Path -LiteralPath $taskFullPath).Path -ne $taskFullPath) { throw 'File is a directory/reparse/redirected path' }
    if ($taskItem.Length -ne $Entry.bytes -or $Entry.bytes -ne $Entry.asset.size -or $Entry.download_bytes -ne $Entry.bytes) { throw 'Archive size changed' }
    if (-not $Entry.verified -or $Entry.download_exit_code -ne 0 -or -not $Entry.sidecar_matches -or $Entry.download_zip_prefix -ne '504b0304') { throw 'Incomplete remote download proof' }
    if ($Entry.local_sha256 -notmatch '^[0-9a-f]{64}$' -or $Entry.download_sha256 -ne $Entry.local_sha256 -or $Entry.asset.digest -ne ('sha256:' + $Entry.local_sha256)) { throw 'Proof digest mismatch' }
    return $taskFullPath
}

Assert-Real $taskRoot
Assert-Real $taskOutputs
Assert-Real $taskEvidence
Assert-CleanupIdle
$taskPlanPath = Join-Path $taskEvidence 'verified-deletion-plan.json'
$taskPlan = Get-Content -LiteralPath $taskPlanPath -Raw | ConvertFrom-Json -DateKind String
if (-not $taskPlan.complete -or -not $taskPlan.remote_private_verified -or -not $taskPlan.only_top_level_redundant_zip_files -or $taskPlan.recursive_deletion) { throw 'Invalid deletion scope' }
if (@($taskPlan.entries).Count -ne $taskPlan.files) { throw 'Plan count mismatch' }
$taskRepository = Get-PrivateApi 'repos/fizzexual/kestrel-sql'
if (-not $taskRepository.private -or $taskRepository.full_name -ne 'fizzexual/kestrel-sql') { throw 'Repository privacy/identity changed' }
$taskValidation = @()
foreach ($taskEntry in $taskPlan.entries) {
    $taskFullPath = Assert-ExactFile $taskEntry
    $taskHash = (Get-FileHash -LiteralPath $taskFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($taskHash -ne $taskEntry.local_sha256) { throw "Local archive changed: $taskFullPath" }
    $taskAsset = Get-PrivateApi ('repos/fizzexual/kestrel-sql/releases/assets/' + $taskEntry.asset.id)
    if ($taskAsset.id -ne $taskEntry.asset.id -or $taskAsset.name -ne $taskEntry.asset.name -or $taskAsset.state -ne 'uploaded' -or $taskAsset.size -ne $taskEntry.bytes -or $taskAsset.digest -ne $taskEntry.asset.digest) { throw 'Remote archive changed' }
    $taskValidation += @{path = $taskFullPath; bytes = $taskEntry.bytes; sha256 = $taskHash; asset_id = $taskAsset.id; github_digest = $taskAsset.digest; download_url = $taskAsset.browser_download_url}
    Write-Output ('Revalidated ' + [IO.Path]::GetFileName($taskFullPath))
}
if (($taskValidation | Measure-Object bytes -Sum).Sum -ne $taskPlan.bytes) { throw 'Plan byte count mismatch' }
Assert-CleanupIdle
$taskBeforeFree = (Get-PSDrive D).Free
Save-New 'predelete-validation.json' @{utc = (Get-Date).ToUniversalTime().ToString('o'); plan_sha256 = (Get-FileHash -LiteralPath $taskPlanPath -Algorithm SHA256).Hash.ToLowerInvariant(); entries = $taskValidation; no_recursive_operations = $true; repository_private = $true; D_free_before_bytes = $taskBeforeFree}
$taskDeleted = @()
try {
    foreach ($taskEntry in $taskPlan.entries) {
        Assert-CleanupIdle
        Assert-Real $taskOutputs
        $taskFullPath = Assert-ExactFile $taskEntry
        Remove-Item -LiteralPath $taskFullPath -Force
        if (Test-Path -LiteralPath $taskFullPath) { throw 'Delete did not complete' }
        $taskRecord = @{path = $taskFullPath; bytes = $taskEntry.bytes; sha256 = $taskEntry.local_sha256; asset_id = $taskEntry.asset.id; download_url = $taskEntry.asset.browser_download_url; utc = (Get-Date).ToUniversalTime().ToString('o'); verified_remote_full_download = $true}
        Save-New ('deleted-' + $taskEntry.asset.id + '.json') $taskRecord
        $taskDeleted += $taskRecord
        Write-Output ('Removed backed-up duplicate ' + [IO.Path]::GetFileName($taskFullPath))
    }
    Save-New 'cleanup-result.json' @{complete = $true; utc = (Get-Date).ToUniversalTime().ToString('o'); deleted = $taskDeleted; files = $taskDeleted.Count; logical_bytes_removed = ($taskDeleted | Measure-Object bytes -Sum).Sum; D_free_before_bytes = $taskBeforeFree; D_free_after_bytes = (Get-PSDrive D).Free; recursive_deletions = 0; original_raw_and_failed_benchmark_stores_retained = $true; repository_files_untouched = $true; current_supported_and_active_061_archives_retained = $true; unmatched_and_unverified_archives_retained = $true}
    Write-Output ('Cleanup complete: ' + $taskDeleted.Count + ' files, ' + ($taskDeleted | Measure-Object bytes -Sum).Sum + ' logical bytes')
} catch {
    Save-New 'cleanup-partial-failure.json' @{utc = (Get-Date).ToUniversalTime().ToString('o'); error = $_.Exception.Message; deleted = $taskDeleted; remaining_files_retained = $true}
    throw
}
