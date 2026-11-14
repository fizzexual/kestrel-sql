$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel'
$taskTarget='D:\Codex\Kestrel\work\perf-143'
$taskProof=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\profile143-remote-save-proof.json' -Raw | ConvertFrom-Json -DateKind String
if(-not $taskProof.complete -or -not $taskProof.private -or -not $taskProof.fresh_remote_text_and_source_byte_exact -or -not $taskProof.all143_outcomes_failures_saved_concisely){throw 'Fresh private save incomplete'}
foreach($taskPair in @(@('profile143-actual-exits.json','cohort_actual_exit','actual_controller_wait_completed'),@('profile143-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),@('profile143-lifecycle-actual-exits.json','lifecycle_actual_exit','actual_auditor_wait_completed'),@('profile143-publication-actual-exits.json','publication_actual_exit','actual_publisher_wait_completed'))){
    $taskExit=Get-Content -LiteralPath (Join-Path $taskRoot ('work\'+$taskPair[0])) -Raw | ConvertFrom-Json
    if($taskExit.($taskPair[1]) -ne 0 -or -not $taskExit.($taskPair[2])){throw 'Actual owned wait/exit incomplete'}
}
if(((Get-Date).ToUniversalTime()-[DateTime]::Parse($taskProof.utc).ToUniversalTime()).TotalMinutes -gt 15){throw 'Refresh exact remote verification'}
$taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskSupervisors.Count){throw 'Other task/timed supervisor active'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase final *> 'D:\Codex\Kestrel\work\profile143-final-storage-guard.log'
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
$taskAudit=Get-Content -LiteralPath (Join-Path $taskTarget 'audit.json') -Raw | ConvertFrom-Json
$taskLife=Get-Content -LiteralPath (Join-Path $taskTarget 'lifecycle-audit.json') -Raw | ConvertFrom-Json
if(-not $taskAudit.complete -or -not $taskAudit.correctness_passed -or $taskAudit.cases -ne 216 -or $taskAudit.rows -ne 7077888 -or $taskAudit.CRC_bytes -ne 169869312 -or $taskAudit.failed_AA -ne 1 -or $taskAudit.failed_guards -ne 1 -or $taskAudit.failed_goals -ne 1){throw 'Full outcome incomplete'}
if(@(Get-Content -LiteralPath (Join-Path $taskTarget 'component-cases.jsonl')).Count -ne 216 -or -not $taskLife.complete -or $taskLife.actual_probes -ne 715 -or $taskLife.probe_native_pairs_checked -ne 154440 -or $taskLife.pauses -ne 7){throw 'Complete journal/lifecycle missing'}
$taskWorkers=@(Get-Content -LiteralPath (Join-Path $taskTarget 'worker-exits.jsonl') | ForEach-Object {ConvertFrom-Json -InputObject $_})
if($taskWorkers.Count -ne 2 -or @($taskWorkers | Where-Object {$_.actual_exit -ne 0 -or -not $_.actual_wait_completed -or $_.forced_owned_worker_kill}).Count){throw 'Worker termination incomplete'}
$taskKit=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\index-kit-143\provenance.json' -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath 'D:\Codex\Kestrel\work\index-kit-143\index_profile143.exe').Hash.ToLowerInvariant() -ne $taskKit.binary_sha256){throw 'Useful kit not retained exactly'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskTarget;bytes=$taskBytes;files=$taskFiles;private_head=$taskProof.head;native_literal_absolute_no_reparse=$true;raw_byte_backup_not_claimed=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\profile143-storage-preflight.json' -Encoding utf8
Remove-Item -LiteralPath $taskTarget -Recurse -Force
if(Test-Path -LiteralPath $taskTarget){throw 'Removal incomplete'}
@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');deleted_exact_owned_target=$taskTarget;logical_bytes_removed=$taskBytes;files_removed=$taskFiles;D_free_bytes=(Get-PSDrive D).Free;existing_private_history_untouched=$true;all_deletes_native_literal_absolute_no_reparse=$true;useful_index_kit143_retained=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\profile143-storage-cleanup-proof.json' -Encoding utf8
Get-Content -LiteralPath 'D:\Codex\Kestrel\work\profile143-storage-cleanup-proof.json'
