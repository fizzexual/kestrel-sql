$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel';$taskTarget='D:\Codex\Kestrel\work\perf-144'
$taskProof=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-remote-save-proof.json' -Raw | ConvertFrom-Json -DateKind String
if(-not $taskProof.complete -or -not $taskProof.private -or -not $taskProof.fresh_remote_text_and_source_byte_exact -or -not $taskProof.all144_outcomes_saved_concisely){throw 'Private save not freshly verified'}
if(((Get-Date).ToUniversalTime()-[DateTime]::Parse($taskProof.utc).ToUniversalTime()).TotalMinutes -gt 15){throw 'Refresh remote byte verification before cleanup'}
foreach($taskSpec in @(@('extrema144-continue-actual-exits.json','build_actual_exit'),@('extrema144-audit-actual-exits.json','audit_actual_exit'),@('extrema144-wire-finish-actual-exits.json','wire_actual_exit'),@('extrema144-recovery-finish-actual-exits.json','recovery_actual_exit'),@('extrema144-publication-v3-actual-exits.json','publication_actual_exit'))){
 $taskExit=Get-Content -LiteralPath ('D:\Codex\Kestrel\work\'+$taskSpec[0]) -Raw | ConvertFrom-Json
 if($taskExit.($taskSpec[1]) -ne 0){throw 'Actual exit incomplete'}
}
$taskLive=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskLive.Count){throw 'Other task/timed supervisor active'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase final *> 'D:\Codex\Kestrel\work\extrema144-final-storage-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Cleanup/reset guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Visible global build active'}
$taskBuild=Get-Content -LiteralPath ($taskTarget+'\build-proof.json') -Raw | ConvertFrom-Json
$taskAudit=Get-Content -LiteralPath ($taskTarget+'\store-audit.json') -Raw | ConvertFrom-Json
$taskWire=Get-Content -LiteralPath ($taskTarget+'\legacy-wire-audit.json') -Raw | ConvertFrom-Json
$taskRecovery=Get-Content -LiteralPath ($taskTarget+'\recovery-proof.json') -Raw | ConvertFrom-Json
if(-not $taskBuild.complete -or $taskBuild.fresh_Archive_tests -ne 344 -or $taskBuild.strict_lints -ne 2 -or -not $taskAudit.all28_stores_checked -or $taskAudit.independent_rows -ne 245952 -or -not $taskWire.all_six_wire_pairs_exact -or @($taskWire.checks).Count -ne 12 -or -not $taskRecovery.complete -or $taskRecovery.fresh_fault_cases -ne 14 -or $taskRecovery.actual_commands -ne 56){throw 'Complete outcomes and failed prefix not accounted'}
if(-not $taskRecovery.no_native_case_repeated -or $taskRecovery.full_independent_rows -ne 28672 -or $taskRecovery.full_independent_CRC_bytes -ne 688128 -or $taskAudit.independent_CRC_bytes -ne 5902848 -or $taskWire.independent_CRC_bytes -ne 9437184){throw 'Full payload/recovery coverage missing'}
$taskKit=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\compaction-kit-144\provenance.json' -Raw | ConvertFrom-Json
if($taskKit.source_private_commit -ne $taskProof.head -or (Get-FileHash -LiteralPath 'D:\Codex\Kestrel\work\compaction-kit-144\candidate144.exe' -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskBuild.candidate_sha256){throw 'Useful candidate not retained'}
foreach($taskArtifact in $taskKit.retained_recovery_artifacts){if((Get-FileHash -LiteralPath ('D:\Codex\Kestrel\work\compaction-kit-144\'+$taskArtifact.name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskArtifact.sha256){throw 'Recovery artifact not retained'}}
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
@{utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskTarget;bytes=$taskBytes;files=$taskFiles;private_head=$taskProof.head;all_outcomes_failures_source_freshly_verified=$true;full_raw_byte_save_not_claimed=$true;native_literal_no_reparse=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-storage-preflight.json' -Encoding utf8
Remove-Item -LiteralPath $taskTarget -Recurse -Force
if(Test-Path -LiteralPath $taskTarget){throw 'Removal incomplete'}
$taskResult=@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');deleted_exact_owned_target=$taskTarget;logical_bytes_removed=$taskBytes;files_removed=$taskFiles;D_free_bytes=(Get-PSDrive D).Free;completed144_stores_and_regenerable_builds_closed=$true;all_deletes_native_literal_absolute_no_reparse=$true;existing_private_history_untouched=$true;useful_candidate_and_recovery_kit_retained=$true;timed_performance_cases=0}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\extrema144-storage-cleanup-proof.json' -Encoding utf8
$taskResult | ConvertTo-Json -Compress
