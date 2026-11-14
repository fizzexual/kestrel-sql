$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase146-preparation-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before146 preparation'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase146-preparation-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before146 preparation'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\derive_extrema_compare_146.py' *> 'D:\Codex\Kestrel\work\phase146-derivation.log'
if($LASTEXITCODE -ne 0){Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase146-derivation.log' -Tail 10;throw 'Derivation failed; preserve partial source'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\prepare_phase_compare_146.py' *> 'D:\Codex\Kestrel\work\phase146-preparation.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');preparation_actual_exit=$taskExit;actual_preparation_wait_completed=$true;timed_cases_started=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase146-preparation-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase146-derivation.log','D:\Codex\Kestrel\work\phase146-preparation.log' -Tail 5
exit $taskExit
