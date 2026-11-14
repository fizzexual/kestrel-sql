$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\coalesce140-preparation-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before preparation'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\coalesce140-preparation-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before preparation'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\declare_prepare_coalesce_140.py' *> 'D:\Codex\Kestrel\work\declare-prepare-coalesce140.log'
$taskExit=$LASTEXITCODE
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\declare-prepare-coalesce140.log' -Tail 12
exit $taskExit
