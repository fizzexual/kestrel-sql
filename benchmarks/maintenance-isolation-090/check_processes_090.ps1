param([ValidateSet('pre-timing','post-timing')][string]$Phase)
$ErrorActionPreference='Stop'
$taskWork='D:\Codex\Kestrel\work\perf-090'
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$taskJobs=@(Get-OtherWork)
$taskReset=Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json
if($taskReset.phase -ne 'waiting-for-full-codex-exit'){throw 'Reset no longer waiting; do not run service/audit IO'}
Assert-Real 'D:\Codex\Kestrel'; Assert-Real 'D:\Codex\Kestrel\work'; Assert-Real $taskWork
$taskWorker=Get-CimInstance Win32_Process -Filter 'ProcessId=23176'
if(-not $taskWorker -or $taskWorker.CreationDate.ToUniversalTime().ToString('o') -ne '2026-10-08T10:33:01.5395400Z'){throw 'Waiting worker identity changed'}
$taskOwner=Invoke-CimMethod -InputObject $taskWorker -MethodName GetOwnerSid
if($taskOwner.Sid -ne [Security.Principal.WindowsIdentity]::GetCurrent().User.Value){throw 'Waiting worker owner changed'}
$taskProof=@{checked_utc=(Get-Date).ToUniversalTime().ToString('o'); active_processes=@($taskJobs | Select-Object ProcessId,Name,ExecutablePath); reset_phase=$taskReset.phase; worker_identity_and_owner_verified=$true; free_bytes=(Get-PSDrive D).Free; physical_workspace=$taskWork}
$taskProof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskWork ($Phase+'-process-check.json')) -Encoding utf8
if($taskJobs.Count){throw 'Other task work active; no overlapping work allowed'}
$taskProof | ConvertTo-Json -Compress
