$ErrorActionPreference='Stop'
$taskLive=& 'D:\Codex\Kestrel\work\inspect_current_kestrel_jobs.ps1' | ConvertFrom-Json -DateKind String
if(@($taskLive.relevant_processes | Where-Object {$_.timed -or $_.deployment -or $_.reset}).Count){throw 'Timed/reset work holds150 source preparation'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\contiguous150-source-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Task/reset held150 source preparation'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\contiguous150-source-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held150 preparation'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\declare_prepare_contiguous_150.py' *> 'D:\Codex\Kestrel\work\contiguous150-source-preparation.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preparation_actual_exit=$taskExit;actual_preparation_wait_completed=$true;builds_started=0;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\contiguous150-source-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\contiguous150-source-preparation.log' -Tail 8
exit $taskExit
