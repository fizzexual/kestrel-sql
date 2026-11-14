$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel'
$taskTarget='D:\Codex\Kestrel\work\perf-141'
$taskProof=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-remote-save-proof.json' -Raw | ConvertFrom-Json -DateKind String
if(-not $taskProof.complete -or -not $taskProof.private -or -not $taskProof.fresh_remote_text_and_source_byte_exact -or -not $taskProof.all141_outcomes_saved_concisely){throw 'Private save not freshly verified'}
foreach($taskPair in @(@('phase141-actual-exits.json','cohort_actual_exit','actual_controller_wait_completed'),@('phase141-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),@('phase141-lifecycle-actual-exits.json','lifecycle_actual_exit','actual_auditor_wait_completed'),@('phase141-publication-v4-actual-exits.json','publication_actual_exit','actual_publisher_wait_completed'))){
    $taskExit=Get-Content -LiteralPath (Join-Path $taskRoot ('work\'+$taskPair[0])) -Raw | ConvertFrom-Json
    if($taskExit.($taskPair[1]) -ne 0 -or -not $taskExit.($taskPair[2])){throw 'Actual owned wait/exit incomplete'}
}
$taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskSupervisors.Count){throw 'Other task/timed supervisor active'}
& 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase final *> 'D:\Codex\Kestrel\work\phase141-final-storage-guard.log'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task/activity cleanup guard held'}
& 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Visible global build active'}
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
$taskCompletion=Get-Content -LiteralPath (Join-Path $taskTarget 'cohort-completion.json') -Raw | ConvertFrom-Json
if(-not $taskCompletion.complete -or $taskCompletion.cases -ne 216 -or -not $taskAudit.complete -or -not $taskAudit.correctness_passed -or $taskAudit.full_payload_rows -ne 7077888 -or $taskAudit.fully_checked_crc_bytes -ne 169869312 -or @($taskAudit.case_checks).Count -ne 216 -or @($taskAudit.identity_failed).Count -ne 20 -or @($taskAudit.guards_failed).Count -ne 15 -or $taskAudit.clustered_goals_qualified){throw 'Full cohort outcomes not accounted'}
if(@(Get-Content -LiteralPath (Join-Path $taskTarget 'component-cases.jsonl')).Count -ne 216){throw 'Journal incomplete'}
$taskLife=Get-Content -LiteralPath (Join-Path $taskTarget 'lifecycle-receipt-audit.json') -Raw | ConvertFrom-Json
if(-not $taskLife.complete -or $taskLife.original_receipts_checked -ne 2304 -or $taskLife.actual_probes -ne 457 -or $taskLife.between_case_pauses -ne 0 -or -not $taskLife.all_probe_intervals_outside_every_native_lifetime){throw 'Additional proofs incomplete'}
if(((Get-Date).ToUniversalTime()-[DateTime]::Parse($taskProof.utc).ToUniversalTime()).TotalMinutes -gt 15){throw 'Refresh remote verification first'}
$taskWorkers=@(Get-Content -LiteralPath (Join-Path $taskTarget 'worker-exits.jsonl') | ForEach-Object {ConvertFrom-Json -InputObject $_})
if($taskWorkers.Count -ne 2 -or @($taskWorkers | Where-Object {$_.actual_exit -ne 0 -or -not $_.actual_wait_completed -or $_.forced_owned_worker_kill}).Count){throw 'Worker termination incomplete'}
$taskPolicy=Get-Content -LiteralPath (Join-Path $taskTarget 'policy.json') -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath 'D:\Codex\Kestrel\work\compaction-kit-131\candidate131.exe').Hash.ToLowerInvariant() -ne $taskPolicy.binary_sha256.'baseline.exe' -or (Get-FileHash -LiteralPath 'D:\Codex\Kestrel\work\compaction-kit-140\candidate140.exe').Hash.ToLowerInvariant() -ne $taskPolicy.binary_sha256.'candidate140.exe'){throw 'Useful exact binary kits not retained'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskTarget;bytes=$taskBytes;files=$taskFiles;private_head=$taskProof.head;all_outcomes_failures_source_freshly_verified=$true;full_raw_byte_save_not_claimed=$true;native_literal_no_reparse=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-storage-preflight.json' -Encoding utf8
Remove-Item -LiteralPath $taskTarget -Recurse -Force
if(Test-Path -LiteralPath $taskTarget){throw 'Removal incomplete'}
$taskResult=@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');deleted_exact_owned_target=$taskTarget;logical_bytes_removed=$taskBytes;files_removed=$taskFiles;D_free_bytes=(Get-PSDrive D).Free;completed141_stores_closed=$true;timed_cases_removed=216;all_deletes_native_literal_absolute_no_reparse=$true;existing_private_history_untouched=$true;small_baseline_131_and140_kits_retained=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\phase141-storage-cleanup-proof.json' -Encoding utf8
$taskResult | ConvertTo-Json -Compress
