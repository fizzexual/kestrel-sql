# Bounded compaction trial 064

**5/6 native speed goals, 1/12 candidate guards and 5/18 identical-baseline checks fail.** The compaction-only **0.3.17-dev.64** candidate is retained as development evidence. Per the declared policy, it does not advance to service testing or become the supported build. Supported **0.3.16** and all previous results remain unchanged. [063 batching](BATCHING_063.md), [062 calibration](SERVICE_CALIBRATION_062.md), [061 analytical wins and service failures](CORE_READ_PATH_061.md), [full history](BENCHMARK_HISTORY.md).

The candidate increases `compact_small`'s maximum selected run count from 32 to 64. The 65,536-row and 64 MiB ceilings, small-run definition, live trigger at 64 small runs, publication format, synchronization and receipt contract stay the same. It is based directly on released 0.3.16; parser 061 and SDK 058/060 changes are excluded. [Candidate source and hashes](benchmarks/compaction-064/source-provenance.json), [exact source](benchmarks/compaction-064/lab/outputs/kestrel-sql/src/archive.rs), [row-ceiling/pinned-reader/retry test](benchmarks/compaction-064/lab/outputs/kestrel-sql/tests/compaction_fanin.rs).

The motivation was 063's measured compaction share of writer work: 10.97% in its zero-delay write profile and 4.70% in its minute mixed profile. Those older service fractions motivate a hypothesis; they do not predict new throughput or p99. This new trial measures sequential native writes, not those service profiles.

There are **27 fresh serial cases**: three Latin-square rounds, receipt histories of 0 / 50,000 / 99,000, and A / B / candidate labels. Each case appends 256 identified batches of 100 rows. Seed histories contain one row per receipt, so final row counts are 25,600 / 75,600 / 124,600. All three labels use byte-identical driver source. A and B share one exact newly linked executable on freshly built released source; these are **not the old prebuilt publication probe file**. The candidate is linked against its qualified default library. [Driver/build provenance](benchmarks/compaction-064/native-driver-build.json), [predeclared goals](benchmarks/compaction-064/policy.json), [frozen case order and aggregation](benchmarks/compaction-064/native-policy.json), [all raw results](benchmarks/compaction-064/native-raw/), [independent audit](benchmarks/compaction-064/native-audit.json).

Before the first performance case, the original every-32-appends driver was corrected to the live 64-small-run trigger; using the former would conceal the intended maintenance-frequency change. The old policy draft is preserved. The charged primary total is every append latency plus every compact-and-reclaim latency. Setup, per-append allocation before the call, stats inspection, SQL checks, cold retries and CRC scans are outside those timers. Append p99 uses Type 7 interpolation over all 256 raw samples. Per-size decisions use the median of three within-round ratios; displayed medians are not divided to produce those ratios. Candidate/A remains primary, B/A is identity calibration, and candidate/B is diagnostic. The two small driver/memory smoke stores are excluded from every competitive sample and ratio.

| Starting receipts | Label | Append + maintenance ms | Append p50 ms | Append p99 ms | Max append ms | Cold reopen ms | Peak working set MiB |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | baseline_a | 3023.7202 | 2.1898 | 48.8047 | 72.3083 | 3.3514 | 4.797 |
| 0 | baseline_b | 2840.5925 | 2.1826 | 43.0343 | 55.3719 | 3.3188 | 4.867 |
| 0 | candidate | 3139.8909 | 2.1723 | 62.6072 | 84.9600 | 1.1555 | 5.172 |
| 50,000 | baseline_a | 961.5646 | 2.0832 | 38.8771 | 57.7901 | 58.9751 | 26.129 |
| 50,000 | baseline_b | 1123.6635 | 2.0959 | 51.0301 | 89.6629 | 58.9659 | 26.117 |
| 50,000 | candidate | 10706.3814 | 2.2753 | 953.7347 | 999.1270 | 57.4676 | 26.082 |
| 99,000 | baseline_a | 1452.6224 | 2.0991 | 102.8392 | 111.0036 | 120.9697 | 43.441 |
| 99,000 | baseline_b | 1396.0099 | 2.1521 | 86.9928 | 114.7870 | 122.7515 | 43.418 |
| 99,000 | candidate | 1579.2998 | 2.0990 | 111.9379 | 135.9743 | 121.3288 | 43.434 |

| Starting receipts | Comparison | Total ratio | Append p99 ratio | Append p50 ratio | Max ratio | Reopen ratio | Peak working-set ratio |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | candidate_a | 1.0384 | 0.8408 | 0.9544 | 1.0358 | 0.3448 | 1.0806 |
| 0 | identity_b_a | 0.9394 | 0.8818 | 0.9789 | 0.8908 | 0.9903 | 1.0138 |
| 0 | candidate_b_diagnostic | 1.0824 | 1.1339 | 0.9750 | 1.3926 | 0.3545 | 1.0626 |
| 50,000 | candidate_a | 1.1436 | 1.2288 | 1.0393 | 1.6516 | 0.9639 | 0.9982 |
| 50,000 | identity_b_a | 1.1686 | 1.2609 | 1.0021 | 1.3216 | 0.9815 | 0.9996 |
| 50,000 | candidate_b_diagnostic | 0.9923 | 0.9745 | 1.0571 | 1.0351 | 0.9789 | 0.9987 |
| 99,000 | candidate_a | 0.9352 | 0.9812 | 0.9990 | 0.7988 | 1.0030 | 0.9993 |
| 99,000 | identity_b_a | 1.0225 | 0.9492 | 0.9945 | 0.9680 | 1.0599 | 0.9995 |
| 99,000 | candidate_b_diagnostic | 1.0001 | 0.9160 | 1.0048 | 0.9190 | 0.9900 | 0.9989 |

| Starting receipts | Speed goals passed | Candidate guards passed | Identity checks passed | Advance |
|---:|---:|---:|---:|---|
| 0 | ❌ 1/2 | ✅ 4/4 | ❌ 4/6 | ❌ |
| 50,000 | ❌ 0/2 | ❌ 3/4 | ❌ 3/6 | ❌ |
| 99,000 | ❌ 0/2 | ✅ 4/4 | ✅ 6/6 | ❌ |

The goals require both charged write time and append p99 to improve at least 10%. Guards permit at most 5% higher append p50 and 10% higher maximum, reopen time and process peak working set. All six B/A metric ratios must stay in 0.90-1.10 per size. Every goal, guard and identity check must pass to advance. At 99,000 receipts the paired charged-time ratio is 0.9352, a measured 6.5% reduction that misses the declared 10% target. At 50,000 it is 1.1436, with p99 1.2288 and maximum 1.6516; these outcomes remain visible. The middle-round 50,000-receipt candidate charged time is **11.2083 times A** and **9.5914 times B**. No best-round selection or competitor switch is made. Calibration failures prevent attributing all differences to the engine change.

The structural result is exact: **seven to four maintenance calls** per 256 appends and **39 to 4 final runs**, plus one large seed run where present. The empty-history cold-reopen paired ratio is 0.3448; its full-process working-set ratio is 1.0806. Larger histories have reopen ratios near 1. This is a scoped local reopening observation, not a write-speed qualification or general capacity result.

Peak working set and peak commit are collected from each retained task-owned process handle after exit. They include setup and verification, rather than isolating compaction allocations. The Windows memory API smoke check succeeded before timing. Microsoft defines [the process memory query](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) and [the peak fields](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters); querying an exited retained handle was verified empirically on this host. Unavailable memory would fail the guard. All 27 counters are available. [Memory helper](benchmarks/compaction-064/process_memory.py), [excluded smoke](benchmarks/compaction-064/native-smoke.json).

✅ **Correctness and recovery:** 78 debug and 78 release Rust tests, formatting and strict default/fault Clippy pass. The full 13-suite qualification checks 4,000 varied SQL cases against each of DuckDB 1.5.6 and SQLite 3.49.1, 56 publication cuts, 22 rejected corruptions, 32 concurrent forced kills, 14 source cuts and eight source kills. The Parquet source pipeline validates 30,000 rows, 300 committed source intervals and 42 DuckDB oracles. Reader checks add 104 manual/concurrent oracles; wide integer JSON, corruption, reopen and exact retry checks pass. [Qualification audit](benchmarks/compaction-064/qualification-audit.json), [full suite logs](benchmarks/compaction-064/qualification-logs/), [raw qualification reports](benchmarks/compaction-064/lab/outputs/kestrel-sql/benchmarks/).

✅ **Wider-merge recovery:** fourteen additional publication cuts exercise a directly seeded 64-run archive, covering seven cut points with process exit and injected I/O failure. Default cold reopen recovers generation 64 and 64 runs before publication, or generation 65 and one run after publication. All 64 original receipt generations, counts/sums, grouped/range oracles and CRCs pass. All fourteen cut stores and their source store remain in the supplemental archive. [Wide-merge results](benchmarks/compaction-064/wide-faults.json).

✅ **Native durability checks:** all 6,912 measured appends, 691,200 appended rows, 81 cold duplicate retries and 97,545,600 CRC-scrubbed bytes pass their driver assertions. All 27 native stores remain preserved. Process cuts on a live filesystem do not qualify physical power loss.

❌ **New DuckDB performance win:** not measured in 064. DuckDB and SQLite are correctness references here. Historical 061 records 60/60 analytical median wins and 10/29 failed service guards; those are separate version/workload results. No PostgreSQL, maximum requests/s, distributed-scale or production-readiness claim follows from this trial.

Posthoc stage counters show that synchronization dominates many runs; for A at 99,000 receipts, catalog encoding contributes 18.33% of summed measured stage time. The fractions include maintenance, omit other work and are not a causal p99 decomposition. All slower samples, checkpoint sizes, cumulative maxima and per-stage histograms are retained. [Posthoc diagnostics](benchmarks/compaction-064/posthoc-stage-diagnostics.json), [next scoped work](benchmarks/compaction-064/NEXT_WORK.md).

The independent source auditor initially failed because Windows cp1252 decoded UTF-8 source. Its original code/error is preserved; explicit UTF-8 repaired only the auditor, which passed without rerunning any database suite. The original qualification JSON also retains an inherited numeric trial label of 61, although version, binaries, harnesses and commands identify 064; the annotation leaves that raw record unchanged. The post-run metadata collector initially assumed an empty process pipeline created a file; the wrapper actually created none. That error and source are preserved, and a structured final check records zero task-owned processes. [Encoding repair](benchmarks/compaction-064/audit-encoding-failure/repair.json), [qualification label note](benchmarks/compaction-064/qualification-metadata-note.json), [process snapshot note](benchmarks/compaction-064/process-snapshot-note.json), [final process check](benchmarks/compaction-064/post-qualification-process-check.json), [metadata failure](benchmarks/compaction-064/final-metadata-failure/).

Before build/timing, 27 old 062 service stores, 32 old 063 service stores and 24 old 063 recovery stores were reclaimed only as duplicate uncompressed copies. All 5,140 files were individually size/CRC/SHA-256 verified against local ZIPs whose digests match their private published assets. This recovers 1,615,720,269 bytes. Older raw reports, source, binaries, failure evidence and full archived stores remain unchanged. Restore prefixes and private links are in [the archive plan](benchmarks/compaction-064/prior-store-archive-plan.json); [completed reclamation](benchmarks/compaction-064/prior-store-archive-result.json).

All surviving qualification fixtures, source, frozen default/fault/native binaries, raw outputs and errors are packaged. The existing successful 32-cycle group-recovery harness removes its cycle stores after validating them; its full raw cycle records and log remain, and **those removed stores are not claimed as archived**. No failure was discarded. Cargo build caches are excluded from evidence; binaries and their source hashes are frozen independently. Builds, audits, packaging and cleanup run outside timed workloads. All task-owned probes stop. The morning report stays frozen. [Reproduction and restoration](benchmarks/compaction-064/REPRODUCE.md), [preservation inventory](benchmarks/compaction-064-preservation.json).

Private immutable [full compaction evidence and stores](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-064-compaction-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-064-compaction-evidence.zip.sha256). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.
