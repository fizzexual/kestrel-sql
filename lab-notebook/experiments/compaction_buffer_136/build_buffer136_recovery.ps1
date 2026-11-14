$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work\perf-136'
if(Test-Path -LiteralPath ($taskRoot+'\recovery-artifact-build.json')){throw 'Do not repeat recovery artifact build'}
$taskPoints=@('segment_partial','segment_written','segment_synced','catalog_partial','catalog_written','catalog_synced','catalog_published')
$taskDeclaration=@{utc=(Get-Date).ToUniversalTime().ToString('o');points=$taskPoints;modes=@('exit','io_error');fresh_owned_fault_cases=14;expected_rows_each=2048;all_existing_named_receipts_preserved=$true;all_cases_excluded_correctness_only=$true;normal_and_fault_artifacts_only=$true;no_passed_test_suite_repeated=$true;physical_power_loss_claim=$false;timed_qualification_cases=0}
$taskDeclaration | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($taskRoot+'\recovery-declaration.json') -Encoding utf8
$env:CARGO_TARGET_DIR=$taskRoot+'\target'
$env:CARGO_INCREMENTAL='0';$env:CARGO_BUILD_JOBS='4'
$env:TMP=$taskRoot+'\tmp';$env:TEMP=$taskRoot+'\tmp'
$taskRecords=[Collections.Generic.List[object]]::new()
Push-Location -LiteralPath ($taskRoot+'\candidate')
try{
 foreach($taskMode in @('normal','fault')){
  & 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> ('D:\Codex\Kestrel\work\buffer136-recovery-build-'+$taskMode+'-guard.log')
  if(-not $? -or $LASTEXITCODE -eq 3){throw 'Timed/reset activity blocks recovery build'}
  $taskLive=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
  if($taskLive.Count){throw 'Other task supervisor active'}
  & 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
  if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build activity'}
  $taskArgs=@('build','--release','--offline','--locked','--features')
  if($taskMode -eq 'normal'){$taskArgs+=@('adaptive-segment-buffer-136','--bin','kestrel','--example','receipt_seed')}else{$taskArgs+=@('adaptive-segment-buffer-136,fault-injection','--example','publication_fault_probe')}
  $taskStarted=(Get-Date).ToUniversalTime().ToString('o')
  & 'C:\Users\Frizer\.cargo\bin\cargo.exe' @taskArgs *> ($taskRoot+'\logs\recovery-artifact-'+$taskMode+'.log')
  $taskExit=$LASTEXITCODE
  $taskRecords.Add(@{mode=$taskMode;actual_exit=$taskExit;actual_wait_completed=$true;started_utc=$taskStarted;completed_utc=(Get-Date).ToUniversalTime().ToString('o');argv=$taskArgs})
  if($taskExit -ne 0){throw ('Recovery artifact build failed: '+$taskMode)}
  if($taskMode -eq 'normal'){
   Copy-Item -LiteralPath ($taskRoot+'\target\release\kestrel.exe') -Destination ($taskRoot+'\binary\recovery136-cli.exe')
   Copy-Item -LiteralPath ($taskRoot+'\target\release\examples\receipt_seed.exe') -Destination ($taskRoot+'\binary\recovery136-seed.exe')
  }else{Copy-Item -LiteralPath ($taskRoot+'\target\release\examples\publication_fault_probe.exe') -Destination ($taskRoot+'\binary\recovery136-fault.exe')}
 }
 $taskHashes=@{}
 foreach($taskName in @('recovery136-cli.exe','recovery136-seed.exe','recovery136-fault.exe')){$taskHashes[$taskName]=(Get-FileHash -LiteralPath ($taskRoot+'\binary\'+$taskName) -Algorithm SHA256).Hash.ToLowerInvariant()}
 @{complete=$true;utc=(Get-Date).ToUniversalTime().ToString('o');records=$taskRecords;binary_sha256=$taskHashes;fresh_tests_repeated=0;timed_qualification_cases=0} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath ($taskRoot+'\recovery-artifact-build.json') -Encoding utf8
 'Recovery artifacts built; no passed tests repeated'
}catch{
 @{utc=(Get-Date).ToUniversalTime().ToString('o');records=$taskRecords;error=$_.Exception.Message;recovery_cases_unstarted=14} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath ($taskRoot+'\recovery-artifact-build-failure.json') -Encoding utf8
 throw
}finally{Pop-Location}
