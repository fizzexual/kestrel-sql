$ErrorActionPreference='Stop'
$taskSource=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\check_coalesce140_prerequisite_activity.ps1' -Raw
$taskTarget='D:\Codex\Kestrel\work\check_profile142_build_activity.ps1'
if(Test-Path -LiteralPath $taskTarget){throw 'Do not overwrite142 build guard'}
$taskSource.Replace('build_coalesce_140','build_index_profile_142') | Set-Content -LiteralPath $taskTarget -Encoding utf8 -NoNewline
