param([Parameter(Mandatory)][int]$OwnerPid,[Parameter(Mandatory)][long]$OwnerCreationFileTime)
$ErrorActionPreference='Stop'
$taskCurrent=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
$taskOwner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$OwnerPid)
if(-not $taskOwner -or $taskCurrent.ParentProcessId -ne $OwnerPid -or $taskOwner.Name -ne 'python.exe' -or $taskOwner.ExecutablePath -ne 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' -or $taskOwner.CommandLine -notmatch '(?i)(^|\s)"?D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]build_payload_147\.py"?\s*$'){throw 'Unverified controller identity'}
if((Get-Process -Id $OwnerPid).StartTime.ToUniversalTime().ToFileTimeUtc() -ne $OwnerCreationFileTime){throw 'Controller creation identity changed'}
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$taskReset=Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json -DateKind String
if($taskReset.phase -ne 'wait-expired-no-source-mutated' -or $taskReset.utc -ne '2026-10-09T10:33:06.6265823Z'){throw 'Reset changed: stop timed cohort'}
if([string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008').State -ne 'Ready' -or [string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Migrate-20261007').State -ne 'Disabled'){throw 'Reset or old migration activity'}
$taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and $_.ProcessId -ne $OwnerPid -and $_.Name -match '^python(w|3.*)?\.exe$' -and
    ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match '(?i)(^|[\\/\s"''])deployment_soak\.py([\s"'']|$)')
})
$taskJobs=@(@(Get-OtherWork | Where-Object ProcessId -ne $OwnerPid)+$taskSupervisors | Sort-Object ProcessId -Unique | ForEach-Object {[pscustomobject]@{pid=$_.ProcessId;name=$_.Name;creation_utc=$_.CreationDate.ToUniversalTime().ToString('o')}})
$taskResetJobs=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -match 'fresh-profile-20261008[/\\].*(fresh_reset|arm_fresh_reset|profile_stage|tree_proof|preserve_app_settings)\.(ps1|py)'} | Select-Object ProcessId,Name)
$taskMutex=[Threading.Mutex]::new($false,'Local\KestrelSqlStorageMigration20261007')
try{if(-not $taskMutex.WaitOne(0)){throw 'Storage cutover active'};$taskMutex.ReleaseMutex()}finally{$taskMutex.Dispose()}
$taskProof=@{utc=(Get-Date).ToUniversalTime().ToString('o');verified_controller_pid=$OwnerPid;verified_controller_creation_filetime=$OwnerCreationFileTime;other_work=$taskJobs;reset_jobs=$taskResetJobs;no_other_task_work=($taskJobs.Count -eq 0 -and $taskResetJobs.Count -eq 0);outside_actual_case_timers_only=$true;no_hash_copy_or_process_change=$true}
$taskProof | ConvertTo-Json -Depth 5 -Compress
if(-not $taskProof.no_other_task_work){exit 3}
# Untimed correctness/build prerequisites only; no performance cases declared.
