param()
$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
$taskTarget='D:\Codex\Kestrel\work\restored-adaptive-speed-117'
$taskOriginal='D:\Codex\Kestrel\work\perf-117'
$taskBackup='D:\Codex\Kestrel\work\github-verified-trial117-20261010'
$taskOut='D:\Codex\Kestrel\work\cleanup-verified-restore-117-v3'
function Assert-RealPath([string]$taskPath) {
 $taskItem=Get-Item -LiteralPath $taskPath -Force
 if([IO.Path]::GetFullPath($taskPath) -cne $taskItem.FullName){throw "Unexpected resolved path: $taskPath"}
 for($taskHere=$taskItem;$null -ne $taskHere;$taskHere=$taskHere.Parent){
  if(($taskHere.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Reparse path: $($taskHere.FullName)"}
 }
}
function Hash([string]$taskPath) { (Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant() }
function Read-Json([string]$taskPath) { Get-Content -LiteralPath $taskPath -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable -DateKind String }
function Save-Json([string]$taskPath,$taskValue) {
 if(Test-Path -LiteralPath $taskPath){throw "Proof already exists: $taskPath"}
 $taskValue | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskPath -Encoding utf8
}
function Get-CheckedTree([string]$taskPath) {
 Assert-RealPath $taskPath
 $taskPending=[Collections.Generic.Queue[string]]::new();$taskPending.Enqueue($taskPath)
 $taskFiles=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
 $taskDirs=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
 while($taskPending.Count){
  $taskDir=$taskPending.Dequeue()
  foreach($taskItem in Get-ChildItem -LiteralPath $taskDir -Force){
   if(($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Reparse descendant: $($taskItem.FullName)"}
   $taskName=[IO.Path]::GetRelativePath($taskPath,$taskItem.FullName).Replace('\','/')
   if($taskName.StartsWith('../') -or [IO.Path]::IsPathRooted($taskName)){throw 'Escaped target'}
   $taskInfo=@{path=$taskItem.FullName;last_write_ticks=$taskItem.LastWriteTimeUtc.Ticks;attributes=[int]$taskItem.Attributes}
   if($taskItem.PSIsContainer){$taskDirs.Add($taskName,$taskInfo);$taskPending.Enqueue($taskItem.FullName)}
   else{$taskInfo.bytes=[long]$taskItem.Length;$taskFiles.Add($taskName,$taskInfo)}
  }
 }
 @{files=$taskFiles;dirs=$taskDirs}
}
if($taskTarget -cne (Join-Path $taskRoot 'restored-adaptive-speed-117') -or
 [IO.Path]::GetFullPath($taskTarget) -cne 'D:\Codex\Kestrel\work\restored-adaptive-speed-117'){throw 'Target scope mismatch'}
foreach($taskPath in @($taskRoot,$taskTarget,$taskOriginal,$taskBackup)){Assert-RealPath $taskPath}
if(Test-Path -LiteralPath $taskOut){throw 'Cleanup record already exists'}
$taskGuardPath=(Get-ChildItem -LiteralPath $taskRoot -Filter 'guard-final-117-*.json' -File | Sort-Object Name | Select-Object -Last 1).FullName
$taskGuard=Read-Json $taskGuardPath
if(-not $taskGuard.verified_idle_terminal_reset -or @($taskGuard.active_processes).Count -ne 0 -or
 ((Get-Date).ToUniversalTime()-[DateTimeOffset]::Parse($taskGuard.utc).UtcDateTime).TotalMinutes -gt 10){throw 'Fresh idle guard required'}
$taskJobs=@(Get-CimInstance Win32_Process | Where-Object {
 $_.ProcessId -ne $PID -and $_.CommandLine -match '[/\\](push_history(_batched)?_117|verify_remote_raw_117|run_native_\d+(_v\d+)?|run_service_\d+(_v\d+)?|build_\d+(_v\d+)?|preserve_\d+|finish_preservation_\d+)\.py'
})
if($taskJobs.Count){throw 'Task-owned workload active'}
$taskProofPath=Join-Path $taskBackup 'proof.json';$taskProofHash=Hash $taskProofPath;$taskProof=Read-Json $taskProofPath
if(-not $taskProof.complete -or -not $taskProof.every_download_size_SHA256_git_oid_exact -or
 -not $taskProof.all_actual_gh_exits0 -or -not $taskProof.all53_remote_downloaded_ZIP_member_CRCs_pass -or
 -not $taskProof.private_before_and_after -or $taskProof.immutable_remote_commit -ne '6aae0a3994fad1eef1b6267346212a3b094078a4' -or
 $taskProof.scope -ne 'benchmarks/adaptive-speed-117'){throw 'Complete exact fresh remote backup required'}
$taskManifestPath=Join-Path $taskOriginal 'evidence-inventory.json';$taskLayoutPath=Join-Path $taskOriginal 'archive-layout.json'
$taskDirsPath=Join-Path $taskOriginal 'directory-inventory.json'
foreach($taskName in @('evidence-inventory.json','archive-layout.json','directory-inventory.json')){
 if((Hash (Join-Path $taskOriginal $taskName)) -ne (Hash (Join-Path $taskBackup "files\$taskName"))){throw 'Original manifest differs from GitHub download'}
}
$taskInventory=Read-Json $taskManifestPath;$taskExpected=$taskInventory.entries
foreach($taskName in @('evidence-inventory.json','archive-layout.json')){
 $taskPath=Join-Path $taskOriginal $taskName
 $taskExpected[$taskName]=@{bytes=[long](Get-Item -LiteralPath $taskPath).Length;sha256=(Hash $taskPath)}
}
$taskExpectedDirs=@((Read-Json $taskDirsPath).directories)
if($taskExpected.Count -ne 38336 -or $taskExpectedDirs.Count -ne 5222){throw 'Unexpected complete restore shape'}
$taskLogicalBytes=[long]0;foreach($taskEntry in $taskExpected.Values){$taskLogicalBytes += [long]$taskEntry.bytes}
if($taskLogicalBytes -ne 4075316365){throw 'Unexpected complete restore size'}
New-Item -ItemType Directory -Path $taskOut | Out-Null
$taskPolicy=@{utc=(Get-Date).ToUniversalTime().ToString('o');before_any_deletion=$true;exact_target=$taskTarget;
 preserved_original=$taskOriginal;fresh_private_GitHub_download=$taskBackup;remote_backup_proof_sha256=$taskProofHash;
 immutable_remote_commit=$taskProof.immutable_remote_commit;files=38336;directories=5222;logical_bytes=$taskLogicalBytes;
 acceptance='Exact absolute native target; no reparse ancestors/descendants; exact file/directory sets, every size/SHA256, unchanged metadata immediately before delete; original and local ZIPs and downloaded backup retained.';
 guard_sha256=(Hash $taskGuardPath);manifest_sha256=(Hash $taskManifestPath);layout_sha256=(Hash $taskLayoutPath)}
Save-Json (Join-Path $taskOut 'policy.json') $taskPolicy
try {
 $taskBefore=Get-CheckedTree $taskTarget
 Save-Json (Join-Path $taskOut 'metadata-before.json') $taskBefore
 if($taskBefore.files.Count -ne $taskExpected.Count -or $taskBefore.dirs.Count -ne $taskExpectedDirs.Count){throw 'Actual tree count mismatch'}
 foreach($taskName in $taskExpectedDirs){if(-not $taskBefore.dirs.ContainsKey($taskName)){throw 'Directory set mismatch'}}
 $taskVerified=0
 foreach($taskName in $taskExpected.Keys){
  if(-not $taskBefore.files.ContainsKey($taskName)){throw "File set mismatch: $taskName"}
  $taskActual=$taskBefore.files[$taskName];$taskWanted=$taskExpected[$taskName]
  if($taskActual.bytes -ne $taskWanted.bytes -or (Hash $taskActual.path) -ne $taskWanted.sha256){throw "Size/hash mismatch: $taskName"}
  $taskVerified++
  if($taskVerified % 5000 -eq 0){Write-Output "Verified $taskVerified / 38336 restored files"}
 }
 $taskAfter=Get-CheckedTree $taskTarget
 Save-Json (Join-Path $taskOut 'metadata-after.json') $taskAfter
 foreach($taskKind in @('files','dirs')){
  if($taskBefore[$taskKind].Count -ne $taskAfter[$taskKind].Count){throw 'Tree changed during verification'}
  foreach($taskName in $taskBefore[$taskKind].Keys){
   if(-not $taskAfter[$taskKind].ContainsKey($taskName)){throw 'Tree set changed during verification'}
   $taskA=$taskBefore[$taskKind][$taskName];$taskB=$taskAfter[$taskKind][$taskName]
   foreach($taskField in @('path','last_write_ticks','attributes','bytes')){
    if($taskA[$taskField] -cne $taskB[$taskField]){throw ("Metadata changed: {0}, field {1}, before {2}, after {3}" -f $taskName,$taskField,$taskA[$taskField],$taskB[$taskField])}
   }
  }
 }
 if((Hash $taskProofPath) -ne $taskProofHash -or (Hash $taskManifestPath) -ne $taskPolicy.manifest_sha256 -or
 (Hash $taskLayoutPath) -ne $taskPolicy.layout_sha256){throw 'Preservation proofs changed'}
 Assert-RealPath $taskTarget
 $taskFreeBefore=[long](Get-PSDrive D).Free
 Save-Json (Join-Path $taskOut 'verification-before-delete.json') (@{utc=(Get-Date).ToUniversalTime().ToString('o');all38336_current_file_SHA_size_exact=$true;all5222_directory_sets_exact=$true;no_reparse=$true;metadata_unchanged=$true;D_free_bytes=$taskFreeBefore;target=$taskTarget})
 Remove-Item -LiteralPath 'D:\Codex\Kestrel\work\restored-adaptive-speed-117' -Recurse -Force
 if(Test-Path -LiteralPath $taskTarget){throw 'Target still exists after removal'}
 foreach($taskPath in @($taskOriginal,$taskBackup)){Assert-RealPath $taskPath}
 $taskFreeAfter=[long](Get-PSDrive D).Free
 $taskDone=@{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');exact_removed_target=$taskTarget;
 files_removed=38336;directories_removed=5222;logical_bytes_removed=$taskLogicalBytes;D_free_before_bytes=$taskFreeBefore;
 D_free_after_bytes=$taskFreeAfter;observed_D_free_delta_bytes=($taskFreeAfter-$taskFreeBefore);
 physical_free_delta_can_include_unrelated_background_activity=$true;current_full_hash_and_sets_verified_before_removal=$true;
 original_perf117_and_local_repo_archives_and_fresh_GitHub_downloads_retained=$true;
 only_unused_restored_trial117_duplicate_removed=$true;no_C_app_history_original_failed_trial_or_other_restore_removed=$true}
 Save-Json (Join-Path $taskOut 'proof.json') $taskDone
 $taskDone | ConvertTo-Json -Compress
} catch {
 Save-Json (Join-Path $taskOut 'failure.json') @{utc=(Get-Date).ToUniversalTime().ToString('o');error=$_.ToString();target_still_exists=(Test-Path -LiteralPath $taskTarget);all_originals_and_archives_retained=$true}
 throw
}
