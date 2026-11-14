$ErrorActionPreference='Stop'
$taskLive=& 'D:\Codex\Kestrel\work\inspect_current_kestrel_jobs.ps1' | ConvertFrom-Json -DateKind String
if(@($taskLive.relevant_processes | Where-Object {$_.timed -or $_.deployment -or $_.reset}).Count){throw 'Actual timed/reset job blocks149 preparation'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase149-preparation-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before149 preparation'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase149-preparation-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before149 preparation'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\derive_payload_compare_149.py' *> 'D:\Codex\Kestrel\work\phase149-derivation.log'
if($LASTEXITCODE -ne 0){Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase149-derivation.log' -Tail 10;throw 'Derivation failed; preserve partial source'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\prepare_phase_compare_149.py' *> 'D:\Codex\Kestrel\work\phase149-preparation.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preparation_actual_exit=$taskExit;actual_preparation_wait_completed=$true;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase149-preparation-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase149-derivation.log','D:\Codex\Kestrel\work\phase149-preparation.log' -Tail 4
exit $taskExit
