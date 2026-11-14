$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase139-preparation-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before preparation'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase139-preparation-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before preparation'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\derive_input_compare_139.py' *> 'D:\Codex\Kestrel\work\phase139-derivation.log'
if($LASTEXITCODE -ne 0){Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-derivation.log' -Tail 10;throw '139 derivation failed'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\prepare_phase_compare_139.py' *> 'D:\Codex\Kestrel\work\phase139-preparation.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preparation_actual_exit=$taskExit;actual_preparation_wait_completed=$true;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-preparation-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase139-derivation.log','D:\Codex\Kestrel\work\phase139-preparation.log' -Tail 8
exit $taskExit
