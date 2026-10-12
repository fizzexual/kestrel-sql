$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel'
$taskWork=Join-Path $taskRoot 'work'
$taskTarget='D:\Codex\Kestrel\work\perf-145'
$taskOther=& (Join-Path $taskWork 'inspect_current_kestrel_jobs.ps1') | ConvertFrom-Json -DateKind String
if(@($taskOther.relevant_processes | Where-Object {$_.timed -or $_.deployment -or $_.reset}).Count){throw 'Timed/reset work active; no cleanup'}
$taskSupervisors=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
if($taskSupervisors.Count){throw 'Other actual supervisor active; no cleanup'}
$taskRemote=Get-Content -LiteralPath (Join-Path $taskWork 'phase145-remote-save-proof.json') -Raw | ConvertFrom-Json -DateKind String
if(-not $taskRemote.complete -or -not $taskRemote.private -or -not $taskRemote.fresh_remote_text_and_source_byte_exact -or -not $taskRemote.all145_outcomes_saved_concisely){throw 'Private concise save required'}
if(((Get-Date).ToUniversalTime()-[datetime]$taskRemote.utc).TotalSeconds -gt 300){throw 'Remote proof stale; freshly verify before cleanup'}
$taskPublication=Get-Content -LiteralPath (Join-Path $taskWork 'phase145-publication-actual-exits.json') -Raw | ConvertFrom-Json
if($taskPublication.publication_actual_exit -ne 0 -or -not $taskPublication.actual_publisher_wait_completed){throw 'Actual publisher exit incomplete'}
$taskActual=Get-Content -LiteralPath (Join-Path $taskWork 'phase145-actual-exits.json') -Raw | ConvertFrom-Json
if($taskActual.cohort_actual_exit -ne 1 -or -not $taskActual.actual_controller_wait_completed){throw 'Expected rejected cohort exit missing'}
& (Join-Path $taskWork 'guard_cleanup_20261010.ps1') -Phase final
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Reset/task guard held before cleanup'}
& (Join-Path $taskWork 'check_global_build_activity.ps1')
if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build guard held before cleanup'}
if([IO.Path]::GetFullPath($taskTarget) -ne $taskTarget -or -not $taskTarget.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Invalid exact scope'}
if((Resolve-Path -LiteralPath $taskTarget).Path -ne $taskTarget){throw 'Redirected target'}
$taskItem=Get-Item -LiteralPath $taskTarget -Force
$taskParent=$taskItem
while($null -ne $taskParent){if($taskParent.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected ancestor'};$taskParent=$taskParent.Parent}
$taskStack=[Collections.Generic.Stack[IO.DirectoryInfo]]::new();$taskStack.Push([IO.DirectoryInfo]$taskItem)
[long]$taskBytes=0;[long]$taskFiles=0
while($taskStack.Count){foreach($taskChild in $taskStack.Pop().EnumerateFileSystemInfos()){
    if($taskChild.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected descendant'}
    if($taskChild.Name -eq '.git'){throw 'Embedded Git'}
    if($taskChild.Attributes -band [IO.FileAttributes]::Directory){$taskStack.Push([IO.DirectoryInfo]$taskChild)}else{$taskBytes+=$taskChild.Length;$taskFiles++}
}}
$taskFailure=Get-Content -LiteralPath (Join-Path $taskTarget 'cohort-failure.json') -Raw | ConvertFrom-Json
if($taskFailure.completed -ne 118 -or (@($taskFailure.unstarted_indices | ForEach-Object {[int]$_}) -join ',') -ne ((118..215) -join ',')){throw 'Prefix/unstarted suffix mismatch'}
$taskAudit=Get-Content -LiteralPath (Join-Path $taskTarget 'prefix-audit.json') -Raw | ConvertFrom-Json
if(-not $taskAudit.complete_prefix_audit -or -not $taskAudit.independent_correctness_passed -or $taskAudit.completed_cases -ne 118 -or $taskAudit.full_payload_rows -ne 3866624 -or $taskAudit.fully_checked_crc_bytes -ne 92798976){throw 'Full prefix independent decode missing'}
$taskLife=Get-Content -LiteralPath (Join-Path $taskTarget 'prefix-lifecycle-audit.json') -Raw | ConvertFrom-Json
if(-not $taskLife.complete -or -not $taskLife.no_performance_qualification -or $taskLife.probe_native_interval_pairs_checked -ne 42532){throw 'Full lifecycle audit missing'}
foreach($taskAuditName in @('phase145-prefix-audit-actual-exits.json','phase145-prefix-lifecycle-actual-exits.json')){
    $taskAuditActual=Get-Content -LiteralPath (Join-Path $taskWork $taskAuditName) -Raw | ConvertFrom-Json
    if(-not $taskAuditActual.actual_auditor_wait_completed -or ($taskAuditName -like '*lifecycle*' -and $taskAuditActual.lifecycle_actual_exit -ne 0) -or ($taskAuditName -notlike '*lifecycle*' -and $taskAuditActual.prefix_audit_actual_exit -ne 0)){throw 'Actual auditor exit missing'}
}
if(@(Get-Content -LiteralPath (Join-Path $taskTarget 'component-cases.jsonl')).Count -ne 118 -or (Test-Path -LiteralPath (Join-Path $taskTarget 'audit.json'))){throw 'Case journal or unstarted full audit mismatch'}
if(-not (Test-Path -LiteralPath (Join-Path $taskWork 'compaction-kit-144\candidate144.exe'))){throw 'Useful engine kit must survive'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');target=$taskTarget;files=$taskFiles;bytes=$taskBytes;private_head=$taskRemote.head;concise_outcomes_source_verified=$true;full_raw_byte_save_not_claimed=$true;no_reparse_or_git=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskWork 'phase145-storage-preflight.json') -Encoding utf8
Remove-Item -LiteralPath $taskTarget -Recurse -Force
if(Test-Path -LiteralPath $taskTarget){throw 'Removal incomplete'}
$taskResult=@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');deleted_exact_owned_target=$taskTarget;logical_bytes_removed=$taskBytes;files_removed=$taskFiles;D_free_bytes=(Get-PSDrive D).Free;all_deletes_native_literal_absolute_no_reparse=$true;existing_private_history_untouched=$true;completed145_prefix_stores_closed=$true;timed_cases_removed=118;unstarted_declared_cases=98;small_useful_binary_kits_retained=$true}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskWork 'phase145-storage-cleanup-proof.json') -Encoding utf8
$taskResult | ConvertTo-Json -Compress
