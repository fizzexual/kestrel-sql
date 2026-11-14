$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\phase148-preflight-actual-exits.json'){throw 'Do not repeat existing preflight'}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\wait_quiet_preflight148_v2.py' *> 'D:\Codex\Kestrel\work\phase148-preflight-quiet-v2.log'
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');actual_exit=$taskExit;actual_quiet_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-preflight-quiet-v2-actual-exits.json' -Encoding utf8
if($taskExit -ne 0){Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase148-preflight-quiet-v2.log' -Tail 8;exit $taskExit}
& 'D:\Codex\Kestrel\work\launch_preflight_phase148.ps1'
exit $LASTEXITCODE
