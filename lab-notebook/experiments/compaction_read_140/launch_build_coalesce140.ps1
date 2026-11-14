$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\build_coalesce_140.py' *> 'D:\Codex\Kestrel\work\build-coalesce140.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');actual_build_wait_completed=$true;build_actual_exit=$taskExit;controller='build_coalesce_140.py';timed_cases_declared=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\coalesce140-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-coalesce140.log' -Tail 7
exit $taskExit
