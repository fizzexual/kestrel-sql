$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel'
$taskTarget='D:\Codex\Kestrel\work\perf-142'
$taskProof=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-remote-save-proof.json' -Raw | ConvertFrom-Json -DateKind String
$taskExit=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-publication-actual-exits.json' -Raw | ConvertFrom-Json
if(-not $taskProof.complete -or -not $taskProof.private -or -not $taskProof.fresh_remote_text_and_source_byte_exact -or -not $taskProof.all142_failures_outcomes_saved_concisely -or $taskExit.publication_actual_exit -ne 0 -or -not $taskExit.actual_publisher_wait_completed){throw 'Fresh private save/wait incomplete'}
if(((Get-Date).ToUniversalTime()-[DateTime]::Parse($taskProof.utc).ToUniversalTime()).TotalMinutes -gt 15){throw 'Refresh exact remote verification'}
$taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskSupervisors.Count){throw 'Other task/timed supervisor active'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase final *> 'D:\Codex\Kestrel\work\profile142-final-storage-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task cleanup guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held before cleanup'}
if([IO.Path]::GetFullPath($taskTarget) -ne $taskTarget -or -not $taskTarget.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Bad absolute scope'}
$taskItem=Get-Item -LiteralPath $taskTarget -Force
if((Resolve-Path -LiteralPath $taskTarget).Path -ne $taskTarget){throw 'Redirected root'}
$taskParent=$taskItem
while($null -ne $taskParent){if($taskParent.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected ancestor'};$taskParent=$taskParent.Parent}
$taskStack=[Collections.Generic.Stack[IO.DirectoryInfo]]::new();$taskStack.Push([IO.DirectoryInfo]$taskItem)
[long]$taskBytes=0;[long]$taskFiles=0
while($taskStack.Count){foreach($taskChild in $taskStack.Pop().EnumerateFileSystemInfos()){
    if($taskChild.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected descendant'}
    if($taskChild.Name -eq '.git'){throw 'Embedded Git'}
    if($taskChild.Attributes -band [IO.FileAttributes]::Directory){$taskStack.Push([IO.DirectoryInfo]$taskChild)}else{$taskBytes+=$taskChild.Length;$taskFiles++}
}}
if(Test-Path -LiteralPath (Join-Path $taskTarget 'component-cases.jsonl')){throw 'Unexpected timing journal'}
$taskAudit=Get-Content -LiteralPath (Join-Path $taskTarget 'closure-audit.json') -Raw | ConvertFrom-Json
if(-not $taskAudit.complete -or $taskAudit.timed_cases -ne 0 -or @($taskAudit.all216timed_indices_unstarted).Count -ne 216 -or $taskAudit.rows -ne 163840 -or $taskAudit.CRC_bytes -ne 3932160 -or -not $taskAudit.extreme_output_failed_exit101){throw 'Failure/prefix closure incomplete'}
$taskWorkers=@(Get-Content -LiteralPath (Join-Path $taskTarget 'worker-exits.jsonl') | ForEach-Object {ConvertFrom-Json -InputObject $_})
if($taskWorkers.Count -ne 2 -or @($taskWorkers | Where-Object {$_.actual_exit -ne 0 -or -not $_.actual_wait_completed -or $_.forced_owned_worker_kill}).Count){throw 'Worker termination incomplete'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskTarget;bytes=$taskBytes;files=$taskFiles;private_head=$taskProof.head;native_literal_absolute_no_reparse=$true;raw_byte_backup_not_claimed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-storage-preflight.json' -Encoding utf8
Remove-Item -LiteralPath $taskTarget -Recurse -Force
if(Test-Path -LiteralPath $taskTarget){throw 'Removal incomplete'}
@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');deleted_exact_owned_target=$taskTarget;logical_bytes_removed=$taskBytes;files_removed=$taskFiles;D_free_bytes=(Get-PSDrive D).Free;existing_private_history_untouched=$true;all_deletes_native_literal_absolute_no_reparse=$true;failed_diagnostic_sources_retained=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-storage-cleanup-proof.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\profile142-storage-cleanup-proof.json'
