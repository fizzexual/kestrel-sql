$ErrorActionPreference='Stop'
$taskLive=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskLive.Count){throw 'Other task/timed supervisor active'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> 'D:\Codex\Kestrel\work\buffer136-preparation-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Preparation guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build active'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\declare_prepare_buffer_136.py' *> 'D:\Codex\Kestrel\work\declare-prepare-buffer136.log'
$taskExit=$LASTEXITCODE
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\declare-prepare-buffer136.log' -Tail 10
exit $taskExit
