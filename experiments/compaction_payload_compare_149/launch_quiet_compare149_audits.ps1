$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath 'D:\Codex\Kestrel\work\phase149-audit-actual-exits.json'){throw 'Never repeat a passed or failed existing audit'}
& 'D:\Codex\Kestrel\work\wait_compare149_audit_quiet.ps1' *> 'D:\Codex\Kestrel\work\phase149-complete-audit-quiet.log'
if(-not $? -or $LASTEXITCODE -ne 0){throw 'Continuous quiet did not complete; no auditor started'}
& 'D:\Codex\Kestrel\work\launch_audits_phase149.ps1'
exit $LASTEXITCODE
