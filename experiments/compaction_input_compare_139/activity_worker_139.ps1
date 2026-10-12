param([Parameter(Mandatory)][int]$OwnerPid,[Parameter(Mandatory)][long]$OwnerCreationFileTime)
$ErrorActionPreference='Stop'
[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
function Assert-Owner {
    $taskCurrent=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
    $taskOwner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$OwnerPid)
    if(-not $taskOwner -or $taskCurrent.ParentProcessId -ne $OwnerPid -or $taskOwner.Name -ne 'python.exe' -or $taskOwner.ExecutablePath -ne 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' -or $taskOwner.CommandLine -notmatch '(?i)(^|\s)"?D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\](run_phase_compare_139|smoke_phase_compare_139)\.py"?\s*$'){throw 'Unverified controller identity'}
    if((Get-Process -Id $OwnerPid).StartTime.ToUniversalTime().ToFileTimeUtc() -ne $OwnerCreationFileTime){throw 'Controller identity changed'}
}
Assert-Owner
while($null -ne ($taskLine=[Console]::In.ReadLine())){
    $taskRequest=$taskLine | ConvertFrom-Json -DateKind String
    if($taskRequest.operation -eq 'stop'){exit 0}
    if($taskRequest.operation -ne 'check' -or $taskRequest.request_id -lt 0){throw 'Invalid metadata request'}
    Assert-Owner
    $taskReset=Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json -DateKind String
    if($taskReset.phase -ne 'wait-expired-no-source-mutated' -or $taskReset.utc -ne '2026-10-09T10:33:06.6265823Z'){throw 'Reset state changed'}
    if([string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008').State -ne 'Ready' -or [string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Migrate-20261007').State -ne 'Disabled'){throw 'Reset/task state changed'}
    $taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.ProcessId -ne $OwnerPid -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
    $taskJobs=@(@(Get-OtherWork | Where-Object ProcessId -ne $OwnerPid)+$taskSupervisors | Sort-Object ProcessId -Unique | ForEach-Object {
        [pscustomobject]@{pid=$_.ProcessId;name=$_.Name;creation_utc=$_.CreationDate.ToUniversalTime().ToString('o');executable_path=$_.ExecutablePath;
            bounded_nonsecret_reason=@{owned_workspace_executable=($_.ExecutablePath -like 'D:\Codex\Kestrel\work\*' -or $_.ExecutablePath -like 'D:\Codex\Kestrel\outputs\kestrel-sql\*');python_supervisor=($_.Name -match '^python(w|3.*)?\.exe$');python_text_in_command=($_.CommandLine -match '\.py');build_copy_hash_token=($_.CommandLine -match '(?i)\b(cargo|rustc|robocopy|xcopy|Copy-Item|Move-Item|Remove-Item|Get-FileHash|hashlib|build|package|compile)\b')}
        }
    })
    $taskResetJobs=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -match 'fresh-profile-20261008[/\\].*(fresh_reset|arm_fresh_reset|profile_stage|tree_proof|preserve_app_settings)\.(ps1|py)'} | Select-Object ProcessId,Name)
    $taskMutex=[Threading.Mutex]::new($false,'Local\KestrelSqlStorageMigration20261007')
    try{if(-not $taskMutex.WaitOne(0)){throw 'Storage cutover active'};$taskMutex.ReleaseMutex()}finally{$taskMutex.Dispose()}
    $taskProof=@{utc=(Get-Date).ToUniversalTime().ToString('o');verified_controller_pid=$OwnerPid;verified_controller_creation_filetime=$OwnerCreationFileTime;other_work=$taskJobs;reset_jobs=$taskResetJobs;no_other_task_work=($taskJobs.Count -eq 0 -and $taskResetJobs.Count -eq 0);outside_actual_case_timers_only=$true;no_hash_copy_or_process_change=$true;persistent_worker_pid=$PID;worker_blocks_on_input_between_requests=$true}
    $taskMessages=@($taskProof);$taskExit=0
    if(-not $taskProof.no_other_task_work){$taskExit=3}else{
        $taskGlobalLines=& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
        $taskGlobal=$taskGlobalLines | ConvertFrom-Json -DateKind String
        $taskMessages+=@($taskGlobal)
        if(-not $taskGlobal.no_visible_build_jobs){$taskExit=3}
    }
    $taskResponse=@{request_id=$taskRequest.request_id;place=$taskRequest.place;index=$taskRequest.index;exit=$taskExit;messages=$taskMessages;no_probe_during_native_case=$true}
    [Console]::Out.WriteLine(($taskResponse | ConvertTo-Json -Depth 8 -Compress))
    [Console]::Out.Flush()
}
