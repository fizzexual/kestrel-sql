# Benchmark history: wins, losses and exact evidence

Latest adaptive code trial: [Adaptive Live collection105](ADAPTIVE_COLLECTION_105.md) implements workload-dependent write collection and passes complete restored correctness. Speed and0.3.17 remain unqualified.

[104 complete native/service rejection and exact restoration](REUSABLE_SYNC_SPEED_104.md): 2,782 lost offers; all ACKs preserved. Supported0.3.16 unchanged; adaptive work is next.


**Latest synchronization candidate:** [103 reusable worker passes correctness and recovery](REUSABLE_SYNC_103.md): 916 current tests, 6 strict lints, 832 coupled cases, 104 publication faults, 26 source faults, 22 corruption rejections and exact restored replay. Speed/adoption remain unqualified; supported 0.3.16 stays unchanged.


**Latest controlled performance:** [102 scoped synchronization speed rejected](PARALLEL_SYNC_SPEED_102.md): 144 native + 144 service cases, 1,872,000 successful offers/zero loss and full restored correctness; native 7 controls/2 guards/1 goal fail, service 1 control/1 goal fail. No adoption; 0.3.16 remains supported.


**Latest synchronization candidate:** [101 scoped overlap passes fresh correctness and recovery](PARALLEL_SYNC_101.md): 682 tests, 576 coupled faults, 72 publication faults, 18 source faults, 22 corruption cases, old formats and exact normal/candidate bytes. Fully restored evidence; speed/adoption remain unqualified and 0.3.16 stays supported.


**Latest matched tracer controls:** [095: stock-trace: unqualified; incremental-trace: unqualified](TRACE_CONTROLS_095.md), all 288 cases and every failure preserved. Diagnostic qualification is separate from an engine speed gain; 0.3.16 stays supported and .17 unqualified.


**Latest recovery milestone:** [094 passes 107 fixed fault cases and 22 corruption rejections](RECLAIM_RECOVERY_094.md), with exact independent restoration. This closes a recovery gap; 093 remains rejected on speed and supported 0.3.16 is unchanged. .17 remains unqualified.


**Latest engine candidate:** [093 incremental reclamation is rejected](INCREMENTAL_RECLAIM_093.md): 2,650 queue drops, five failed A/A checks and missed append goals. All 178,622 ACK batches pass full independent data/CRC audit and exact restoration; lower medians do not qualify a win. Supported 0.3.16 remains unchanged; .17 is unqualified.


**Reclamation measurement milestone:** [092 passes all native phase controls](RECLAIM_PHASES_092.md), 314 tests, both balanced halves and all 72 exact stores. File deletion accounts for about 83% of native reclaim time; this justifies a separate bounded Live cleanup candidate. Diagnostics are qualified in this scope; no engine gain or supported upgrade is claimed. All earlier failures remain preserved; supported 0.3.16 is unchanged.


**Writer diagnostic milestone:** [091 passes all full/half overhead controls](TRACE_CONTROLS_091.md) under unchanged 5% limits with exact 090 artifacts, 1.872 million successful requests, 179,280 reopened ACK batches and 59,760 correlated traced ACKs. Reclamation is the next measured writer target. This qualifies scoped diagnostics, not an engine gain or 0.3.17 release; [090](MAINTENANCE_ISOLATION_090.md) and all earlier failures remain preserved. Supported 0.3.16 is unchanged.

**Fresh D: compact reader comparison:** [085 rejects the new reader](FAST_COMPARE_085.md): 11 speed goals, seven guards and nine A/A checks fail; both balanced halves fail. Full-cohort 99K migration/recovery p99 improve about 12%/14%, while publication tails fail calibrated guards. [084 correctness qualification](FAST_READER_084.md) passes 63 debug/release tests, 195 historical heads, 15 errors, 15 owned kills and 30 corruptions. Supported 0.3.16 remains unchanged.

**Reader CPU diagnostic:** [083 identifies parsing/map lifetime as the main anchor cost](READER_CPU_083.md). All 108 cases and 648 phase windows pass complete ledger checks. Large parse/anchor CPU and wall controls pass in the full cohort and both halves; other diagnostic failures and short CPU windows remain visible. The diagnostic does not override the rejected full-workload candidates.

**Fresh D: loader comparison:** [082 rejects the bounded bulk reader](LOAD_COMPARE_082.md): all 20 reader goals, nine guards and 14 A/A checks fail. Peak process memory falls about 12%, but migration/recovery regress. [081 fresh correctness qualification](RECEIPT_LOAD_081.md) passes 60 debug and 60 release tests, 15 injected errors, 15 owned kills and 30 independent corruptions. Supported 0.3.16 remains unchanged.

**Fresh D: source robustness:** [080 retains large publication gains and fails robustness](SOURCE_ROBUSTNESS_080.md): 108 cases, 6,912 publications and 1,296 opens; three guards and 11 calibration checks fail, as do both balanced halves. [Verified workspace cleanup](WORKSPACE_CUTOVER_2026-10-08.md) frees 52.90 GiB from C: while preserving all Kestrel history on D:. Shared Codex fresh-profile reset is separate and not yet executed.

**Historical 079 source-state comparison:** [079 publication gains and failed guards](SOURCE_COMPARE_079.md) measures 37.7%/56.6% lower large-history publication totals with stable controls. Only three of four goals are calibrated; eight guards and 19 A/A checks fail. Full qualification fails; supported 0.3.16 stays unchanged. All prior reports and failures remain accessible.

**Prior source-state qualification:** [078 bounded source positions](SOURCE_STATE_078.md) passes 57 debug/release tests, 15 injected errors, 15 owned kills and 30 independently corrupted fixtures. It removes whole-ledger cloning from new source publication; all 201 history files remain byte-identical. No fresh speed measurement or engine adoption. [077 measured recovery gains and failed guards](RECOVERY_COMPARE_077.md) remain visible.

**Fresh recovery comparison:** [077 anchor recovery benchmark](RECOVERY_COMPARE_077.md) measures about 51–52% lower large-history anchor medians with stable controls. All four goals pass; four guards and two A/A checks fail. Full histories and regressions remain preserved. Supported 0.3.16 stays unchanged; [075 failed CAT4 comparison](HYBRID_CYCLES_075.md) is not superseded.

**Latest recovery qualification:** [076 validated anchor reuse](ANCHOR_REUSE_076.md) passes 49 debug/release tests, 15 errors, 15 owned kills and 30 independent corruption cases. Anchor-terminated recovery reads/parses once; no fresh latency comparison yet. Publication bytes are unchanged. Supported 0.3.16 stays unchanged; [075 failed performance guards](HYBRID_CYCLES_075.md) remain visible.

**Latest hybrid benchmark:** [075 full-cycle metadata trial](HYBRID_CYCLES_075.md) passes four large-history goals but fails nine guards and ten identical-control checks. Retained-history bytes fall about 67%; publication p50 and recovery regress. All raw cases remain visible. Supported 0.3.16 stays unchanged; [074 correctness qualification](HYBRID_RECEIPTS_074.md) and [073 failed page trial](RECEIPT_CYCLES_073.md) remain preserved.

**Latest hybrid qualification:** [074 passes metadata correctness/error/kill checks](HYBRID_RECEIPTS_074.md). Forty debug/release tests, 15 injected errors, 15 owned process kills and 21 independent corruption cases pass. Import/ordinary deltas sync one file; speed is not measured. Supported 0.3.16 stays unchanged; [073 performance failures remain visible](RECEIPT_CYCLES_073.md).

**Latest receipt-cycle benchmark:** [073 passes large metadata goals but fails adoption](RECEIPT_CYCLES_073.md). All 54 cases/3,456 publications/648 recoveries pass logical-history checks. At 50K matched publication time falls 10.8%, but p50/migration/small-store regressions and 11 guards/six A-A failures reject the candidate. Retained evidence bytes shrink; current reachable page metadata is about 10% larger. Supported 0.3.16 stays unchanged.

**Latest structural model:** [072 preserves full retry/source history across actual edits and interrupted writes](RECEIPT_PAGES_072.md). 18 debug/release tests, 73 full-history oracle checks, seven error cuts, seven process kills and 12 malformed-file cases pass. Large checkpoint bytes fall, normal delta bytes and migration grow; no new speed benchmark or engine promotion. [071 timings and ordering correction remain visible](COMPRESSION_071.md).

**Latest checkpoint model and benchmark correction:** [071 uses verified balanced order; fast Zstandard still fails adoption gates](COMPRESSION_071.md). All 54 cases and 648 frames are preserved. Read the [069/070 order correction](MODEL_ORDER_AUDIT_071.md): their size rotation cancelled variant rotation. Original reports/raw evidence remain unchanged. In 071, large bytes fall about 46%, but two goals, five guards and four A/A checks fail. Supported 0.3.16 remains unchanged.

**Latest checkpoint model:** [070 Zstandard level 1 cuts stored bytes by about 70% but fails publication speed gates](COMPRESSION_070.md). All 36 cases and 432 frames are preserved. Large charged totals are 1.1501x/1.2058x raw; two goals, four guards and five A/A checks fail. Twelve native debug/release tests and all native/Python/Arrow byte checks pass. Model rejected; supported 0.3.16 remains unchanged.

**Latest checkpoint compression model:** [069 saves 62.8% of stored large-checkpoint bytes but fails paid-latency gates](COMPRESSION_069.md). All 36 cases and 432 frames are preserved. Large publication totals are 1.71x/1.89x raw; two goals, six guards and three A/A checks fail. Exact native/Python decoding and eight debug/release tests pass. Model rejected; no SQL engine edit or supported promotion. 0.3.16 remains supported.

**Latest publication diagnostics:** [068 identifies individual slow publication stages](TRACE_068.md). An opt-in one-slot tracer on the exact released core passes 80 debug/release tests and full correctness/recovery. All six diagnostic stores, six byte-equivalence stores and 32 group-kill stores are retained. No speedup or competitor comparison, overhead qualification, physical-cause claim or supported promotion. Supported 0.3.16 remains unchanged.

**Latest engine buffer trial:** [067 bounds reusable catalog memory](BUFFER_067.md). Large-history catalog encoding takes 17.1%/19.8% less time; six memory guards pass. All 54 native cases and all 32 validated group-kill stores are preserved. Failures: 1 speed goal, 4 latency guards, 11 identical-baseline checks. Full correctness and exact released/candidate archive bytes pass. No service advance or supported promotion; 0.3.16 remains supported.

**Latest encoder profiles:** [065/066 isolate catalog-buffer allocation](ENCODER_PROFILES_065_066.md). Separate twelve-round replication passes 43/43 checks and reduces fixed-input encoding time by 21.1%/22.8% on large checkpoints. Original calibration failure remains visible. These are CPU models; supported 0.3.16 and all database results remain unchanged.

**Latest compaction trial:** [064 increases bounded merge fan-in](COMPACTION_064.md). 5/6 native speed goals, 1/12 candidate guards and 5/18 identical-baseline checks fail. Correctness/recovery pass, including fourteen wider-merge cuts. No service advance or supported promotion; 0.3.16 and all earlier results remain unchanged.

**Latest batching experiment:** [063 tests current released 0/1/4 ms options with identical zero-delay controls](BATCHING_063.md). 4/10 identity checks and 6/26 option criteria fail. All previous native gains and service failures remain preserved. Supported 0.3.16 and its zero-delay default are unchanged.

**Latest service calibration:** [062 compares identical released binaries and unchanged clean core 061](SERVICE_CALIBRATION_062.md). 3/14 A/A tolerance checks fail; 2/14 candidate/A guards fail. Original 061 native gains, full DuckDB matrix and all ten service failures remain preserved. No engine change or supported promotion.

**Latest clean core development:** [061 ports the parser gain independently of SDK 058/060](CORE_READ_PATH_061.md). Native range medians 5.6 to 2.7 microseconds; 60/60 fresh DuckDB median wins, 0/60 failed native guards, 10/29 failed service guards. 77 tests per mode and full correctness/recovery gates pass. Supported 0.3.16 is unchanged.

**Latest read-path development:** [060 reproduces roughly 50% shorter native range queries and 28–29% shorter parsing](READ_PATH_060.md). 82 tests per mode, 4,000 SQL cases per reference, 42 fault/retry stores and 18 read-service cases pass. Network p99 has no consistent win; prior write-tail failures remain. Supported 0.3.16 is unchanged.

**Latest service qualification:** [059 retains SDK gains and rejects nine regression criteria](SERVICE_GUARDS_059.md). All 36 cold checks pass; three current minute runs have zero loss, while overload losses and slower tails remain. The disk stop, original 20 cases and resumed-only 16 cases are preserved. Supported 0.3.16 is unchanged.

**Latest SDK development trial:** [058 adds machine-readable ingestion outcomes](ERROR_CONTRACT_TRIAL_058.md). 82 debug/release tests, 42 fault/reopen cases and seven paired guards pass; slower samples and driver failures remain visible. No speed-up or supported engine release is claimed; 0.3.16 is unchanged.

**Latest storage model:** [057 rejects advance zero filling after charging initialization](PUBLICATION_057.md), with a verified standalone Cargo reproduction. [Adoption assessment](ADOPTION_STATUS.md) explains the current case for Kestrel alongside PostgreSQL. No SQL engine upgrade; supported 0.3.16 and every earlier result remain unchanged.

**Morning report, October 7:** [Bulgarian before/after, wins/losses, recovery and every failed trial](OVERNIGHT_2026-10-07.md). [056 tests a persistent-file primitive and fails two hypothesis checks](PUBLICATION_056.md); it changes no SQL engine. Supported 0.3.16 and all earlier releases remain unchanged.

**Latest CAT6 service qualification:** [055 preserves native gains but fails write-tail and zero-loss service gates](SERVICE_TRIAL_055.md). [054 keeps all ten native pairs and adds 88 debug passes](PUBLICATION_054.md). The disk-space failure and resumed-only missing tests remain visible; supported 0.3.16 is unchanged.

**Latest compact-receipt trial:** [053 halves checkpoint metadata and improves native tails, but fails the p50 guard](TRIAL_053.md). Full correctness/migration checks pass; all slower rounds and raw evidence remain visible. Supported 0.3.16 is unchanged.

**Latest native publication work:** [051 measured receipt-checkpoint stalls](PUBLICATION_051.md) and [052 file-sizing experiment rejected by all four gates](TRIAL_052.md). Raw results, slower rounds and failure evidence remain accessible; supported 0.3.16 is unchanged.

**Fresh isolated 050 service results:** [all 36 paired cases, wins/losses, raw samples and recovery audit](SERVICE_TRIAL_050.md). Supported 0.3.16 remains unchanged; older measurements and rejected trials remain visible.

**Verified development hardening 050:** [CAT5 restore identity fix, failing/passing regressions and full recovery checks](TRIAL_050.md). Supported 0.3.16 remains unchanged; fresh performance qualification is pending.

**Unreleased trial 049:** [retained-handle service measurements and recovery evidence](TRIAL_049.md). Supported 0.3.16 remains unchanged; all rounds, failures and raw data are preserved.

**Unreleased storage trial 048:** [paired service results, failed gates and full recovery evidence](TRIAL_048.md) test a single synchronized generation file. Supported 0.3.16 remains unchanged; all baseline, slower and failed trial evidence is preserved.

[Latest package: 0.3.16](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16) | [All release downloads](https://github.com/fizzexual/kestrel-sql/releases) | [Raw reports and samples](benchmarks/) | [Current qualification](verification.json)

The repository is private. Every packaged snapshot has its own Git tag and release download. Older archives are immutable; the current tree keeps earlier reports, raw samples, baselines and rejected experiments. Historical measurements are labelled by the version actually tested. A later release does not turn an old result into a fresh benchmark.

## Start here

| Question | Evidence |
|---|---|
| Where did Kestrel beat another database? | [Repeated six-engine comparison](PERFORMANCE_031.md), [100M-row wins and losses](SCALE.md) |
| What is the fresh 0.3.16 service result? | [52-case qualification, read/write tails and six-engine wins/losses](SERVICE_047.md), [all raw evidence](benchmarks/service-047-audit.json) |
| Where did it lose or drop work? | [Original hard tests](HARD_TESTS.md), [current 0.3.16 service failures](SERVICE_047.md), [earlier live-service failures](V03_RESULTS.md), [0.3.6 controls](PERFORMANCE_036.md), [0.3.7 write stalls](PERFORMANCE_037.md) |
| What is faster today? | [Packed medium cache and current matrix](PERFORMANCE_046.md), [previous bounded reader reuse](PERFORMANCE_045.md), [previous adaptive sparse SUM controls](PERFORMANCE_044.md), [previous dense SUM controls](PERFORMANCE_043.md), [previous medium-cache controls](PERFORMANCE_042.md), [previous seeded-cache controls](PERFORMANCE_041.md), [previous scan controls](PERFORMANCE_040.md), [previous sparse grouping](PERFORMANCE_039.md), [previous 100M-row comparison](PERFORMANCE_038.md), [Immutable embedded retry reuse](PERFORMANCE_036.md), [filtered scan improvement](PERFORMANCE_032.md), [receipt metadata reduction](PERFORMANCE_033.md) |
| What can a pipeline rely on locally? | [Source checkpoint contract](SOURCE_INGEST.md), [replay/backfill portfolio](PORTFOLIO.md), [0.3.7 recovery evidence](PERFORMANCE_037.md) |
| Can this replace a production general-purpose SQL database? | [SQL/API boundaries and release gates](README.md), [executed capability checks](HARD_TESTS.md) |
| What is the next storage hypothesis? | [I/O primitive measurements](benchmarks/sync-037-io-comparison.json), [rejected parallel-sync audit](benchmarks/sync-037-io-audit.json); these are not database benchmarks |

The [047 qualification](SERVICE_047.md) was added after the 0.3.16 package was released. It uses identical source/binaries and creates no new software release; historical ZIPs and assets remain unchanged.

## Release-by-release evidence

| Snapshot | Main change / experiment | Human-readable report | Raw evidence |
|---|---|---|---|
| [0.1.0](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.1.0) | Initial RAM engine and aggregate precomputation | [Initial benchmark](BENCHMARK.md) | [Initial timings](benchmarks/results.json) |
| [0.2.0](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.2.0) | Disk storage, 100M rows, real taxi-data pipeline | [Scale and tradeoffs](SCALE.md), [portfolio](PORTFOLIO.md) | [Random windows](benchmarks/random-window-results.json), [fixed matrix](benchmarks/large-results.json), [NYC results](benchmarks/nyc-results.json) |
| [Stress-tested 0.2.0](https://github.com/fizzexual/kestrel-sql/releases/tag/stress-tested-0.2.0) | Six engines, 66 cases; mixed-write losses exposed | [Hard tests](HARD_TESTS.md) | [Stress runs](benchmarks/stress-results.json), [sample audit](benchmarks/stress-audit.json), [capabilities](benchmarks/capability-results.json) |
| [0.3.0](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.0) | Immutable live snapshots, receipts, group publication | [Live ingestion results](V03_RESULTS.md) | [Final live sweep](benchmarks/stress-v03-release.json), [retained earlier runs](benchmarks/stress-v03-results.json) |
| [0.3.1](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.1) | Receipt-copy removal, cheaper compaction, stage profiling | [Repeated comparisons](PERFORMANCE_031.md) | [Audit](benchmarks/perf-031-audit.json), [all files](benchmarks/) |
| [0.3.2](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.2) | Reusable page buffers and typed scan reductions | [Scan gains and service losses](PERFORMANCE_032.md) | [Stage profiles](benchmarks/perf-032-profile.json), [audit](benchmarks/perf-032-audit.json) |
| [0.3.3](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.3) | Bounded receipt deltas/checkpoints; 96.86% fewer catalog bytes | [Publication measurements](PERFORMANCE_033.md) | [Matched publication runs](benchmarks/publication-033-paired.json), [faults/corruptions](benchmarks/publication-033-faults.json), [audit](benchmarks/perf-033-audit.json) |
| [0.3.4](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.4) | Optional 0/2/8/20 ms coalescing; zero-delay default retained | [Policy comparisons](PERFORMANCE_034.md) | [Audit and all controls](benchmarks/perf-034-audit.json) |
| [0.3.5](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.5) | Opt-in confirmed retries; losing always-on trial preserved | [Retry gains and write losses](PERFORMANCE_035.md) | [Audit](benchmarks/retry-035-audit.json), [trial sources](benchmarks/trial-0.3.5-source/), [trial harness](benchmarks/trial-035-harness/) |
| [0.3.6](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.6) | Immutable prepared input; confirmed retry reuse, zero new rows during timing | [Embedded and ordinary controls](PERFORMANCE_036.md) | [Embedded runs](benchmarks/prepared-036-direct.json), [open-loop controls](benchmarks/prepared-036-write-controls.json), [audit](benchmarks/prepared-036-audit.json) |
| [0.3.7](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.7) | Output and source resume position in one durable receipt | [Contract and cost measurements](PERFORMANCE_037.md) | [Comparisons](benchmarks/source-037-comparison.json), [faults/kills](benchmarks/source-037-faults.json), [Parquet replay](portfolio/source-pipeline-037-results.json), [audit](benchmarks/source-037-audit.json) |
| [0.3.8](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.8) | Bounded adaptive integer grouping; 1M/10M/100M and real-data comparisons | [Every before/after and win/loss](PERFORMANCE_038.md) | [Current audit](benchmarks/group-038-audit.json), [initial trial and fixture correction](benchmarks/group-038-cell-trial-audit.json) |
| [0.3.9](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.9) | Wider bounded arrays, typed sparse reductions, adaptive tagged lookup cache; first-cache penalties preserved | [Current grouping matrix](PERFORMANCE_039.md) | [All 45 shapes and controls](benchmarks/group-039-audit.json), [intermediate regressions](benchmarks/trial-039-first-cache/trial-audit.json) |
| [0.3.10](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.10) | Direct first-filter selection; rejected outlining trial preserved | [Current scans and every matrix loss](PERFORMANCE_040.md) | [Scan audit and all 45 shapes](benchmarks/scan-040-audit.json), [rejected trial](benchmarks/trial-040-noinline/proof.json) |
| [0.3.11](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.11) | Per-query sparse-cache indexing; exact tags and adaptive fallback | [Current pairs and every win/loss](PERFORMANCE_041.md) | [55-shape audit](benchmarks/cache-041-audit.json), [preserved trial](benchmarks/trial-041-seeded-multiply/proof.json) |
| [0.3.12](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.12) | Reuse-triggered medium sparse cache; deferred allocation and bounded fallback | [Current pairs and every win/loss](PERFORMANCE_042.md) | [60-shape audit](benchmarks/cache-042-audit.json), [rejected eager trial](benchmarks/trial-042-reuse-gated-large/proof.json), [deferred trial](benchmarks/trial-042-deferred-large/proof.json) |
| [0.3.13](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.13) | Fuse exact counts and shared dense SUM/AVG in one selected-row pass | [10M/100M pairs and every win/loss](PERFORMANCE_043.md) | [60-shape audit](benchmarks/dense-043-audit.json), [preserved development trial](benchmarks/trial-043-fused-shared-sum/proof.json), [dense SQL oracles](benchmarks/dense-043-differential.json) |
| [0.3.14](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.14) | Skip cache-hit stores; fuse shared SUM only in the small-cache kernel | [Pairs and every win/loss](PERFORMANCE_044.md) | [60-shape audit](benchmarks/sparse-044-audit.json), [rejected enum fusion](benchmarks/sparse-044-rejected-enum-fusion.json), [unselected wider fusion](benchmarks/sparse-044-rejected-wide-typed-fusion.json), [focused sparse SQL oracles](benchmarks/sparse-044-differential.json) |
| [0.3.15](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.15) | Exclusively owned per-segment stream reuse; 128 retained idle files | [Pairs and every win/loss](PERFORMANCE_045.md) | [60-shape audit](benchmarks/reader-045-audit.json), [unselected offset trial](benchmarks/reader-045-offset-unselected.json), [concurrent reuse/corruption oracles](benchmarks/reader-045-verification.json) |
| [0.3.16](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16) | Exact packed medium tags: 384 to 256 KiB, same budgets and fallback | [Pairs and every win/loss](PERFORMANCE_046.md) | [60-shape audit](benchmarks/packed-046-audit.json), [predeclared criteria](benchmarks/packed-046-trial-policy.json), [both build failures](benchmarks/packed-046-build-repairs.json) |

Each report links its exact raw inputs and samples. Gzipped JSONL sample files remain in their named directories under `benchmarks`; they are downloadable from GitHub and included in the corresponding ZIP. Sample counts, losses and percentiles must be assessed together.

## How to read wins and losses

- Aggregate indexes accelerate eligible ranges; the reference engines were not given equivalent materialized aggregate views. This is a measured design tradeoff, not a universal database ranking.
- Req/s in paced workloads is capped by the offered rate. Successful-request p99 does not include failed offers; every report exposes losses separately.
- Prepared retry calls acknowledge existing data. They insert zero new rows in the timed embedded loop and cannot be compared with network SQL throughput.
- Shared Windows desktop timings vary. Use paired builds within a run; do not divide unrelated release measurements to invent a speedup.
- The most recent complete six-engine comparison used 0.3.1. Current 0.3.7 source-checkpoint evidence does not refresh that ranking.
- Publication errors and process kills are local live-filesystem tests. Physical power loss, replication, long endurance and Facebook-scale qualification remain untested.

## Preserved unsuccessful evidence

The reports explicitly retain the initial overload failures, slow live runs, the rejected always-enabled retry index, the rejected weak hashing trial, setup/profiling mistakes, and the latest parallel-sync diagnostic. Baseline source and binaries are under `benchmarks/baseline-*` and `bin/baseline-*`; rejected source is under `benchmarks/trial-*`. Earlier proof files are `verification-v*.json`.

[Release asset hashes and original package dates](release-history.json) identify the exact downloads. Git tags point to their actual historical snapshot rather than the current source tree. Benchmark execution stays local; repository GitHub Actions is disabled. No deployment is configured.

[Publication verification](repository-publication.json) records all uploaded assets, server SHA-256 checks and matching historical tag commits.

## Fresh D: service check 086 — October 8, 2026

[54-case service check](SERVICE_D_086.md): 900,000/900,000 operations, zero losses and all 45,072 acknowledged batches survive reopen. Full A/A passes, but write-heavy overall/append p99 regress by paired 15.75%/24.32%; full and first-block qualification fail. No supported upgrade. [0.3.17 release target and remaining gates](RELEASE_TARGET_0_3_17.md). All previous results remain preserved.

## Service-writer diagnostics087 — October8,2026

[Bounded optional writer tracing](WRITER_TRACE_087.md): fresh correctness/byte/protocol qualification in both isolated cores,90 native commands and32 SQLite comparisons. Initial extra-field validation failure and all setup/audit stops preserved. No overhead/speed claim or supported upgrade.086 service regressions remain release blockers.

## Controlled writer overhead 088 — October 8, 2026

[Fresh four-family qualification](WRITER_OVERHEAD_088.md): 288 cases, 2.88 million successful offers and 147,024 reopened ACK batches. Fixed full/two-half checks fail 15 A/A and 12 candidate criteria; six candidate failures are calibrated. Default released-core write overall p99 regresses paired 23.4%. Read/memory/rate/loss checks pass. All slow cases and raw evidence retained; no low-overhead or supported release claim.

## Controlled default-build investigation 089 — October 8, 2026

[Three matched-toolchain source/build controls](BUILD_COMPARE_089.md): 464 native test executions, eight byte-equivalent stores, 32 cross-reopens, 32 SQLite comparisons and four wire/setup variants pass. All 216 timed cases, 2.16 million offers and 110,268 reopened ACK batches pass correctness with zero loss. No candidate guard fails, but eight of 117 A/A checks fail across six of nine required scopes; every family remains unqualified overall. Original rebuild, version-only and feature-disabled diagnostic source comparisons do not establish exclusive causality, speed gains, tracer overhead, competitor wins or a release. Complete raw evidence/restored audit and post-run reporting failure are preserved; 088 remains unchanged.

## Maintenance source isolation 090 — October 8, 2026

[Corrective source isolation](MAINTENANCE_ISOLATION_090.md) restores original feature-disabled maintenance statements while preserving traced behavior.322 Native test executions/five lint modes and 104 untimed commands pass byte/cross-reopen/SQLite/named/concurrent/controlled unknown-outcome/old-format/wire checks. All 144 service cases, 1.872 million requests and 179,280 reopened ACK batches pass correctness. Default compatibility passes full/both halves; complete tracing qualification fails two write-overall A/A half controls, with 0 candidate failures. All stalls, failed preparation and complete raw/restored evidence remain preserved. Supported 0.3.16 is unchanged; no engine gain/competitor win/release claim.


## Isolated asynchronous reclamation 096

[ASYNC_RECLAIM_096.md](ASYNC_RECLAIM_096.md): actual bounded owned deletion worker;693 native tests/four lints,40 fault and8 concurrent cases, exact ACK/CRC/ownership/format/retry/restoration pass. All first failures and partial stores retained. No performance timing, speed/adoption/competitor/release claim;0.3.16 supported,0.3.17 unqualified.


## Coupled worker/publication recovery 097

[COUPLED_RECOVERY_097.md](COUPLED_RECOVERY_097.md): 448 actual coupled worker error/exit and publication/compaction schedules pass; 370 fresh tests/four lints, complete ACK/ambiguous receipt/CRC/ownership checks and exact restoration. Every failed controller/preparation remains. Speed unmeasured; 0.3.16 supported and .17 unqualified.


## Normal owned async service 098

[ASYNC_SERVICE_098.md](ASYNC_SERVICE_098.md): all 1,872,000 offers and 179,280 ACKs pass independent data and graceful completion checks, but second-half append calibration and improvement miss the fixed gates. The entire 144-case result and all failures were restored exactly; unqualified, no adoption, supported 0.3.16 unchanged and .17 pending.


## Retirement diagnostic 099

[RETIREMENT_099.md](RETIREMENT_099.md): all 144 native cases, data and lifecycle checks pass, but four baseline repeatability gates fail. The approximately 1.1 ms retirement signal remains unqualified; no handle offload or speed adoption. All raw and failed attempts are restored exactly, supported 0.3.16 stays unchanged and .17 is pending.


## Append publication diagnostic 100

[PUBLICATION_COST_100.md](PUBLICATION_COST_100.md): all 144 cases, historical/current data and lifecycle checks pass, but one named p99 repeatability gate fails. All stages, stalls and unchanged decisions are restored exactly. Unqualified, no adoption; supported 0.3.16 stays unchanged and .17 is pending. A separate static proof retains qualified 091 as the basis for a future code hypothesis.


## October 9, 2026 — verified local storage cleanup

[Storage cleanup](STORAGE_CLEANUP_20261009.md) removes 49 redundant top-level ZIP copies (8.97 GiB) only after full private GitHub download/hash verification. Every original benchmark failure/raw store and all newer unbacked-up experiments remain. No performance result or release status changes.
