# Current-release batching experiment 063

**4/10 identical zero-delay calibration checks fail; 6/26 optional-delay criteria fail.** This experiment uses the same frozen **0.3.16 executable path and SHA-256 for all four labels**. It introduces no engine change or new supported release. The default remains zero delay. [Older batching results](PERFORMANCE_034.md), [061 native gains and service failures](CORE_READ_PATH_061.md), and [062 calibration](SERVICE_CALIBRATION_062.md) remain intact.

Baseline A and B both use zero delay. The options use 1 ms and 4 ms collection windows already supported by `LiveOptions`. Four Latin-square rounds rotate all four labels so every label occupies each position once per profile. Every case starts from a fresh 1M-row store with 64 clients and 100-row identified append batches. The profiles offer 500 requests/s: 25% writes for 15 seconds and 5% writes for 60 seconds. The queue remains 256 requests with two-second worker expiry. Setup, cold reopen, exact retry, 20 NumPy windows per case and full CRC checks are outside arrivals. All 32 cases run serially; task-owned bridges stop after each case. [Predeclared policy](benchmarks/batching-063/policy.json), [all cases](benchmarks/batching-063/paired-service.json), [raw samples](benchmarks/batching-063/paired-service-samples/), [independent audit](benchmarks/batching-063/audit.json).

The primary comparator is always each option/A; option/B remains diagnostic. Ratios are medians of four within-round ratios, rather than ratios of displayed medians. Identical B/A p99 and throughput must stay in 0.90-1.10, with loss difference at most one percentage point. An option must reduce append p99 by at least 10% and publication attempts by at least 15%, preserve overall/query p99 within 10%, retain at least 90% of arrival-window throughput, increase losses by at most one percentage point and lose no request in any minute soak. Every option criterion and every identity check must pass to call it a demonstrated scoped improvement. All outcomes, slower rounds and losses remain visible.

| Profile / seconds | Label / delay ms | Overall p99 ms | Query p99 ms | Append p99 ms | Window req/s | Publication attempts | Lost / offered |
|---|---|---:|---:|---:|---:|---:|---:|
| write / 15 | baseline_a / 0 | 122.5356 | 1.2104 | 219.6151 | 500.00 | 1302.5 | 0 / 30,000 |
| write / 15 | baseline_b / 0 | 137.1441 | 1.2202 | 301.3733 | 499.93 | 1310.5 | 0 / 30,000 |
| write / 15 | delay1 / 1 | 105.4799 | 1.2188 | 254.5876 | 499.97 | 935.5 | 0 / 30,000 |
| write / 15 | delay4 / 4 | 121.2828 | 1.2178 | 231.9933 | 499.97 | 732.5 | 0 / 30,000 |
| mixed / 60 | baseline_a / 0 | 3.5688 | 1.2864 | 83.8408 | 500.00 | 1503.0 | 0 / 120,000 |
| mixed / 60 | baseline_b / 0 | 12.2778 | 1.2828 | 85.1070 | 500.00 | 1481.5 | 0 / 120,000 |
| mixed / 60 | delay1 / 1 | 25.9436 | 1.2828 | 91.3923 | 499.99 | 1236.0 | 0 / 120,000 |
| mixed / 60 | delay4 / 4 | 19.0106 | 1.2957 | 84.9796 | 500.00 | 1204.0 | 0 / 120,000 |

| Profile | Comparison | Overall ratio | Query ratio | Append ratio | Window req/s ratio | Publication ratio | Predeclared checks |
|---|---|---:|---:|---:|---:|---:|---|
| write | baseline_b/baseline_a | 1.2939 | 1.0110 | 1.6374 | 1.0000 | 0.9961 | ❌ 3/5 |
| write | delay1/baseline_a | 0.9313 | 1.0064 | 1.1015 | 1.0000 | 0.6235 | ❌ 5/6 |
| write | delay4/baseline_a | 1.0119 | 1.0133 | 1.0364 | 0.9999 | 0.5875 | ❌ 5/6 |
| write | delay1/baseline_b | 0.9186 | 0.9950 | 1.3168 | 1.0000 | 0.6244 | diagnostic only |
| write | delay4/baseline_b | 0.8006 | 1.0021 | 0.7311 | 0.9999 | 0.5773 | diagnostic only |
| mixed | baseline_b/baseline_a | 3.4518 | 0.9949 | 0.7371 | 1.0000 | 0.9822 | ❌ 3/5 |
| mixed | delay1/baseline_a | 6.6443 | 0.9672 | 1.3639 | 1.0000 | 0.8195 | ❌ 5/7 |
| mixed | delay4/baseline_a | 5.3484 | 0.9645 | 0.9897 | 1.0000 | 0.8011 | ❌ 5/7 |
| mixed | delay1/baseline_b | 3.0686 | 1.0020 | 1.1030 | 1.0000 | 0.8340 | diagnostic only |
| mixed | delay4/baseline_b | 3.0933 | 1.0124 | 0.9687 | 1.0000 | 0.8130 | diagnostic only |

- ❌ **delay1**: option criteria fail; identical-binary calibration fails; demonstrated scoped improvement **no**.
- ❌ **delay4**: option criteria fail; identical-binary calibration fails; demonstrated scoped improvement **no**.

| Profile | Label | Durable groups | Batches/group | Mean actual collection ms | Compactions | Compaction fraction of measured writer work |
|---|---|---:|---:|---:|---:|---:|
| write | baseline_a | 1263.5 | 1.648 | 0.0011 | 39.0 | 10.97% |
| write | baseline_b | 1271.5 | 1.624 | 0.0010 | 39.0 | 8.98% |
| write | delay1 | 908.0 | 2.114 | 5.3208 | 27.5 | 7.59% |
| write | delay4 | 711.0 | 2.756 | 8.3694 | 21.5 | 10.00% |
| mixed | baseline_a | 1458.0 | 1.017 | 0.0011 | 45.0 | 4.70% |
| mixed | baseline_b | 1436.5 | 1.033 | 0.0010 | 45.0 | 9.91% |
| mixed | delay1 | 1199.0 | 1.239 | 7.9951 | 37.0 | 6.42% |
| mixed | delay4 | 1168.0 | 1.270 | 10.8346 | 36.0 | 3.69% |

Actual collection includes code execution and OS scheduling. The compaction fraction divides measured compaction time by measured append-publication plus compaction time; it excludes collection, queueing and other work and is not a p99 decomposition. These posthoc diagnostics do not identify a scheduling cause or change the predeclared criteria. Publication attempts above include compaction publications.

All **600,000 offered requests** are accounted for, with 600,000 executed raw samples and 53,984 acknowledged append batches preserved after cold reopen. Whole-batch counts/sums, exact retry, **640 NumPy windows** and **897,561,600 CRC-scrubbed bytes** pass. Unacknowledged committed batches in the service runs: **0**. All minute cases have zero loss: **✅**. Losses, expiry, service/dispatch distributions and publication stage counters accompany successful-request quantiles; summed stage counters are not a causal explanation of p99.

Before performance timing, **24 new process-kill cycles** test zero, 1 and 4 ms with sixteen simultaneous producers and eight kill delays. Every acknowledged batch survives, all recovered batches are whole, exact retry retains original receipt generations after a second reopen, and full scrubs pass. Attempted / acknowledged / initially published batches: **820 / 532 / 532**; initially committed without an ACK: **0**. Those uncertain outcomes are disclosed and reconciled, not counted as successful ACKs. Every recovery store is retained. [Recovery results](benchmarks/batching-063/recovery.json), [adaptation provenance](benchmarks/batching-063/recovery-provenance.json).

These are current option measurements, not before/after engine-code improvements or competitor timings. Four pairs on a shared Windows desktop and finite offered schedules do not qualify maximum sustainable capacity. The collection deadline bounds intentional waiting, not OS wakeup, queued work, synchronization or ACK latency. Sync and publication are unchanged. Process kills on a live filesystem do not qualify physical power loss. No compiler, other heavy task, audit, packaging or cleanup overlaps timed workloads. All task-owned database processes stop after comparison; the supported source, binaries and already-issued morning report remain unchanged. [Process check](benchmarks/batching-063/post-qualification-process-check.json), [reproduction](benchmarks/batching-063/REPRODUCE.md), [full history](BENCHMARK_HISTORY.md).

The next scoped engine experiment is [bounded compaction fan-in](benchmarks/batching-063/NEXT_WORK.md), with unchanged row/byte ceilings and full independent correctness and service qualification. This is a measured motivation and a future test plan, not an implemented or verified speedup.

The first local package's summary mistakenly inherited a count of 27 service stores from 062. Its complete ZIP already contained all **32 service stores and 24 recovery stores**, with every CRC and payload hash verified. Before upload, the packager derives and asserts both actual counts, and a corrected package is produced. The first local package, original helper and summary remain preserved; no database case is rerun and no raw timing or fixture changes. [Metadata correction proof](benchmarks/batching-063/package-metadata-correction.json), [original summary](benchmarks/batching-063/package-metadata-failure/batching-063-bundle-check.json).

Private immutable [full batching evidence and stores](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-063-batching-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-063-batching-evidence.zip.sha256). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.
