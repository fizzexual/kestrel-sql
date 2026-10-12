$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
$taskStarted=(Get-Date).ToUniversalTime()
$taskDeadline=$taskStarted.AddHours(2)
$taskAttempts=0
$taskPolls=0
$taskProofPath=Join-Path $taskRoot 'phase145-cohort-launch-wait-actual-exits.json'
if(Test-Path -LiteralPath $taskProofPath){throw 'Do not overwrite actual waiter exit'}
if(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json')){throw 'Controller already attempted; inspect its prefix'}
if(Test-Path -LiteralPath (Join-Path $taskRoot 'perf-145\fixtures')){throw 'Controller fixture already exists'}
$taskStartedProof=Join-Path $taskRoot 'phase145-cohort-launch-wait-started.json'
if(Test-Path -LiteralPath $taskStartedProof){throw 'Existing waiter identity; inspect rather than duplicate'}
$taskSelf=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
@{utc=$taskStarted.ToString('o');waiter_pid=$PID;waiter_creation_utc=$taskSelf.CreationDate.ToUniversalTime().ToString('o');waiter_creation_filetime=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToFileTimeUtc();source=$PSCommandPath;metadata_only_until_controller_launch=$true;no_duplicate_automation=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskStartedProof -Encoding utf8
try {
    while((Get-Date).ToUniversalTime() -lt $taskDeadline){
        $taskProbeStarted=(Get-Date).ToUniversalTime()
        $taskReset=Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json -DateKind String
        if($taskReset.phase -ne 'wait-expired-no-source-mutated' -or $taskReset.utc -ne '2026-10-09T10:33:06.6265823Z'){throw 'Reset changed; stop without native jobs'}
        if([string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008').State -ne 'Ready' -or [string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Migrate-20261007').State -ne 'Disabled'){throw 'Reset/migration task state changed'}
        $taskProcesses=@(Get-CimInstance Win32_Process)
        $taskResetJobs=@($taskProcesses | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -match 'fresh-profile-20261008[/\\].*(fresh_reset|arm_fresh_reset|profile_stage|tree_proof|preserve_app_settings)\.(ps1|py)'})
        if($taskResetJobs.Count){throw 'Reset worker active; no SQL work'}
        $taskJobs=@($taskProcesses | Where-Object {
            $_.ProcessId -ne $PID -and (
                $_.ExecutablePath -like 'D:\Codex\Kestrel\work\*' -or $_.ExecutablePath -like 'D:\Codex\Kestrel\outputs\kestrel-sql\*' -or
                ($_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')) -or
                ($_.Name -match '^(rustc|cargo|clippy-driver)\.exe$' -and $_.CommandLine -match 'Kestrel|letys') -or
                ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\].*\.py' -and $_.ParentProcessId -ne $PID) -or
                ($_.Name -match '^(robocopy|xcopy|7z|tar)\.exe$' -and $_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]')
            )
        })
        $taskClear=($taskJobs.Count -eq 0)
        if($taskClear){
            $taskGlobalLines=& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
            $taskGlobal=$taskGlobalLines | ConvertFrom-Json -DateKind String
            $taskClear=$taskGlobal.no_visible_build_jobs
        }
        $taskPolls++
        @{started_utc=$taskProbeStarted.ToString('o');utc=(Get-Date).ToUniversalTime().ToString('o');poll=$taskPolls;clear=$taskClear;other_work=@($taskJobs | ForEach-Object {@{pid=$_.ProcessId;name=$_.Name;creation_utc=$_.CreationDate.ToUniversalTime().ToString('o')}});metadata_only=$true;no_native_case_started_by_poll=$true} | ConvertTo-Json -Depth 5 -Compress | Add-Content -LiteralPath (Join-Path $taskRoot 'phase145-cohort-launch-wait-metadata.jsonl') -Encoding utf8
        if($taskClear){
            $taskAttempts++
            & 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File 'D:\Codex\Kestrel\work\launch_phase_compare_145.ps1'
            $taskChildExit=$LASTEXITCODE
            # No gate probes while the qualified controller/native children run.
            if(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json')){
                $taskActual=Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json') -Raw | ConvertFrom-Json
                if(-not $taskActual.actual_controller_wait_completed -or $taskActual.cohort_actual_exit -ne $taskChildExit){throw 'Actual controller wait/exit mismatch'}
                @{utc=(Get-Date).ToUniversalTime().ToString('o');gate_actual_exit=$taskChildExit;actual_wait_completed=$true;controller_launch_attempts=$taskAttempts;metadata_polls=$taskPolls;controller_attempted=$true;no_native_case_or_checkpoint_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskProofPath -Encoding utf8
                exit $taskChildExit
            }
            throw 'Launcher held before controller creation; preserve existing append/guard and use a separate verified continuation, never retry here'
        }
        Start-Sleep -Seconds 10
    }
    throw 'Metadata launch wait deadline; no controller started'
} catch {
    @{utc=(Get-Date).ToUniversalTime().ToString('o');gate_actual_exit=1;actual_wait_completed=$true;controller_launch_attempts=$taskAttempts;metadata_polls=$taskPolls;bounded_error=$_.Exception.Message;controller_actual_exit_proof_present=(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json'));checkpoint_append_present=(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-running-next-proof.json'));no_case_or_checkpoint_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskProofPath -Encoding utf8
    throw
}
