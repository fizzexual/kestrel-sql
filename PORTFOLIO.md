# KestrelSQL: data-engineering portfolio case study

**Latest measured source-state comparison:** [079 publication gains and failed guards](SOURCE_COMPARE_079.md) measures37.7%/56.6% lower large-history publication totals with stable controls. Only3/4 goals are calibrated;8 guards and19 A/A checks fail. Full qualification fails; supported0.3.16 stays unchanged. All prior reports and failures remain accessible.

**Latest source-state qualification:** [078 bounded source positions](SOURCE_STATE_078.md) passes 57 debug/release tests, 15 injected errors, 15 owned kills and 30 independently corrupted fixtures. It removes whole-ledger cloning from new source publication; all 201 history files remain byte-identical. No fresh speed measurement or engine adoption. [077 measured recovery gains and failed guards](RECOVERY_COMPARE_077.md) remain visible.

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

**Fresh post-release service qualification:** [SERVICE_047.md](SERVICE_047.md) retains 52 million-row cases and 1,327,600 offered operations on unchanged 0.3.16. In three current six-engine rounds, Kestrel had 3/5 mixed-p99 median wins, 4/5 read-p99 wins and 2/5 append-p99 wins. Its failed 60-second soak and inconsistent batching trials remain visible; these results establish no engine upgrade or production service guarantee.


The [0.3.16 packed medium-cache case study](PERFORMANCE_046.md) reduces tagged lookup memory by one-third, uses criteria declared before timing, preserves compile/footprint failures and retains every slower control. Independent zero/signed-key collision oracles and current durable retry/crash evidence support the bounded change.

The [0.3.15 bounded reader reuse case study](PERFORMANCE_045.md) profiles fragmented query overhead, preserves an offset-only experiment with inconclusive scan gains, and selects exclusive file reuse under an explicit idle-handle budget. It verifies eight-client exact results, beyond-i64 sums, corruption after warming, fresh scrubs, snapshot retirement and durable retries. All 60 current shapes, losses and slower controls remain visible; this is local experimental evidence.

The [0.3.14 adaptive sparse-kernel case study](PERFORMANCE_044.md) retains two unsuccessful wider-fusion trials, then selects a small-cache kernel with guarded wider fallback. It independently verifies signed wide shared SUM/AVG across cache modes and durable retry/crash behavior. The final release retains 60 fresh shapes, 74 Rust tests and 4,000 SQL cases against each reference.

The [0.3.13 dense-reduction case study](PERFORMANCE_043.md) follows a measured 10M-row aggregation bottleneck through stage profiling, a preserved development trial and separately rebuilt 10M/100M comparisons. Independent oracles cover exact counts, signed extremes, shared AVG, repeated SUM and beyond-i64 JSON, alongside durable retry/crash and Parquet source workflows. It retains 60 fresh query shapes, 73 Rust tests and 3,400 SQL comparisons against each reference.

The [0.3.12 medium-cache case study](PERFORMANCE_042.md) profiles a remaining wide-key aggregation loss, retains a tiny-query regression, and verifies deferred allocation with irregular signed keys, adaptive memory bounds and exact wide sums. It includes 60 fresh shapes, 72 Rust tests and 2,800 SQL comparisons against each reference. Prior failures and unsuccessful experiments remain accessible.

The [0.3.11 cache case study](PERFORMANCE_041.md) traces a grouping loss to repeated hash mapping, tests per-query cache indexing, constructs actual seed-specific collisions, and adds Fibonacci/power-of-two patterns. It retains 55 fresh shapes, 70 Rust tests, 2,200 SQL comparisons against each reference and current durability checks. Existing service failures and all benchmark losses stay visible.


The [0.3.10 filter case study](PERFORMANCE_040.md) follows a measured scan regression through stage profiling, an unsuccessful outlining trial, direct first-filter selection and final 1M/100M controls. All 70 Rust tests and 1,600 SQL comparisons against each reference pass, alongside current retry/crash/source checks. The full matrix retains 29 wins/1 loss and 11 wins/4 losses on the extra shapes. Existing requests/s failures remain visible.


The [0.3.9 grouping case study](PERFORMANCE_039.md) profiles sparse/hash reduction costs, expands bounded dense execution and validates an adaptive tagged lookup cache. The matched comparison has 22 median DuckDB wins and 8 losses; 15 additional stress shapes have 11 wins and 4 losses. All 69 Rust tests, 1,000 independent SQL cases and current crash/source replay checks pass. Intermediate cache penalties and remaining service failures remain accessible.


## Project statement

Built a Rust embedded analytics engine and Python/SQL pipelines to investigate fast exact aggregates over append-only events. The archive persists 100 million rows, automatically maintains sparse aggregate indexes, accepts overlapping late batches and keeps raw values on disk. Version 0.3 adds concurrent immutable read views, durable batch receipts, group publication and bounded small-run compaction. Query results are checked against mature SQL engines rather than inferred from timing alone.

The portfolio demonstrates SQL, source lineage, data modeling, quality controls, reconciliation, ingestion, persistence, and performance measurement. It is a substantial project for interviews; it cannot guarantee a hiring outcome or establish production operating experience.

## Evidence a reviewer can inspect

| Evidence | Result | Where |
|---|---|---|
| Scale | 100M persisted rows; 2.4 GB raw integer payload | [SCALE.md](SCALE.md) |
| Process memory | 30.8 MiB measured peak for the ordered scale process, excluding OS file cache | [large-results.json](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/large-results.json) |
| Random window latency | 2.095 ms Kestrel median vs 165.798 ms DuckDB; 31 fresh windows at 100M rows | [random-window-results.json](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/random-window-results.json) |
| Public source pipeline | 3,475,226 input / 3,475,077 accepted / 149 rejected | [nyc-results.json](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/nyc-results.json) |
| Independent SQL checks | 500 Archive cases against each of SQLite and DuckDB; 124 scale windows against DuckDB | [archive-verification.json](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/archive-verification.json) |
| Recovery and integrity | Metadata/page CRC, atomic catalog publication, lock ownership, corruption/pending-file regression tests | [tests/archive.rs](tests/archive.rs) |
| Adaptive integer grouping | Fresh 100M-row full aggregate grouping: 5.504 s to 1.694 s; all shapes/controls/losses retained | [PERFORMANCE_038.md](PERFORMANCE_038.md) |
| Engineering checks | 63 Rust tests pass in debug and release for 0.3.8; format and Clippy pass | [verification.json](verification.json) |
| Retry availability | Opt-in confirmed retries validate independently of writer queueing; original receipts, bounded lookup memory, pending-ID races and fail-closed health; unsuccessful always-on trial preserved | [PERFORMANCE_035.md](PERFORMANCE_035.md) |
| Coalescing policy | Same-binary 0/2/8 ms comparisons, collection diagnostics, explicit latency/loss tradeoffs and zero-delay default | [PERFORMANCE_034.md](PERFORMANCE_034.md) |
| Receipt publication | 96.86% fewer catalog bytes in three alternating 50K-ID comparisons; bounded recovery and exact publication-cut checks | [PERFORMANCE_033.md](PERFORMANCE_033.md) |
| Analytical SQL | Validated 248 category/day rows: dimension join, complete calendar, LAG, and ranking | [gold_analysis.sql](portfolio/gold_analysis.sql), [checks](portfolio/gold-verification.json) |
| Historical concurrent stress | Six engines, 66 cases, 933,600 offered requests, 64 clients; exact reconciliation | [HARD_TESTS.md](HARD_TESTS.md) |
| Current live ingestion | Snapshots, group commits, identified retries, bounded cache and compaction; repeated comparisons with retained failures | [PERFORMANCE_035.md](PERFORMANCE_035.md) |
| Replay/backfill pipeline | 30,000 Parquet rows with 8 ms policy; both sources replayed without duplication; 42 exact SQL checks | [live-pipeline-035-results.json](portfolio/live-pipeline-035-results.json) |
| Actual Archive crashes | 32 concurrent process kills across 0/2/8/20 ms policies; whole batches, original receipt generations and no lost acknowledged batches | [group-035-recovery.json](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/group-035-recovery.json) |
| Research decisions | Primary papers and official docs connect architecture decisions to explicit future experiment gates | [RESEARCH.md](RESEARCH.md) |

The 0.2 hard tests exposed a significant limit: Kestrel completed 881.12 requests/s at 2,000 offered mixed requests/s, with 611.30 ms successful-request p99 and 53.94% loss/unexecuted work. Version 0.3 addresses writer exclusion, repeated boundary decoding and small-run growth. Version 0.3.1 adds stage profiling, faster exact retries, buffered durable writes and cheaper compaction input reads. [Historical 0.3.1 results](PERFORMANCE_031.md) disclose repeated comparisons, intermediate regressions and remaining failures; [0.3 results](V03_RESULTS.md) preserve the earlier evidence. [Fresh 0.3.16 service qualification](SERVICE_047.md) separates read/write percentiles and retains a failed minute-long soak. Durable-write tail latency remains a production qualification gate. Archive also lacks raw point retrieval, joins and transactional updates. Explain those boundaries and retain failed runs when presenting the project.

## Data model and pipeline

The immutable bronze source is January 2025 yellow taxi Parquet plus the published TLC zone lookup. Download size and SHA-256 values identify the exact source files. That pipeline creates a fresh run directory per rebuild. The separate 0.3 Parquet demonstration uses durable source-hash/chunk IDs for incremental archive retries; this is batch idempotency, not an end-to-end exactly-once contract.

Silver has one row per accepted source record with three typed columns: `ts` (UTC epoch seconds), `value` (integer total-charge cents), and `device` (pickup LocationID). The zone lookup is a small dimension joined by LocationID in DuckDB. Source records have no engine-enforced unique trip key; the pipeline preserves duplicates rather than inventing deduplication semantics.

Quality rules reject pickups outside January 2025, invalid/over-72-hour durations, missing/nonfinite/excessive amounts, and unknown pickup zones. These are explicit project policies. Rule counts can overlap. Rejected rows remain recoverable from the retained source using the recorded predicates; there is no separately published quarantine table in this release. Negative charges are retained as possible adjustments. Money is converted through a fixed-scale decimal before integer storage. New York local timestamps are normalized to UTC; the chosen month has no daylight-saving transition, so DST ambiguity is not independently tested.

Gold daily trip counts and total charged cents reconcile to silver. [nyc-daily-metrics.csv](portfolio/nyc-daily-metrics.csv) contains the 31 daily aggregates. The extra analytical SQL joins the zone dimension and uses window functions to compute day-to-day trip changes and rankings across the lookup's eight borough categories (including special/unknown categories). A complete calendar spine inserts zero-event days, so LAG compares consecutive calendar days. The 248 output rows reconcile to silver by day and in total; independent checks validate rankings and zone-key uniqueness. Joins and window functions execute in DuckDB in the pipeline; Kestrel's supported SQL subset is documented separately.

The importer streams batches into immutable sorted column segments and verifies every persisted page. Independent queries reconcile the month, day, hour, selected zone, and grouped zone outputs. All five matched the reference. Sources: [NYC TLC datasets](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) and [field dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).

## Design decision to explain in interviews

The first prototype kept a full 128-bit cumulative total for every value, consuming 24 logical bytes per column per row. That is simple and fast but poorly suited to large tables. Version 0.2 stores raw 8-byte integers on disk and one checkpoint per 4,096 rows, moving most work to ingestion. Eligible queries combine checkpoints and read only boundary pages. Runs are sorted independently, so new batches can arrive late without invalidating earlier aggregate indexes.

This is precomputation with known prior art. It trades sorting, write-time indexing, metadata, and restricted SQL for query speed. A maintained aggregate structure in another database can provide a similar algorithmic advantage. The engineering contribution is the concrete embedded storage path, automatic maintenance, exactness checks, and reproducible cost measurements.

A real-data zone query exposed a planning weakness: a second predicate initially forced a broad scan even though a time range could bound it. The planner now uses the sorted time predicate to limit streamed reads before applying the other filter. A Rust regression test and independent multi-filter cases check correctness. The current zone query reads 3,440,640 payload bytes; it still loses to DuckDB, so further work needs profiling rather than another unsupported speed claim.

## Suggested CV bullet

> Implemented archive-local source checkpointing in an embedded Rust metrics engine: published source intervals with output in one synchronized receipt, enforced contiguous progress and recovered offsets/data together. Verified 300 Parquet intervals against 42 DuckDB queries, 14 exact publication failures and eight forced-kill/resume cycles; disclosed write stalls and the absence of distributed consumer fencing.

> Profiled embedded batch-retry costs and implemented immutable prepared input with library-computed payload identity; retained preparation-inclusive and ordinary controls, rejected a weak hashing optimization, and verified original receipts and whole batches across stalled-writer, disk-full and process-exit tests. Published the narrower confirmed-retry gain separately from durable-write capacity and service failures.

> Diagnosed repeated receipt-ledger rewriting in an embedded Rust metrics store; implemented bounded catalog deltas/checkpoints, reducing catalog bytes for 96 appends from 788.02 MB to 24.72 MB with 50K retained IDs. Verified recovery through 56 exact process-exit/injected-error cases and retained checkpoint stalls and concurrent-load failures alongside performance gains.

> Profiled and optimized streamed aggregate queries with reusable buffers, row selections and typed reductions; reduced unordered-filter median latency from 6.49 to 3.69 ms in three alternating 1M-row comparisons. Verified results against independent SQL engines and retained mixed-load failures alongside observed publication stalls for further investigation.

> Developed a Rust/Python SQL analytics project with 100M persisted events and a 3.48M-record NYC data pipeline; added source hashes, quality/reconciliation checks, sparse aggregate indexes, late-batch support, and 500 SQL differential cases. Measured 2.095 ms median for indexed random time-window aggregates at 100M rows, versus 165.798 ms in the tested single-thread DuckDB setup.

> Built a reproducible six-engine stress harness with open-loop arrivals, up to 64 clients, 66 workload cases and explicit overload accounting; reconciled committed batches, audited retained request samples, and verified recovery across 24 forced Archive process kills. Identified mixed-write latency and SQL capability limits that block production qualification.

> Extended an embedded Rust metrics engine with immutable concurrent snapshots, durable SHA-256 batch receipts, group commits and bounded compaction/cache; verified replay and late backfills against 42 DuckDB SQL cases and recovered/retried batches across 24 forced process kills. Published raw performance samples and retained unstable runs instead of claiming universal speed superiority.

Keep the workload qualification when citing latency. Explain the memory counter's exclusion of OS caches and show the slower scan/grouping results. Use the project to demonstrate ownership: reproduce it, trace a query through the planner and storage code, and implement a small extension you can defend live.

## Five-minute demonstration

1. Open the real-data quality report and explain why negative charges were retained and timezone/money conversions were explicit.
2. Run `cargo test --release --locked`, then use the bundled executable with a fresh small archive via the commands in [ARCHIVE.md](ARCHIVE.md).
3. Show an unaligned time-window SQL query and its `bytes_read` and `plan` fields. Explain the boundary lookup and cumulative subtraction.
4. Show the 100M random-window report, then the unordered/grouped losses. Explain why the design favors a subset of analytics.
5. Run the [live Rust example](examples/live_ingest.rs) in a fresh directory, showing the stable pinned view, deduplicated replay and new view after a late event. Walk through receipt/catalog publication and one forced-kill recovery result. State that physical power loss remains unqualified.

## Next milestones with acceptance criteria

| Milestone | Reviewable acceptance criterion |
|---|---|
| General scan performance | Profile and reduce scalar/page I/O overhead; rerun the retained operator matrix and publish both latency and memory changes |
| Retry-safe ingestion | Implemented for archive batches; extend to atomic source checkpoints, consumer fencing, receipt-ledger endurance and explicit retention policy |
| Compaction and retention | Small-run compaction and reference-safe reclamation implemented; extend interrupted-maintenance fault injection, orphan cleanup and bounded retention, and quantify write amplification |
| Backup and restore | Restore into a clean process from a consistent snapshot; reconcile counts/sums and scrub all payload pages |
| Mixed-write service performance | Profile catalog publication and locking; sustain 2,000 offered requests/s with zero loss and p99 at or below 100 ms, preserving current commit/reconciliation behavior |
| Operations | Add stable error codes and metrics, test disk-full and physical power loss, extend endurance testing, and qualify Linux as well as Windows |
| Pipeline deployment | Add scheduled incremental runs, source-manifest tracking, quarantined rows, automated data assertions, and a monitored backfill policy |

These milestones distinguish a measured prototype from a supported production database. The current repository does not claim distributed processing, an orchestration deployment, full SQL parity, or production qualification.
