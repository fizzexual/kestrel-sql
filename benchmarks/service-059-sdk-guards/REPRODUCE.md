# Reproduce service controls 059

059 changes no engine code. It measures the frozen SDK development build from 058 (`0.3.17-dev.58`) against supported `0.3.16`, on one shared Windows computer. Original SHA-256, policy, versions, wall times, compilation provenance, every raw sample and all stores remain evidence of that original run. New timings must stay in a separate directory.

Use Python 3.12+ with NumPy available for the independent cold SQL oracle (original 3.12.10 / NumPy 2.2.5). Original host telemetry uses Windows APIs and reports whole-host CPU/memory at 1 Hz; it cannot identify storage or process causes. Check the artifact manifest before executing binaries. Keep builds, correctness suites, audits, packaging and cache cleanup outside timing windows.

To use the original runners without path edits, create this directory layout in a new workspace:

```text
workspace/
  outputs/kestrel-sql/        # private repository checkout, frozen 0.3.16 baseline bins/harness
  work/perf-059/              # policy.json, paired_service.py, bin/kestrel-stress.exe
  work/perf-058/candidate/    # exact SDK source for the post-run auditor
```

The 059 evidence ZIP carries `engine-058-source/` so the exact SDK source can be copied into `work/perf-058/candidate`. Candidate binary and build provenance are part of 059. The previous [058 development evidence](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-058-error-contract-evidence.zip) contains the complete original build/driver history. Use the repository commit that publishes 059 for the accompanying supported baseline/harness; historical supported archives are unchanged.

Copy the original policy into a new policy, retain its workload/guard values, and explicitly record the new declaration time before running. Do not copy original `paired-service.json`, `paired-service-samples/` or `service-fixtures/` into the new run directory. The runner refuses existing result/store directories. For an independent compiler run, first rebuild the exact SDK source/lock as a default, feature-free `kestrel-stress` release binary, record toolchain/source/binary hashes and update the candidate hash in the new policy. Compilation must end before service workloads start. This constitutes a new experiment; do not substitute its outputs for original 059.

Add `outputs/kestrel-sql/benchmarks` to `PYTHONPATH`, plus your NumPy dependency path when needed. Run `python -u work/perf-059/paired_service.py` from the workspace. It executes 36 fresh local cases: six profiles, three rounds and two variants, alternating variant order. Each case starts one task-owned loopback bridge and stops it after cold reopen and reconciliation. Setup/seeding, the NumPy checks and full CRC scrubs are outside the arrival timer. The write-labelled profile is 25% writes; mixed is 5%, scan is 10% and read is 0%. All writes contain 100 rows; there are 64 clients and zero intentional group delay.

Preserve the complete output even if the script fails. A failed case stops the runner; it does not quietly retry a timed case or discard earlier results. No automatic resume or promotion is provided. The original fixed disk preflight reserves 800,000,000 free bytes before every case; the original debug-cache reclamation occurs before any timed run and is recorded separately. Reclaim only verified disposable task-owned compilation caches when necessary; keep all original source, binaries, reports and stores.

The actual original run stopped after 20 completed cases at a low-space preflight. `resume_service.py` is a separate evidence-specific continuation, not a generic rerun mechanism: it asserts the exact failed label/byte count, snapshots the initial attempt, verifies all original raw hashes, skips all 20 completed tuples and executes only 16 unstarted cases. The report retains both phases. No pair spans the maintenance pause. For a new experiment, preserve any failed attempt and design a separate continuation only after inspecting the failure; do not substitute original 059's maintenance paths or failure-specific assumptions.

After the runner and all children have exited, run `python work/perf-059/audit.py`. It recalculates raw percentiles, sequence accounting, offered losses and paired ratios; verifies the unchanged supported source/binaries and SDK source; checks publication-stage counter deltas; and audits every cold acknowledgment/batch/NumPy/CRC assertion. The original auditor additionally checks the already-issued morning report's preserved hash. Reports distinguish successful-operation latency from dropped/expired/failed operations, completion throughput inside the arrival window from throughput including drain, regression guards from the separate zero-loss sustained goal, and current timings from historical 047/055/058.

All original stores and a complete per-file inventory are included in the separate development ZIP. Process restart, finite single-machine load and passing CRCs do not establish physical power-loss, distributed, PostgreSQL equivalence or production qualification. There is no fresh competitor comparison in 059.
