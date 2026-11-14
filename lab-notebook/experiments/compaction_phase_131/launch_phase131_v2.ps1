$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\build_phase_131_v2.py' *> 'D:\Codex\Kestrel\work\build-phase131-v2.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');actual_build_wait_completed=$true;build_actual_exit=$taskExit;controller='build_phase_131_v2.py';first_launcher_exit=1;first_launcher_started_Cargo_jobs=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase131-v2-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-phase131-v2.log' -Tail 7
exit $taskExit
