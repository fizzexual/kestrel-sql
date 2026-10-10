$ErrorActionPreference='Stop'
$taskRows=@(Get-CimInstance Win32_Process | Where-Object {
 $_.ProcessId -ne $PID -and (
  $_.Name -match '^(rustc|cargo|clippy-driver|MSBuild|cmake|ninja|javac)\.exe$' -or
  ($_.Name -match '^python(w|3.*)?\.exe$' -and $_.CommandLine -match '(?i)(^|[\\/\s"''])build\.py([\s"'']|$)') -or
  ($_.Name -match '^(node|cmd|powershell|pwsh|dotnet|java)\.exe$' -and $_.CommandLine -match '(?i)(npm|pnpm|yarn|dotnet|gradle|mvn).{0,60}\b(build|compile|package|assemble|test|publish|install|verify)\b') -or
  ($_.Name -eq 'java.exe' -and $_.CommandLine -match '(?i)(org\.codehaus\.plexus\.classworlds\.launcher\.Launcher|org\.gradle\.).*\b(build|compile|package|assemble|test|publish|install|verify)\b')
 )
} | ForEach-Object { [pscustomobject]@{name=$_.Name;pid=$_.ProcessId;creation_utc=$_.CreationDate.ToUniversalTime().ToString('o')} })
$taskProof=@{utc=(Get-Date).ToUniversalTime().ToString('o');visible_build_jobs=$taskRows;no_visible_build_jobs=($taskRows.Count -eq 0);not_during_timing=$true;no_process_or_app_changed=$true}
$taskProof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ('D:\Codex\Kestrel\work\global-build-preflight-'+(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffffff')+'.json') -Encoding utf8
$taskProof | ConvertTo-Json -Compress
if($taskRows.Count){exit 3}
