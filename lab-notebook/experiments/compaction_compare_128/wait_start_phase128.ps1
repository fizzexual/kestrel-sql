$ErrorActionPreference='Stop'
$taskDeadline=(Get-Date).ToUniversalTime().AddHours(2)
$taskLogRoot='D:\Codex\Kestrel\work'
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$taskPrevious=''
function Wait-QuietPhase128 {
    while($true){
        if((Get-Date).ToUniversalTime() -gt $taskDeadline){throw 'Wait deadline expired; no new timing started'}
        $taskBusy=@(Get-OtherWork | Select-Object ProcessId,Name)
        $taskBuild=@(Get-CimInstance Win32_Process | Where-Object {
            $_.ProcessId -ne $PID -and (
                $_.Name -match '^(rustc|cargo|clippy-driver|MSBuild|cmake|ninja|javac)\.exe$' -or
                ($_.Name -match '^python(w|3.*)?\.exe$' -and $_.CommandLine -match '(?i)(^|[\\/\s"''])build\.py([\s"'']|$)') -or
                ($_.Name -match '^(node|cmd|powershell|pwsh|dotnet|java)\.exe$' -and $_.CommandLine -match '(?i)(npm|pnpm|yarn|dotnet|gradle|mvn).{0,60}\b(build|compile|package|assemble|test|publish|install|verify)\b') -or
                ($_.Name -eq 'java.exe' -and $_.CommandLine -match '(?i)(org\.codehaus\.plexus\.classworlds\.launcher\.Launcher|org\.gradle\.).*\b(build|compile|package|assemble|test|publish|install|verify)\b')
            )
        } | Select-Object ProcessId,Name)
        $taskKey=(@($taskBusy)+@($taskBuild) | Sort-Object ProcessId -Unique | ConvertTo-Json -Compress)
        if($taskKey -ne $script:taskPrevious){Write-Output ('WAIT_ACTIVITY '+$taskKey);$script:taskPrevious=$taskKey}
        if($taskBusy.Count -eq 0 -and $taskBuild.Count -eq 0){return}
        Start-Sleep -Seconds 40
    }
}
try {
    Wait-QuietPhase128
    & 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase preaudit *> (Join-Path $taskLogRoot 'phase128-preparation-guard.log')
    & 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\prepare_phase_compare_128.py' *> (Join-Path $taskLogRoot 'prepare-phase-compare-128.log')
    if($LASTEXITCODE -ne 0){throw 'Preparation failed; inspect its actual log'}
    Write-Output 'PHASE128_DECLARED_216_PREPARED'
    & 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\smoke_phase_compare_128.py' *> (Join-Path $taskLogRoot 'smoke-phase-compare-128.log')
    if($LASTEXITCODE -ne 0){throw 'Smoke failed; no qualification timer'}
    Write-Output 'PHASE128_SIX_INDEPENDENT_SMOKES_PASS'
    Wait-QuietPhase128
    & 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase pretime *> (Join-Path $taskLogRoot 'phase128-pretime-guard.log')
    & 'D:\Codex\Kestrel\work\check_global_build_activity.ps1' *> (Join-Path $taskLogRoot 'phase128-global-preflight.log')
    if(-not $?){throw 'Visible build preflight failed'}
    & 'D:\Codex\Kestrel\work\launch_phase_compare_128.ps1'
    if($LASTEXITCODE -ne 0){throw 'Actual cohort exit failed; no selected retiming'}
    Write-Output 'PHASE128_ACTUAL_COHORT_EXIT_ZERO'
    Wait-QuietPhase128
    & 'D:\Codex\Kestrel\work\guard_cleanup_20261010.ps1' -Phase posttime *> (Join-Path $taskLogRoot 'phase128-posttime-guard.log')
    & 'C:\Users\Frizer\AppData\Local\Programs\Python\Python312\python.exe' 'D:\Codex\Kestrel\work\audit_phase_compare_128.py' *> (Join-Path $taskLogRoot 'audit-phase-compare-128.log')
    $taskAuditExit=$LASTEXITCODE
    $taskExits=Get-Content -LiteralPath (Join-Path $taskLogRoot 'phase128-actual-exits.json') -Raw | ConvertFrom-Json
    $taskExits | Add-Member -NotePropertyName audit_actual_exit -NotePropertyValue $taskAuditExit
    $taskExits | Add-Member -NotePropertyName audit_actual_wait_completed -NotePropertyValue $true
    $taskExits | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskLogRoot 'phase128-actual-exits.json') -Encoding utf8
    Get-Content -LiteralPath (Join-Path $taskLogRoot 'audit-phase-compare-128.log') -Tail 3
    if($taskAuditExit -ne 0){throw 'Actual independent audit failed; preserve all cases'}
    Write-Output 'PHASE128_COMPLETE_ALL_INDEPENDENT_AUDITS_ZERO'
} catch {
    @{utc=(Get-Date).ToUniversalTime().ToString('o');error=$_.Exception.Message;no_process_or_app_stopped=$true;no_selected_retiming=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskLogRoot 'phase128-wait-or-stage-failure.json') -Encoding utf8
    Write-Error $_
    exit 1
}
