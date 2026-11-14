$ErrorActionPreference='Stop'
& 'D:\Codex\Kestrel\work\wait_compare135_audit_quiet.ps1'
if(-not $? -or $LASTEXITCODE -ne 0){throw 'Continuous quiet not established'}
foreach($taskAudit in @('main','lifecycle')){
 $taskLive=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^python(w|3.*)?\.exe$' -and ($_.CommandLine -match 'D:[/\\]Codex[/\\]Kestrel[/\\]work[/\\]' -or $_.CommandLine -match 'deployment_soak')})
 if($taskLive.Count){throw 'Other task/timed supervisor active'}
 & 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> ('D:\Codex\Kestrel\work\phase135-'+$taskAudit+'-preaudit-guard.log')
 if(-not $? -or $LASTEXITCODE -eq 3){throw 'Preaudit guard held'}
 & 'D:\Codex\Kestrel\work\check_global_build_activity.ps1'
 if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build active'}
 if($taskAudit -eq 'main'){$taskSource='audit_phase_compare_135.py';$taskProof='phase135-audit-actual-exits.json';$taskLog='audit-phase-compare-135.log'}else{$taskSource='audit_lifecycle_receipts_135.py';$taskProof='phase135-lifecycle-actual-exits.json';$taskLog='audit-lifecycle-receipts-135.log'}
 & 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' ('D:\Codex\Kestrel\work\'+$taskSource) *> ('D:\Codex\Kestrel\work\'+$taskLog)
 $taskExit=$LASTEXITCODE
 if(Test-Path -LiteralPath ('D:\Codex\Kestrel\work\'+$taskProof)){throw 'Do not overwrite audit actual exit'}
 @{utc=(Get-Date).ToUniversalTime().ToString('o');audit_actual_exit=$taskExit;actual_audit_wait_completed=$true;controller=$taskSource} | ConvertTo-Json | Set-Content -LiteralPath ('D:\Codex\Kestrel\work\'+$taskProof) -Encoding utf8
 Get-Content -LiteralPath ('D:\Codex\Kestrel\work\'+$taskLog) -Tail 8
 if($taskExit -ne 0){exit $taskExit}
}
exit 0
