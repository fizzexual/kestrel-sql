$ErrorActionPreference = 'Stop'
$kestrelCommitProof=Get-Content -LiteralPath 'D:\Codex\Kestrel\work\commit-089-proof.json' -Raw | ConvertFrom-Json
if (-not $kestrelCommitProof.clean -or -not $kestrelCommitProof.supported_core_and_overnight_unchanged) { throw 'Commit proof incomplete' }
$kestrelExpectedHead=$kestrelCommitProof.head
$kestrelRestoreProof=Get-Content -LiteralPath 'D:\Codex\Kestrel\outputs\kestrel-sql\benchmarks\build-compare-089\restored-audit-proof.json' -Raw | ConvertFrom-Json
if (-not $kestrelRestoreProof.passed -or $kestrelRestoreProof.native_launches -ne 0 -or $kestrelRestoreProof.timing_reruns -ne 0) { throw 'Restoration proof incomplete' }
. 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -LoadForTests
$kestrelJobs = @(Get-OtherWork)
if ($kestrelJobs.Count) { throw 'Task work is still active; final state is not quiet.' }
$kestrelReset = Get-Content -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\reset-status.json' -Raw | ConvertFrom-Json
if ($kestrelReset.phase -ne 'waiting-for-full-codex-exit') { throw 'Offline reset state changed; do not interfere.' }
$kestrelWorker = Get-CimInstance Win32_Process -Filter 'ProcessId=23176'
if (-not $kestrelWorker -or $kestrelWorker.CreationDate.ToUniversalTime().ToString('o') -ne '2026-10-08T10:33:01.5395400Z') { throw 'Worker identity changed.' }
$kestrelOwner = Invoke-CimMethod -InputObject $kestrelWorker -MethodName GetOwnerSid
if ($kestrelOwner.Sid -ne [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) { throw 'Worker owner changed.' }
Assert-Real 'D:\Codex\Kestrel'
Assert-Real 'D:\Codex\Kestrel\work'
Assert-Real 'D:\Codex\Kestrel\outputs\kestrel-sql'
if ((Get-FileHash -LiteralPath 'D:\Codex\Migration-20261007\fresh-profile-20261008\fresh_reset.ps1' -Algorithm SHA256).Hash.ToLowerInvariant() -ne '005d2246f6948eb9d2cef36a9169d9bcd82c9289c9bb0c5f7565fdae79b27e3b') { throw 'Reset helper hash changed.' }
if ((Get-FileHash -LiteralPath 'D:\Codex\Migration-20261007\helper-runtime\powershell\pwsh.exe' -Algorithm SHA256).Hash.ToLowerInvariant() -ne '362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139') { throw 'Independent runtime hash changed.' }
$kestrelOldTask = Get-ScheduledTask -TaskName 'Codex-Kestrel-Migrate-20261007'
$kestrelFreshTask = Get-ScheduledTask -TaskName 'Codex-Kestrel-Fresh-20261008'
if ($kestrelOldTask.State -ne 'Disabled' -or $kestrelFreshTask.State -ne 'Running') { throw 'Scheduled task state changed.' }
$kestrelCurrentAutomation = Get-Content -LiteralPath 'C:\Users\Frizer\.codex\automations\continue-kestrelsql-on-d\automation.toml' -Raw
$kestrelOldAutomation = Get-Content -LiteralPath 'C:\Users\Frizer\.codex\automations\keep-improving-kestrelsql\automation.toml' -Raw
if ($kestrelCurrentAutomation -notmatch 'status\s*=\s*"ACTIVE"' -or $kestrelCurrentAutomation -notmatch '01a11a37-2a11-7cc0-99eb-de65618b6f70') { throw 'Current D: continuation changed.' }
if ($kestrelOldAutomation -notmatch 'status\s*=\s*"PAUSED"') { throw 'Old automation no longer paused.' }
$kestrelRepo = 'D:/Codex/Kestrel/outputs/kestrel-sql'
$kestrelHead = (& git -c "safe.directory=$kestrelRepo" -C $kestrelRepo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $kestrelHead -ne $kestrelExpectedHead) { throw 'Unexpected repository HEAD.' }
$kestrelStatus = @(& git -c "safe.directory=$kestrelRepo" -C $kestrelRepo status --porcelain)
if ($LASTEXITCODE -ne 0 -or $kestrelStatus.Count) { throw 'Repository is not clean.' }
$kestrelProof = @{utc=(Get-Date).ToUniversalTime().ToString('o'); head=$kestrelHead; clean=$true; active_benchmark_jobs=0; reset_phase=$kestrelReset.phase; exact_worker_identity_and_owner_verified=$true; helper_and_runtime_unchanged=$true; old_migration_task_disabled=$true; old_automation_paused=$true; current_D_heartbeat_active=$true; physical_D_workspace_verified=$true; D_free_bytes=(Get-PSDrive D).Free; supported='0.3.16'; raw_restore_verified=$true; no_release_or_remote_publication=$true}
$kestrelProof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'D:\Codex\Kestrel\work\build-089-final-state.json' -Encoding utf8
$kestrelProof | ConvertTo-Json -Compress
