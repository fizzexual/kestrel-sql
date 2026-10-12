$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
$taskStarted=(Get-Date).ToUniversalTime()
$taskDeadline=$taskStarted.AddHours(2)
$taskAttempts=0
$taskPolls=0
$taskProofPath=Join-Path $taskRoot 'phase145-preflight-wait-actual-exits.json'
if(Test-Path -LiteralPath $taskProofPath){throw 'Do not overwrite actual waiter exit'}
if(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-preflight-actual-exits.json')){throw 'Preflight already attempted; inspect its prefix'}
if(Test-Path -LiteralPath (Join-Path $taskRoot 'perf-145\smoke-fixtures')){throw 'Preflight fixture already exists'}
$taskStartedProof=Join-Path $taskRoot 'phase145-preflight-wait-started.json'
if(Test-Path -LiteralPath $taskStartedProof){throw 'Existing waiter identity; inspect rather than duplicate'}
$taskSelf=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
@{utc=$taskStarted.ToString('o');waiter_pid=$PID;waiter_creation_utc=$taskSelf.CreationDate.ToUniversalTime().ToString('o');waiter_creation_filetime=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToFileTimeUtc();source=$PSCommandPath;metadata_only_until_excluded_preflight=$true;no_duplicate_automation=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskStartedProof -Encoding utf8
try {
    while((Get-Date).ToUniversalTime() -lt $taskDeadline){
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
        @{utc=(Get-Date).ToUniversalTime().ToString('o');poll=$taskPolls;clear=$taskClear;other_work=@($taskJobs | ForEach-Object {@{pid=$_.ProcessId;name=$_.Name;creation_utc=$_.CreationDate.ToUniversalTime().ToString('o')}});metadata_only=$true;no_native_case_started_by_poll=$true} | ConvertTo-Json -Depth 5 -Compress | Add-Content -LiteralPath (Join-Path $taskRoot 'phase145-preflight-wait-metadata.jsonl') -Encoding utf8
        if($taskClear){
            $taskAttempts++
            & 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File 'D:\Codex\Kestrel\work\launch_preflight_phase145.ps1'
            $taskChildExit=$LASTEXITCODE
            # No metadata probes while the excluded native preflight runs.
            if(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-preflight-actual-exits.json')){
                $taskPreflight=Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-preflight-actual-exits.json') -Raw | ConvertFrom-Json
                if(-not $taskPreflight.actual_preflight_wait_completed -or $taskPreflight.preflight_actual_exit -ne $taskChildExit){throw 'Actual preflight wait/exit mismatch'}
                @{utc=(Get-Date).ToUniversalTime().ToString('o');waiter_actual_exit=$taskChildExit;actual_wait_completed=$true;preflight_attempts=$taskAttempts;metadata_polls=$taskPolls;qualification_cases_started=0;no_passed_native_case_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskProofPath -Encoding utf8
                exit $taskChildExit
            }
            if(Test-Path -LiteralPath (Join-Path $taskRoot 'perf-145\smoke-fixtures')){throw 'Native prefix exists without actual exit; retain and inspect'}
            if($taskChildExit -eq 0){throw 'Launcher zero without actual preflight proof'}
            # A guard can race a new build before Python creation; only recheck safety.
        }
        Start-Sleep -Seconds 10
    }
    throw 'Metadata wait deadline; no qualified timing started'
} catch {
    @{utc=(Get-Date).ToUniversalTime().ToString('o');waiter_actual_exit=1;actual_wait_completed=$true;preflight_launcher_attempts=$taskAttempts;metadata_polls=$taskPolls;bounded_error=$_.Exception.Message;qualification_cases_started=0;no_case_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskProofPath -Encoding utf8
    throw
}
