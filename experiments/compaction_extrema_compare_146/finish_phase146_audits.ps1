$ErrorActionPreference='Stop'
$taskRoot='D:\Codex\Kestrel\work'
if((Test-Path -LiteralPath (Join-Path $taskRoot 'phase146-audit-actual-exits.json')) -or (Test-Path -LiteralPath (Join-Path $taskRoot 'phase146-lifecycle-actual-exits.json'))){throw 'Audits already attempted; inspect their actual exits'}
$taskActual=Get-Content -LiteralPath (Join-Path $taskRoot 'phase146-actual-exits.json') -Raw | ConvertFrom-Json
if($taskActual.cohort_actual_exit -ne 0 -or -not $taskActual.actual_controller_wait_completed){throw 'Actual controller completion required'}
& 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File (Join-Path $taskRoot 'wait_compare146_audit_quiet.ps1')
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$taskQuiet=Get-Content -LiteralPath (Join-Path $taskRoot 'phase146-audit-quiet-proof.json') -Raw | ConvertFrom-Json -DateKind String
if(-not $taskQuiet.complete -or $taskQuiet.continuous_observed_clear_seconds -lt 120 -or ((Get-Date).ToUniversalTime()-[datetime]$taskQuiet.utc).TotalSeconds -gt 60){throw 'Fresh continuous quiet incomplete'}
& 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File (Join-Path $taskRoot 'launch_audits_phase146.ps1')
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' (Join-Path $taskRoot 'audit_phase146_manual_probe.py') *> (Join-Path $taskRoot 'phase146-manual-probe-audit.log')
$taskExit=$LASTEXITCODE
@{utc=(Get-Date).ToUniversalTime().ToString('o');manual_probe_audit_actual_exit=$taskExit;actual_auditor_wait_completed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'phase146-manual-probe-actual-exits.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot 'phase146-manual-probe-audit.log') -Tail 2
exit $taskExit
