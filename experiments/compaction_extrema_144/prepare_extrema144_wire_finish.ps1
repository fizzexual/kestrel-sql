$ErrorActionPreference='Stop'
$taskSource=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\check_extrema144_wire_activity.ps1' -Raw
$taskTarget='D:\Codex\Kestrel\work\check_extrema144_wire_finish_activity.ps1'
if(Test-Path -LiteralPath $taskTarget){throw 'Do not overwrite finishing guard'}
$taskSource.Replace('audit_extrema144_legacy_wire','finish_extrema144_wire') | Set-Content -LiteralPath $taskTarget -Encoding utf8 -NoNewline
