$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\profile142-preparation-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity held before diagnostic preparation'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\profile142-preparation-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held before diagnostic preparation'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\prepare_index_profile_142.py' *> 'D:\Codex\Kestrel\work\profile142-preparation.log'
$taskExit=$LASTEXITCODE
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-preparation.log' -Tail 10
exit $taskExit
