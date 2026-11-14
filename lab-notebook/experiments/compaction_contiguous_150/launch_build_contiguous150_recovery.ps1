$ErrorActionPreference='Stop'
$taskLive=& 'D:\Codex\Kestrel\work\inspect_current_kestrel_jobs.ps1' | ConvertFrom-Json -DateKind String
if(@($taskLive.relevant_processes | Where-Object {$_.timed -or $_.deployment -or $_.reset}).Count){throw 'Actual timed/reset work blocks recovery artifacts'}
& 'D:\Codex\Kestrel\work\build_contiguous150_recovery.ps1'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');recovery_artifact_build_actual_exit=$taskExit;actual_recovery_build_wait_completed=$true;fresh_passed_suites_repeated=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\contiguous150-recovery-build-actual-exits.json' -Encoding utf8
if(-not $? -or $taskExit -ne 0){throw 'Recovery artifact build did not complete'}
