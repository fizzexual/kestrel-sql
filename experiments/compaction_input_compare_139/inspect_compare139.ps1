$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase prepreserve *> 'D:\Codex\Kestrel\work\phase139-prepublication-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity guard held before analysis'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> 'D:\Codex\Kestrel\work\phase139-prepublication-global.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before analysis'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\analyze_compare139.py'
exit $LASTEXITCODE
