$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel';$taskWork=Join-Path $taskRoot 'work';$taskTarget='D:\Codex\Kestrel\work\perf-149'
$taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskSupervisors.Count){throw 'Actual owned/timed supervisor active; no cleanup'}
$taskRemote=Get-Content -LiteralPath (Join-Path $taskWork 'phase149-remote-save-proof.json') -Raw | ConvertFrom-Json -DateKind String
if(-not $taskRemote.complete -or -not $taskRemote.private -or -not $taskRemote.fresh_remote_text_and_source_byte_exact -or -not $taskRemote.all149_outcomes_saved_concisely){throw 'Verified short private save required'}
if(((Get-Date).ToUniversalTime()-[datetime]$taskRemote.utc).TotalSeconds -gt 300){throw 'Refresh remote bytes before cleanup'}
foreach($taskPair in @(@('phase149-actual-exits.json','cohort_actual_exit','actual_controller_wait_completed'),@('phase149-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),@('phase149-lifecycle-actual-exits.json','lifecycle_actual_exit','actual_auditor_wait_completed'),@('phase149-publication-actual-exits.json','publication_actual_exit','actual_publisher_wait_completed'))){
    $taskExit=Get-Content -LiteralPath (Join-Path $taskWork $taskPair[0]) -Raw | ConvertFrom-Json
    if($taskExit.($taskPair[1]) -ne 0 -or -not $taskExit.($taskPair[2])){throw 'Actual completed wait/exit required'}
}
& (Join-Path $taskWork 'guard_cleanup_20261010.ps1') -Phase final *> (Join-Path $taskWork 'phase149-storage-guard.log')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before cleanup'}
& (Join-Path $taskWork 'check_global_build_activity.ps1')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Visible global build held cleanup'}
if([IO.Path]::GetFullPath($taskTarget) -ne $taskTarget -or -not $taskTarget.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Bad exact absolute scope'}
if((Resolve-Path -LiteralPath $taskTarget).Path -ne $taskTarget){throw 'Redirected target'}
$taskItem=Get-Item -LiteralPath $taskTarget -Force;$taskParent=$taskItem
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
if(-not $taskCompletion.complete -or $taskCompletion.cases -ne 216 -or -not $taskAudit.complete -or -not $taskAudit.correctness_passed -or $taskAudit.full_payload_rows -ne 7077888 -or $taskAudit.fully_checked_crc_bytes -ne 169869312 -or @($taskAudit.case_checks).Count -ne 216 -or @($taskAudit.summaries).Count -ne 144){throw 'Full independent outcomes incomplete'}
$taskLife=Get-Content -LiteralPath (Join-Path $taskTarget 'lifecycle-receipt-audit.json') -Raw | ConvertFrom-Json
if(-not $taskLife.complete -or $taskLife.original_receipts_checked -ne 2304 -or -not $taskLife.all_probe_intervals_outside_every_native_lifetime){throw 'Original monitoring/receipt audit incomplete'}
$taskPublication=Get-Content -LiteralPath (Join-Path $taskWork 'phase149-publication-proof.json') -Raw | ConvertFrom-Json
if($taskPublication.component_qualified -or $taskPublication.release017_qualified -or -not $taskPublication.supported016_core_byte_exact){throw 'Unqualified source must remain isolated'}
if(@(Get-Content -LiteralPath (Join-Path $taskTarget 'component-cases.jsonl')).Count -ne 216){throw 'Journal incomplete'}
$taskWorkers=@(Get-Content -LiteralPath (Join-Path $taskTarget 'worker-exits.jsonl') | ForEach-Object {ConvertFrom-Json -InputObject $_})
if($taskWorkers.Count -ne 2 -or @($taskWorkers | Where-Object {$_.actual_exit -ne 0 -or -not $_.actual_wait_completed -or $_.forced_owned_worker_kill}).Count){throw 'Workers not actually terminal'}
$taskPolicy=Get-Content -LiteralPath (Join-Path $taskTarget 'policy.json') -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath (Join-Path $taskWork 'compaction-kit-122\baseline.exe')).Hash.ToLowerInvariant() -ne $taskPolicy.binary_sha256.'baseline.exe' -or (Get-FileHash -LiteralPath (Join-Path $taskWork 'compaction-kit-147\candidate147.exe')).Hash.ToLowerInvariant() -ne $taskPolicy.binary_sha256.'candidate147.exe'){throw 'Useful exact binary kits not retained'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskTarget;bytes=$taskBytes;files=$taskFiles;private_head=$taskRemote.head;short_outcomes_source_verified=$true;full_raw_byte_save_not_claimed=$true;no_reparse_or_git=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskWork 'phase149-storage-preflight.json') -Encoding utf8
Remove-Item -LiteralPath $taskTarget -Recurse -Force
if(Test-Path -LiteralPath $taskTarget){throw 'Removal incomplete'}
$taskResult=@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');deleted_exact_owned_target=$taskTarget;logical_bytes_removed=$taskBytes;files_removed=$taskFiles;D_free_bytes=(Get-PSDrive D).Free;completed149_stores_closed=$true;timed_cases_removed=216;all_deletes_native_literal_absolute_no_reparse=$true;existing_private_history_untouched=$true;small_useful_kits_retained=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskWork 'phase149-storage-cleanup-proof.json') -Encoding utf8
$taskResult | ConvertTo-Json -Compress
