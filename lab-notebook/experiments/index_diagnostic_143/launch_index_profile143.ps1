$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\append_profile143_running.py' *> 'D:\Codex\Kestrel\work\append-profile143-declared.log'
if($LASTEXITCODE -ne 0){throw 'Checkpoint failed before timing'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase pretime *> 'D:\Codex\Kestrel\work\profile143-pretime-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Task/reset pretime guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\profile143-pretime-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build before timing'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\run_index_profile_143.py' *> 'D:\Codex\Kestrel\work\run-index-profile-143.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');cohort_actual_exit=$taskExit;actual_controller_wait_completed=$true;controller='run_index_profile_143.py'} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\profile143-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\run-index-profile-143.log' -Tail 6
exit $taskExit
