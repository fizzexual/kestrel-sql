$ErrorActionPreference='Stop'
& 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File 'D:\Codex\Kestrel\work\wait_prefix145_audit_quiet.ps1'
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -NoProfile -File 'D:\Codex\Kestrel\work\launch_prefix145_audits.ps1'
exit $LASTEXITCODE
