$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\build_extrema_144.py' *> 'D:\Codex\Kestrel\work\build-extrema144.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');actual_build_wait_completed=$true;build_actual_exit=$taskExit;controller='build_extrema_144.py';timed_cases_declared=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-extrema144.log' -Tail 7
exit $taskExit
