# Measured results

Recorded for the prototype on 5 October 2026. These are specialized workload measurements on one live Windows machine, not a database leaderboard or production certification.

Environment: Windows-10-10.0.19045-SP0; Intel64 Family 6 Model 165 Stepping 5, GenuineIntel; Python 3.12.10; rustc 1.97.1 (8bab26f4f 2026-07-14). Reference versions: DuckDB 1.5.6, SQLite 3.49.1.

One million deterministic rows; three BIGINT columns; one execution thread; three warmups; 31 measured repetitions. All datasets fit in RAM. Every reported query result matched the reference engines. Query medians below are in **microseconds**.

| Query | Kestrel Rust API | Kestrel Python + pipe + JSON | DuckDB Python | Indexed SQLite Python | SQLite manual prefix table |
|---|---:|---:|---:|---:|---:|
| all_aggregates | 4.4 | 38.1 | 3,171.7 | 51,905.4 | 35.4 |
| broad_window | 5.2 | 40.6 | 2,612.5 | 39,067.9 | 35.5 |
| narrow_window | 3.8 | 35.4 | 417.3 | 65.8 | 31.5 |
| unordered_filter | 6,749.4 | 6,483.6 | 3,199.1 | 18,446.8 | — |
| grouped | 22,629.1 | 23,529.5 | 5,881.2 | 346,853.0 | — |
| min_max | 3,815.7 | 3,817.6 | 2,737.7 | 33,030.9 | — |

The broad-window query aggregates 500,000 rows. Kestrel takes 5.2 μs through its Rust API or 40.6 μs through the Python/pipe interface, versus 2612.5 μs for DuckDB's Python binding. That is approximately 502× and 64× respectively **for this query and setup**. Boundary costs differ and neither ratio predicts other workloads.

DuckDB wins the grouped, unordered-filter, and MIN/MAX cases. SQLite with an explicitly precomputed prefix table also avoids range scans and slightly beats Kestrel's pipe interface in these measurements. The manual SQLite queries have additional schema and explicit boundary-lookups; they are not the original SQL. This baseline demonstrates that the algorithm is known and reproducible. It includes initial construction, but no future-ingestion maintenance was measured for that table.

Kestrel's values and prefix entries use 72,000,048 logical bytes, approximately three times the raw 64-bit column data. This is not peak resident memory. The durable run wrote 14,067,959 WAL bytes, appended its million-row batch in 292.9 ms, and reopened/rebuilt indexes in 88.8 ms. The batch data was generated before Kestrel's append timer. Comparator ingestion methods differ, so these load figures are diagnostics, not ingestion speed rankings.

## What the benchmark includes

- Warm parsing, execution, and materialization, with startup/loading outside query timers.
- Ordinary SQLite covering `(ts,value)` and `value` indexes; SQLite's statement cache disabled.
- A DuckDB `ts` ART index and a single execution thread.
- Raw timings, p95 values, SQL, results, and competitor EXPLAIN plans in [results.json](benchmarks/results.json).
- A separate Rust memory run, durable run after reopening, and conservative Python/pipe Kestrel run.
- A manual SQLite prefix-table baseline with query rewrites, construction cost, and explained limits.

## Limits

This is a small synthetic, append-only suite with an ordered timestamp column. It excludes multi-client contention, cold I/O, larger-than-memory data, heavy late arrivals, mixed transactional updates, power failures, and distributed execution. Engines were measured sequentially on a shared live machine, without CPU affinity or randomized engine ordering. API boundaries and maintained data structures differ. Competitors implement substantially more SQL. No claim about the fastest current engine follows from this run.

## Verification

- 15 Rust tests pass in debug and optimized release builds.
- 1,002 SQL comparisons pass against both DuckDB and SQLite; the final comparison suite includes 200 randomized queries that exercise the prefix fast path.
- Recovery tests cover abrupt process termination, all partial-tail cut points in a transaction, byte-by-byte complete corruption, exclusive locking, and injected partial-write/synchronization failures.
- Formatting and Clippy with warnings treated as errors pass.
- The example script runs successfully, including read-own-writes and rollback.
- Local qualification was performed on Windows. The included Linux/Windows CI configuration has not been run remotely.

See [README.md](README.md) for reproduction commands and the production release gates.
