# KestrelSQL: data-engineering portfolio case study

## Project statement

Built a Rust embedded analytics engine and Python/SQL pipelines to investigate fast exact aggregates over append-only events. The archive persists 100 million rows, automatically maintains sparse aggregate indexes, accepts overlapping late batches and keeps raw values on disk. Version 0.3 adds concurrent immutable read views, durable batch receipts, group publication and bounded small-run compaction. Query results are checked against mature SQL engines rather than inferred from timing alone.

The portfolio demonstrates SQL, source lineage, data modeling, quality controls, reconciliation, ingestion, persistence, and performance measurement. It is a substantial project for interviews; it cannot guarantee a hiring outcome or establish production operating experience.

## Evidence a reviewer can inspect

| Evidence | Result | Where |
|---|---|---|
| Scale | 100M persisted rows; 2.4 GB raw integer payload | [SCALE.md](SCALE.md) |
| Process memory | 30.8 MiB measured peak for the ordered scale process, excluding OS file cache | [large-results.json](benchmarks/large-results.json) |
| Random window latency | 2.095 ms Kestrel median vs 165.798 ms DuckDB; 31 fresh windows at 100M rows | [random-window-results.json](benchmarks/random-window-results.json) |
| Public source pipeline | 3,475,226 input / 3,475,077 accepted / 149 rejected | [nyc-results.json](benchmarks/nyc-results.json) |
| Independent SQL checks | 500 Archive cases against each of SQLite and DuckDB; 124 scale windows against DuckDB | [archive-verification.json](benchmarks/archive-verification.json) |
| Recovery and integrity | Metadata/page CRC, atomic catalog publication, lock ownership, corruption/pending-file regression tests | [tests/archive.rs](tests/archive.rs) |
| Engineering checks | 55 Rust tests pass in debug and release for 0.3.7; format and Clippy pass | [verification.json](verification.json) |
| Retry availability | Opt-in confirmed retries validate independently of writer queueing; original receipts, bounded lookup memory, pending-ID races and fail-closed health; unsuccessful always-on trial preserved | [PERFORMANCE_035.md](PERFORMANCE_035.md) |
| Coalescing policy | Same-binary 0/2/8 ms comparisons, collection diagnostics, explicit latency/loss tradeoffs and zero-delay default | [PERFORMANCE_034.md](PERFORMANCE_034.md) |
| Receipt publication | 96.86% fewer catalog bytes in three alternating 50K-ID comparisons; bounded recovery and exact publication-cut checks | [PERFORMANCE_033.md](PERFORMANCE_033.md) |
| Analytical SQL | Validated 248 category/day rows: dimension join, complete calendar, LAG, and ranking | [gold_analysis.sql](portfolio/gold_analysis.sql), [checks](portfolio/gold-verification.json) |
| Historical concurrent stress | Six engines, 66 cases, 933,600 offered requests, 64 clients; exact reconciliation | [HARD_TESTS.md](HARD_TESTS.md) |
| Current live ingestion | Snapshots, group commits, identified retries, bounded cache and compaction; repeated comparisons with retained failures | [PERFORMANCE_035.md](PERFORMANCE_035.md) |
| Replay/backfill pipeline | 30,000 Parquet rows with 8 ms policy; both sources replayed without duplication; 42 exact SQL checks | [live-pipeline-035-results.json](portfolio/live-pipeline-035-results.json) |
| Actual Archive crashes | 32 concurrent process kills across 0/2/8/20 ms policies; whole batches, original receipt generations and no lost acknowledged batches | [group-035-recovery.json](benchmarks/group-035-recovery.json) |
| Research decisions | Primary papers and official docs connect architecture decisions to explicit future experiment gates | [RESEARCH.md](RESEARCH.md) |

The 0.2 hard tests exposed a significant limit: Kestrel completed 881.12 requests/s at 2,000 offered mixed requests/s, with 611.30 ms successful-request p99 and 53.94% loss/unexecuted work. Version 0.3 addresses writer exclusion, repeated boundary decoding and small-run growth. Version 0.3.1 adds stage profiling, faster exact retries, buffered durable writes and cheaper compaction input reads. [Current results](PERFORMANCE_031.md) disclose repeated comparisons, intermediate regressions and remaining failures; [0.3 results](V03_RESULTS.md) preserve the earlier evidence. Durable-write tail latency remains a release gate. Archive also lacks raw point retrieval, joins and transactional updates. Explain those boundaries and retain failed runs when presenting the project.

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
