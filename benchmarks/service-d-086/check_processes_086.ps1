param([ValidateSet('pre-smoke','pre-timing','post-timing')][string]$Phase)
$ErrorActionPreference='Stop'
$taskWork='D:\Codex\Kestrel\work\perf-086'
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$taskOther=@(Get-OtherWork)
$taskStream=[IO.File]::Open('D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json',[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
$taskReader=[IO.StreamReader]::new($taskStream)
try{$taskReset=$taskReader.ReadToEnd() | ConvertFrom-Json}finally{$taskReader.Dispose()}
if($taskReset.phase -ne 'waiting-for-full-codex-exit'){throw 'Reset is no longer waiting; keep service timings stopped'}
Assert-Real 'D:\Codex\Kestrel';Assert-Real 'D:\Codex\Kestrel\work';Assert-Real $taskWork
$taskProof=@{checked_utc=(Get-Date).ToUniversalTime().ToString('o');active_processes=@($taskOther | Select-Object ProcessId,Name,ExecutablePath);reset_phase=$taskReset.phase;free_bytes=(Get-PSDrive D).Free;physical_workspace=$taskWork}
$taskProof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskWork ($Phase+'-process-check.json')) -Encoding utf8
if($taskOther.Count -ne 0){throw 'Other task work active; keep service timings stopped'}
$taskProof | ConvertTo-Json -Depth 6 -Compress
