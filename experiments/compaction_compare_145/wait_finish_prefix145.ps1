$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
$taskClock=[Diagnostics.Stopwatch]::StartNew()
$taskQuietSince=$null
$taskStarted=(Get-Date).ToUniversalTime()
$taskActualPath=Join-Path $taskRoot 'phase145-finish-wait-actual-exits.json'
$taskStartedPath=Join-Path $taskRoot 'phase145-finish-wait-started.json'
if((Test-Path -LiteralPath $taskActualPath) -or (Test-Path -LiteralPath $taskStartedPath)){throw 'Existing finish job; do not duplicate'}
$taskSelf=Get-CimInstance Win32_Process -Filter ('ProcessId='+$PID)
@{utc=$taskStarted.ToString('o');pid=$PID;creation_utc=$taskSelf.CreationDate.ToUniversalTime().ToString('o');metadata_only_until_quiet=$true;no_duplicate_automation=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskStartedPath -Encoding utf8
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$taskPolls=0
$taskAttempts=0
try {
    while($taskClock.Elapsed.TotalSeconds -lt 7200){
        $taskBegin=(Get-Date).ToUniversalTime()
        $taskReset=Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json -DateKind String
        if($taskReset.phase -ne 'wait-expired-no-source-mutated' -or $taskReset.utc -ne '2026-10-09T10:33:06.6265823Z'){throw 'Reset changed; no action'}
        if([string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008').State -ne 'Ready' -or [string](Get-ScheduledTask -TaskName 'Codex-Kestrel-Migrate-20261007').State -ne 'Disabled'){throw 'Task state changed'}
        $taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
        $taskJobs=@(@(Get-OtherWork)+$taskSupervisors | Sort-Object ProcessId -Unique | Select-Object @{n='pid';e={$_.ProcessId}},Name,@{n='creation_utc';e={$_.CreationDate.ToUniversalTime().ToString('o')}})
        $taskGlobalRaw=& (Join-Path $taskRoot 'check_global_build_activity.ps1')
        $taskGlobal=$taskGlobalRaw | ConvertFrom-Json -DateKind String
        $taskClear=($taskJobs.Count -eq 0 -and $taskGlobal.no_visible_build_jobs)
        $taskPolls++
        @{started_utc=$taskBegin.ToString('o');utc=(Get-Date).ToUniversalTime().ToString('o');clear=$taskClear;poll=$taskPolls;other_jobs=$taskJobs;global_builds=$taskGlobal.visible_build_jobs;no_hash_git_copy_build_cleanup=$true} | ConvertTo-Json -Depth 6 -Compress | Add-Content -LiteralPath (Join-Path $taskRoot 'phase145-finish-wait-metadata.jsonl') -Encoding utf8
        if($taskClear){
            if($null -eq $taskQuietSince){$taskQuietSince=$taskClock.Elapsed.TotalSeconds}
            if($taskClock.Elapsed.TotalSeconds-$taskQuietSince -ge 120){
                $taskAttempts++
                & 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File (Join-Path $taskRoot 'launch_publish_prefix145_v2.ps1')
                if($LASTEXITCODE -ne 0){throw 'Publication held/failed; preserve partial state and do not repeat'}
                & 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File (Join-Path $taskRoot 'close_prefix145_storage.ps1')
                if($LASTEXITCODE -ne 0){throw 'Cleanup held/failed; keep completed fixtures and refresh remote proof before continuation'}
                & 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'append_prefix145_closed.py')
                if($LASTEXITCODE -ne 0){throw 'Closed checkpoint append failed; inspect exact old prefix before continuation'}
                @{utc=(Get-Date).ToUniversalTime().ToString('o');actual_exit=0;actual_wait_completed=$true;publication_attempts=$taskAttempts;metadata_polls=$taskPolls;completed145_closure=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskActualPath -Encoding utf8
                exit 0
            }
        }else{$taskQuietSince=$null}
        Start-Sleep -Seconds 10
    }
    throw 'Metadata-only finish wait expired; no repeat or unrelated process change'
} catch {
    @{utc=(Get-Date).ToUniversalTime().ToString('o');actual_exit=1;actual_wait_completed=$true;publication_attempts=$taskAttempts;metadata_polls=$taskPolls;bounded_error=$_.Exception.Message;no_repeated_native_case=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskActualPath -Encoding utf8
    throw
}
