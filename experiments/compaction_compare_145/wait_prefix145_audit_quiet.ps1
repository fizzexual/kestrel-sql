$ErrorActionPreference='Stop'
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$taskClock=[Diagnostics.Stopwatch]::StartNew()
$taskQuietSince=$null
$taskResets=0
$taskObservations=[Collections.Generic.List[object]]::new()
while($taskClock.Elapsed.TotalSeconds -lt 7200){
    $taskReset=Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json -DateKind String
    if($taskReset.phase -ne 'wait-expired-no-source-mutated' -or $taskReset.utc -ne '2026-10-09T10:33:06.6265823Z'){throw 'Reset changed'}
    if([string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008').State -ne 'Ready' -or [string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Migrate-20261007').State -ne 'Disabled'){throw 'Task state changed'}
    $taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
    $taskOther=@(@(Get-OtherWork)+$taskSupervisors | Sort-Object ProcessId -Unique | Select-Object @{n='pid';e={$_.ProcessId}},Name,@{n='creation_utc';e={$_.CreationDate.ToUniversalTime().ToString('o')}})
    $taskGlobalRaw=& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
    $taskGlobal=$taskGlobalRaw | ConvertFrom-Json -DateKind String
    $taskReportFile=Get-Item -LiteralPath 'D:\Codex\Kestrel\work\deployment-final-8h-20261012.json'
    $taskReport=Get-Content -LiteralPath $taskReportFile.FullName -Raw | ConvertFrom-Json -DateKind String
    $taskSettled=($taskReport.state -eq 'finished' -and $null -eq $taskReport.active_host_pid -and ((Get-Date).ToUniversalTime()-$taskReportFile.LastWriteTimeUtc).TotalSeconds -gt 30)
    $taskClear=($taskOther.Count -eq 0 -and $taskGlobal.no_visible_build_jobs -and $taskSettled)
    $taskObservation=@{utc=(Get-Date).ToUniversalTime().ToString('o');clear=$taskClear;other_jobs=$taskOther;global_builds=$taskGlobal.visible_build_jobs;sprout_terminal_settled=$taskSettled;sprout_passed=$taskReport.passed;no_hash_git_copy_build_or_cleanup=$true}
    $taskObservations.Add($taskObservation)
    $taskObservation | ConvertTo-Json -Depth 5 -Compress | Add-Content -LiteralPath 'D:\Codex\Kestrel\work\phase145-prefix-audit-quiet-observations.jsonl' -Encoding utf8
    if($taskClear){
        if($null -eq $taskQuietSince){$taskQuietSince=$taskClock.Elapsed.TotalSeconds}
        if($taskClock.Elapsed.TotalSeconds-$taskQuietSince -ge 120){
            $taskProof=@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');continuous_observed_clear_seconds=($taskClock.Elapsed.TotalSeconds-$taskQuietSince);busy_reset_count=$taskResets;observations=$taskObservations.Count;no_other_job_or_setting_changed=$true;terminal_sprout_passed=$taskReport.passed;snapshot_limits='Ten-second observations cannot exclude every brief unobserved process';no_hash_during_wait=$true}
            if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\phase145-prefix-audit-quiet-proof.json'){throw 'Do not overwrite quiet proof'}
            $taskProof | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase145-prefix-audit-quiet-proof.json' -Encoding utf8
            $taskProof | ConvertTo-Json -Compress
            exit 0
        }
    }else{$taskQuietSince=$null;$taskResets++}
    Start-Sleep -Seconds 10
}
throw 'Quiet deadline expired; no audit/publication/cleanup started'
