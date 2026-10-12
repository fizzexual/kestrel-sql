$ErrorActionPreference='Stop'
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\build_index_profile_142.py' *> 'D:\Codex\Kestrel\work\build-profile142.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');build_actual_exit=$taskExit;actual_build_wait_completed=$true;kernel_only=$true;new_engine_tests=0} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-build-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\build-profile142.log' -Tail 8
exit $taskExit
