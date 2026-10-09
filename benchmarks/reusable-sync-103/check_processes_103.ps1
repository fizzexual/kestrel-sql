param([ValidateSet('pretime','posttime','preaudit','prepreserve','final')][string]$Phase)
$ErrorActionPreference='Stop'
$taskControl='D:\Codex\Migration-20261007\fresh-profile-20261008'
$taskHelper=Join-Path $taskControl 'fresh_reset.ps1'
if((Get-FileHash -LiteralPath $taskHelper -Algorithm SHA256).Hash.ToLowerInvariant() -ne '005d2246f6948eb9d2cef36a9169d9bcd82c9289c9bb0c5f7565fdae79b27e3b'){throw 'Reviewed reset helper changed'}
. $taskHelper -LoadForTests
$taskRoot='D:\Codex\Kestrel'
Assert-Real $taskRoot
Assert-Real (Join-Path $taskRoot 'work\perf-103')
Assert-Real 'C:\Users\Frizer\.codex'
$taskStatusPath=Join-Path $taskControl 'reset-status.json'
$taskStatusHash=(Get-FileHash -LiteralPath $taskStatusPath -Algorithm SHA256).Hash
$taskReset=Get-Content -LiteralPath $taskStatusPath -Raw | ConvertFrom-Json -DateKind String
if($taskReset.phase -ne 'wait-expired-no-source-mutated' -or $taskReset.utc -ne '2026-10-09T10:33:06.6265823Z' -or @($taskReset.verified_c_backups_already_removed).Count -ne 0){throw 'Expired reset state changed; stop SQL work'}
$taskFresh=Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008'
$taskInfo=Get-ScheduledTaskInfo -TaskName 'Codex-Kestrel-Fresh-20261008'
if([string]$taskFresh.State -ne 'Ready' -or $taskInfo.LastTaskResult -ne 2){throw 'Reset task not in verified terminal expiry'}
if([string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Migrate-20261007').State -ne 'Disabled'){throw 'Old migration task must stay disabled'}
$taskOwnerSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
if($taskOwnerSid -ne 'S-1-5-21-1859710255-3507972019-1030976530-1001'){throw 'Owner changed'}
$taskFormer=Get-CimInstance Win32_Process -Filter 'ProcessId=23176'
if($taskFormer -and $taskFormer.CreationDate.ToUniversalTime().ToString('o') -eq '2026-10-08T10:33:01.5395400Z'){throw 'Former reset worker still exists'}
$taskResetJobs=@(Get-CimInstance Win32_Process | Where-Object {
 $_.ProcessId -ne $PID -and $_.CommandLine -match 'fresh-profile-20261008[/\\].*(fresh_reset|arm_fresh_reset|profile_stage|tree_proof|preserve_app_settings)\.(ps1|py)'
})
if($taskResetJobs.Count){throw 'Reset/preparation work active; stop SQL work'}
$taskMutex=[Threading.Mutex]::new($false,'Local\KestrelSqlStorageMigration20261007')
try{
 if(-not $taskMutex.WaitOne(0)){throw 'Storage cutover mutex owned; no SQL work'}
 $taskMutex.ReleaseMutex()
}finally{$taskMutex.Dispose()}
$taskJobs=@(Get-OtherWork)
if($taskJobs.Count){$taskJobs | ConvertTo-Json -Depth 5;throw 'Task work active; no phase overlap'}
if((Get-FileHash -LiteralPath $taskStatusPath -Algorithm SHA256).Hash -ne $taskStatusHash -or [string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008').State -ne 'Ready'){throw 'Reset state changed during guard'}
$taskProof=@{utc=(Get-Date).ToUniversalTime().ToString('o');phase=$Phase;active_processes=@();reset_phase=$taskReset.phase;reset_status_utc=$taskReset.utc;reset_status_sha256=$taskStatusHash.ToLowerInvariant();reset_worker_active=$false;fresh_task_state='Ready';fresh_task_last_result=2;old_task_state='Disabled';owner_sid=$taskOwnerSid;verified_idle_terminal_reset=$true;shared_C_home_still_real=$true;D_free_bytes=(Get-PSDrive D).Free;no_reset_task_setting_or_source_change=$true}
$taskProof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskRoot ('work\guard-'+$Phase+'-103-'+(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffffff')+'.json')) -Encoding utf8
$taskProof | ConvertTo-Json -Compress
