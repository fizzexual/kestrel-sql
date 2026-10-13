$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel';$taskWork=Join-Path $taskRoot 'work';$taskTarget='D:\Codex\Kestrel\work\perf-150'
$taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskSupervisors.Count){throw 'Actual task/timed supervisor active'}
$taskRemote=Get-Content -LiteralPath (Join-Path $taskWork 'contiguous150-remote-save-proof.json') -Raw | ConvertFrom-Json -DateKind String
if(-not $taskRemote.complete -or -not $taskRemote.private -or -not $taskRemote.fresh_remote_text_and_source_byte_exact -or -not $taskRemote.all150_outcomes_saved_concisely){throw 'Verified private save required'}
if(((Get-Date).ToUniversalTime()-[datetime]$taskRemote.utc).TotalSeconds -gt 300){throw 'Fresh remote bytes required'}
foreach($taskPair in @(@('contiguous150-build-actual-exits.json','build_actual_exit','actual_build_controller_wait_completed'),@('contiguous150-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),@('contiguous150-wire-actual-exits.json','wire_actual_exit','actual_wire_wait_completed'),@('contiguous150-recovery-actual-exits.json','recovery_actual_exit','actual_recovery_wait_completed'),@('contiguous150-publication-actual-exits.json','publication_actual_exit','actual_publisher_wait_completed'))){
    $taskExit=Get-Content -LiteralPath (Join-Path $taskWork $taskPair[0]) -Raw | ConvertFrom-Json
    if($taskExit.($taskPair[1]) -ne 0 -or -not $taskExit.($taskPair[2])){throw 'Actual completed wait/exit required'}
}
& (Join-Path $taskWork 'guard_cleanup_20261010.ps1') -Phase final *> (Join-Path $taskWork 'contiguous150-storage-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task work held cleanup'}
& (Join-Path $taskWork 'check_global_build_activity.ps1')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build held cleanup'}
if([IO.Path]::GetFullPath($taskTarget) -ne $taskTarget -or -not $taskTarget.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Bad exact absolute scope'}
if((Resolve-Path -LiteralPath $taskTarget).Path -ne $taskTarget){throw 'Redirected root'}
$taskItem=Get-Item -LiteralPath $taskTarget -Force;$taskParent=$taskItem
while($null -ne $taskParent){if($taskParent.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected ancestor'};$taskParent=$taskParent.Parent}
$taskStack=[Collections.Generic.Stack[IO.DirectoryInfo]]::new();$taskStack.Push([IO.DirectoryInfo]$taskItem)
[long]$taskBytes=0;[long]$taskFiles=0
while($taskStack.Count){foreach($taskChild in $taskStack.Pop().EnumerateFileSystemInfos()){
    if($taskChild.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected descendant'}
    if($taskChild.Name -eq '.git'){throw 'Embedded Git'}
    if($taskChild.Attributes -band [IO.FileAttributes]::Directory){$taskStack.Push([IO.DirectoryInfo]$taskChild)}else{$taskBytes+=$taskChild.Length;$taskFiles++}
}}
$taskBuild=Get-Content -LiteralPath (Join-Path $taskTarget 'build-proof.json') -Raw | ConvertFrom-Json
$taskAudit=Get-Content -LiteralPath (Join-Path $taskTarget 'store-audit.json') -Raw | ConvertFrom-Json
$taskWire=Get-Content -LiteralPath (Join-Path $taskTarget 'legacy-wire-audit.json') -Raw | ConvertFrom-Json
$taskRecovery=Get-Content -LiteralPath (Join-Path $taskTarget 'recovery-proof.json') -Raw | ConvertFrom-Json
if(-not $taskBuild.complete -or $taskBuild.fresh_Archive_tests -ne 348 -or $taskBuild.strict_lints -ne 2 -or -not $taskAudit.all52_declared_stores_checked -or $taskAudit.independent_rows -ne 644636 -or $taskAudit.independent_CRC_bytes -ne 15471264){throw 'Fresh correctness/audit incomplete'}
if(-not $taskWire.all_six_wire_pairs_exact -or $taskWire.independent_rows -ne 393216 -or $taskWire.independent_CRC_bytes -ne 9437184){throw 'Exact format proof incomplete'}
if(-not $taskRecovery.complete -or $taskRecovery.fresh_fault_cases -ne 14 -or $taskRecovery.actual_commands -ne 56 -or $taskRecovery.full_independent_rows -ne 28672 -or $taskRecovery.full_independent_CRC_bytes -ne 688128){throw 'Full recovery/prefix accounting incomplete'}
$taskKit=Get-Content -LiteralPath (Join-Path $taskWork 'compaction-kit-150\provenance.json') -Raw | ConvertFrom-Json
foreach($taskFile in $taskKit.files){if((Get-FileHash -LiteralPath (Join-Path $taskWork ('compaction-kit-150\'+$taskFile.file))).Hash.ToLowerInvariant() -ne $taskFile.sha256){throw 'Useful exact kit not retained'}}
@{utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskTarget;bytes=$taskBytes;files=$taskFiles;private_head=$taskRemote.head;all_outcomes_failures_source_verified=$true;full_raw_byte_save_not_claimed=$true;no_reparse_or_git=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskWork 'contiguous150-storage-preflight.json') -Encoding utf8
Remove-Item -LiteralPath $taskTarget -Recurse -Force
if(Test-Path -LiteralPath $taskTarget){throw 'Removal incomplete'}
$taskResult=@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');deleted_exact_owned_target=$taskTarget;logical_bytes_removed=$taskBytes;files_removed=$taskFiles;D_free_bytes=(Get-PSDrive D).Free;completed150_stores_and_builds_closed=$true;all_deletes_native_literal_absolute_no_reparse=$true;existing_private_history_untouched=$true;useful150_candidate_and_recovery_kits_retained=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskWork 'contiguous150-storage-cleanup-proof.json') -Encoding utf8
$taskResult | ConvertTo-Json -Compress
