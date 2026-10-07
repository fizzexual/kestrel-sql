# Reproduce native publication diagnostics 051 and 052

These commands use the preserved release-mode binaries on this Windows computer. They do not compile anything. Run one diagnostic at a time, without another database benchmark, compiler, test suite, archive operation or Git compression running. Keep all new fixtures and unsuccessful output. A repeated run is new evidence; it does not replace the original results.

Use the existing checkout at `C:\Users\Frizer\Documents\Codex\2026-10-05\letys\outputs\kestrel-sql`. The preserved Python harness expects this `outputs/kestrel-sql` and sibling `work` layout. Source and binary hashes are in each original policy. The immutable private downloads are linked from [051](PUBLICATION_051.md) and [052](TRIAL_052.md).

For 051, start PowerShell in the repository and create a fresh task-owned directory:

```powershell
$repoPath = (Get-Location).Path
$taskPath = Split-Path (Split-Path $repoPath -Parent) -Parent
$jobPath = Join-Path $taskPath ('work\native-repro-051-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $jobPath | Out-Null
Copy-Item -LiteralPath (Join-Path $repoPath 'benchmarks\publication-051-native\native_publication.py') -Destination $jobPath
Copy-Item -LiteralPath (Join-Path $repoPath 'benchmarks\publication-051-native\audit_native.py') -Destination $jobPath
python (Join-Path $jobPath 'native_publication.py') --initialize
python (Join-Path $jobPath 'native_publication.py')
python (Join-Path $jobPath 'audit_native.py')
```

Check each Python exit code before proceeding. The first command declares and hashes the policy; the second executes all 18 serial cases, retains raw stdout/stderr/status and stores fresh databases under `fixtures`; the third audits after timing has finished. The native driver verifies exact COUNT/SUM, full CRCs and cold duplicate retries. Stage-counter deltas include maintenance, while append timers exclude it. This diagnostic does not establish maximum service requests/s.

For the rejected 052 experiment, use a different fresh directory and copy its isolated source/binaries alongside the harness:

```powershell
$jobPath = Join-Path $taskPath ('work\native-repro-052-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $jobPath | Out-Null
$evidencePath = Join-Path $repoPath 'benchmarks\trial-052-pending-length'
Copy-Item -LiteralPath (Join-Path $evidencePath 'candidate') -Destination $jobPath -Recurse
Copy-Item -LiteralPath (Join-Path $evidencePath 'bin') -Destination $jobPath -Recurse
foreach ($name in @('native_publication.py', 'audit_native.py', 'audit_advance.py', 'trial-policy.json')) {
    Copy-Item -LiteralPath (Join-Path $evidencePath $name) -Destination $jobPath
}
python (Join-Path $jobPath 'native_publication.py') --initialize
python (Join-Path $jobPath 'native_publication.py')
python (Join-Path $jobPath 'audit_native.py')
python (Join-Path $jobPath 'audit_advance.py')
```

The last step checks every paired final database frame for byte equality and evaluates the original four advance gates. It runs only after all timing. Original 052 fails all four gates and is not a supported upgrade. The ordinary binaries have no fault hooks; `publication_fault_probe.exe` is explicitly test-only. The corrected cut harness and preserved failing coverage assertions remain in the evidence directory. The full 050 correctness qualification and 052's narrower release/cut/kill qualification are distinct.

Neither harness restarts an existing result directory. Stop only processes you launched for this test if interrupted; never stop another user's database or compiler. The original work fixtures remain preserved separately from the Git repository and ZIPs, with their hashes recorded in the reports.
