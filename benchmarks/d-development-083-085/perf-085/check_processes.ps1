param([ValidateSet('pre-smoke','pre-timing','post-timing')][string]$Phase)
$ErrorActionPreference='Stop'
$taskWork='D:\Codex\Kestrel\work\perf-085'
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$taskOther=@(Get-OtherWork)
$taskReset=Get-Content -Raw -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' | ConvertFrom-Json
if($taskReset.phase -ne 'waiting-for-full-codex-exit'){throw 'Reset is no longer waiting; benchmark must not overlap reset IO'}
$taskProof=@{checked_utc=(Get-Date).ToUniversalTime().ToString('o');active_processes=@($taskOther | Select-Object ProcessId,Name,ExecutablePath);reset_phase=$taskReset.phase;free_bytes=(Get-PSDrive D).Free;physical_workspace='D:\Codex\Kestrel'}
$taskProof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskWork ($Phase+'-process-check.json')) -Encoding utf8
if($taskOther.Count -ne 0){throw 'Other Kestrel work active; keep timing stopped'}
$taskProof | ConvertTo-Json -Depth 6 -Compress
