# KestrelSQL

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

[Benchmark history: wins, losses and raw evidence](BENCHMARK_HISTORY.md) · [Download every preserved release](https://github.com/fizzexual/kestrel-sql/releases) · [Latest 0.3.16 package](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16)

**Fresh post-release service qualification:** [SERVICE_047.md](SERVICE_047.md) retains 52 million-row cases and 1,327,600 offered operations on unchanged 0.3.16. In three current six-engine rounds, Kestrel had 3/5 mixed-p99 median wins, 4/5 read-p99 wins and 2/5 append-p99 wins. Its failed 60-second soak and inconsistent batching trials remain visible; these results establish no engine upgrade or production service guarantee.

**Current source: 0.3.16 experimental packed medium key-cache candidate.** Exact signed tags and checked group indexes reduce the promoted table from 384 to 256 KiB on this 64-bit build. Cache budgets/fallback, randomized HashMap authority, exact i128 reductions and reader ownership remain. In 21 alternating 1M-row irregular SUM pairs, timings changed from 19.788 to 17.743 ms (paired ratio 0.897); wide SUM changed from 15.906 to 15.232 ms (paired ratio 0.950). Fresh DuckDB scores are 60 wins/0 losses over 60 shapes; the closest case has a 0.32% median gap and 2/3 round wins. A separate 21-pair repeat records a win with paired candidate/DuckDB ratio 0.979; its outcome is retained separately. [PERFORMANCE_046.md](PERFORMANCE_046.md) keeps every slower guard, two preserved build failures, predeclared criteria, 77 Rust tests, 4,000 SQL cases against each reference and current retry/crash/Parquet evidence.

**The 0.3.15 bounded reader reuse experiment.** Each segment can retain one exclusively owned idle stream file, with a shared limit of 128 idle files per archive. Queries still read and validate payload checksums; full scrubs open fresh files. In 21 alternating 1M-row fragmented scan pairs, the unordered query changed from 7.830 to 4.551 ms (paired ratio 0.581); 1,000-row sparse SUM changed from 0.118 to 0.065 ms (paired ratio 0.560). Fresh DuckDB scores are 59 wins/1 loss over 60 shapes. [PERFORMANCE_045.md](PERFORMANCE_045.md) retains every slower guard, the unselected offset-only trial, 76 Rust tests, 4,000 SQL checks against each reference, 104 concurrent/manual bridge oracles and current retry/crash/Parquet evidence.

**The 0.3.14 adaptive sparse SUM experiment.** Cache hits avoid redundant writes; shared sparse SUM/AVG fuses into key lookup while the small cache is active at block entry, with the earlier wider mapper retained. In 21 alternating 1M-row pairs, small sparse SUM changed from 8.566 to 8.013 ms (paired ratio 0.931); wide sparse SUM changed from 12.475 to 12.179 ms (paired ratio 0.954). Fresh DuckDB scores are 58 wins/2 losses over 60 shapes. [PERFORMANCE_044.md](PERFORMANCE_044.md) retains all results, rejected wider-fusion trials, 74 Rust tests, 4,000 SQL checks against each reference and current durable retry/crash/Parquet evidence.

**The 0.3.13 fused dense SUM experiment.** Dense GROUP SUM/AVG shares one exact counting and reduction pass. In 21 alternating 10M-row pairs, GROUP SUM changed from 73.730 to 66.423 ms (paired ratio 0.898); seven 100M-row pairs measured 733.970 to 666.307 ms (paired ratio 0.907). Fresh DuckDB scores are 58 wins/2 losses over 60 shapes. [PERFORMANCE_043.md](PERFORMANCE_043.md) preserves every result and guard, 73 Rust tests, 3,400 SQL checks against each reference, signed wide JSON and current recovery/Parquet evidence.

**The 0.3.12 medium-group cache experiment.** Sparse groups promote a wider exact-tag cache after measured key reuse, deferring allocation until the next nonempty block. In 21 alternating 1M-row wide-key pairs, GROUP SUM changed from 27.704 to 16.834 ms (paired ratio 0.616). Fresh DuckDB scores are 56 wins/4 losses over 60 shapes. [PERFORMANCE_042.md](PERFORMANCE_042.md) retains every result, the rejected tiny-query regression, all guards, 72 Rust tests, 2,800 SQL checks against each reference and current recovery/Parquet evidence. Promoted queries allocate an additional 384 KiB on this computer.

**The 0.3.11 seeded group-cache experiment.** Sparse GROUP BY cache indexing now uses a per-query multiplier while retaining exact key tags and randomized hash-table fallback. In 21 alternating 1M-row collision pairs, GROUP SUM changed from 18.115 to 8.972 ms. Fresh DuckDB scores are 28 wins/2 losses on matched shapes, 14/1 on prior stress shapes and 10/0 on added key patterns. [PERFORMANCE_041.md](PERFORMANCE_041.md) retains all 55 shapes, every loss, guard measurements, 70 Rust tests, 2,200 SQL cases against each reference and retry/crash/Parquet evidence.

**The 0.3.10 direct-filter experiment.** Streaming scans generate matching row positions directly from the first residual predicate. In 21 alternating 1M-row pairs, the unordered scan changed from 3.154 to 2.893 ms; seven 100M-row pairs changed from 340.939 to 318.823 ms. The fresh matched DuckDB matrix has 29 median wins and 1 loss. [PERFORMANCE_040.md](PERFORMANCE_040.md) keeps every loss, the rejected outlining trial, checks against 0.3.8, 70 Rust tests, 1,600 SQL cases against each reference and current retry/crash/Parquet evidence.

**The 0.3.9 sparse-grouping experiment.** Compact domains now have a 65,536-slot ceiling with the existing 8 MiB state budget and row-count guard; wider keys use typed hash states and a bounded tagged cache that disables itself for poor hit rates or higher cardinality. In the fresh 1M-row full-grouping cases, sparse keys changed from 72.40 to 24.81 ms and 5,003 compact keys from 106.96 to 17.11 ms. The matched matrix has 22 median DuckDB wins and 8 losses; an additional wide/collision/high-cardinality matrix keeps its own score. [PERFORMANCE_039.md](PERFORMANCE_039.md) includes every loss, cache regressions, 69 Rust tests, 1,000 SQL oracle cases and current recovery/Parquet checks.

**The 0.3.8 grouping experiment.** Compact integer group domains use bounded direct-address arrays, with exact shared SUM/AVG reductions and hash fallback for wider keys. In the fresh 100M-row full GROUP BY comparison, the median of three run medians changed from 5.504 s in 0.3.7 to 1.694 s; DuckDB measured 1.896 s. All results matched. [PERFORMANCE_038.md](PERFORMANCE_038.md) includes every win/loss, raw samples, short control repeats, 63 Rust tests and current recovery/Parquet checks. No new network req/s or production-service claim is made.

**The 0.3.7 source-checkpoint experiment.** `SourceArchive` commits each nonempty output and its source interval in one synchronized receipt publication. Reopening recovers the resume position with its data; gaps, overlaps, stale offsets and changed retries are rejected. It adds no checkpoint file or sync and preserves CAT4/SEG2. See [PERFORMANCE_037.md](PERFORMANCE_037.md) for measured costs, 55 Rust tests, current recovery/Parquet checks and retained write stalls, and [SOURCE_INGEST.md](SOURCE_INGEST.md) for the SDK. This is archive-local checkpoint atomicity; distributed consumer fencing and zero-output checkpointing remain work.

The [0.3.6 immutable batch experiment](PERFORMANCE_036.md) adds `PreparedBatch` and `LiveArchive::append_prepared` for confirmed embedded retries. Its extra receipt index stays off by default; construction and fresh-write costs remain disclosed. Previous packages and measurements are preserved.

The [0.3.5 lookup experiment](PERFORMANCE_035.md) separates confirmed retries from writer queueing. Its initial write-heavy regression is preserved; the additional lookup remains opt-in.

The [0.3.4 coalescing experiment](PERFORMANCE_034.md) adds an explicit `LiveOptions` window and collection diagnostics. Optional waiting can regress latency and loss, so the default remains zero delay.

In the [0.3.3 receipt-catalog experiment](PERFORMANCE_033.md), 50,000 retained retry IDs and 96 new appends wrote 24.72 MB of catalogs versus 788.02 MB in the fresh 0.3.2 baseline (96.86% fewer bytes). CAT4 uses receipt deltas and bounded checkpoints, preserves synchronization before ACK, reads older catalogs and is rejected by pre-CAT4 writers. Checkpoint/storage stalls and service-target failures remain disclosed.

The [0.3.2 scan experiment](PERFORMANCE_032.md) reduced unordered-filter median time from 6.49 to 3.69 ms on a paired 1M-row fixture, while failing repeated service targets. The 0.3.1 measurements below describe an earlier release and run; they do not describe the current service envelope.

An experimental embedded SQL database for exact live metrics over append-only events. The working product idea is **automatically indexed, arbitrary time-window totals inside an application**, with durable ingestion and no materialized-view definition per window.

**Version 0.3.1 improves replay and compaction costs and adds publication-stage diagnostics.** `LiveArchive` combines immutable read snapshots, durable group commits, SHA-256 batch receipts, small-segment compaction and a bounded decoded-page cache. Late batches immediately contribute to new read views; exact retries do not add duplicate rows. Try the [Rust and Parquet workflows](LIVE_METRICS.md), inspect [current measured results](PERFORMANCE_031.md), and read the [primary-source design notebook](RESEARCH.md).

`Archive` stores immutable sorted column segments with sparse prefix sums, block extrema, checksums and atomic catalog generations. Raw rows remain on disk. The original `Database` API below remains a separate RAM-resident transactional prototype. See [ARCHIVE.md](ARCHIVE.md), [historical large-scale results](SCALE.md), and the [portfolio case study](PORTFOLIO.md).

**Readiness: research prototype.** This repository demonstrates a specialized speed advantage and tests important recovery behavior. Production release still requires the work and acceptance criteria below. There is no verified claim that this is the world's fastest database or that the underlying algorithm is novel.

**Performance evidence includes failures.** The [0.2 stress baseline](HARD_TESTS.md) completed about 881 requests/s at 2,000 offered mixed requests/s, with 53.94% loss/unexecuted work. Version 0.3 addresses the coarse writer lock, repeated boundary decoding and growing small-run count. Version 0.3.1 targets receipt copies, small publication writes and compaction input reads. Repeated comparisons, raw samples, intermediate regressions and remaining failures are in [PERFORMANCE_031.md](PERFORMANCE_031.md); [V03_RESULTS.md](V03_RESULTS.md) preserves the preceding release. Archive SQL capability gaps still prevent a transactional social-graph comparison.

In three rotated 15-second mixed runs at 2,000 offered requests/s, version 0.3.1 completed all offers with run p99s of 4.24–31.17 ms (median 6.38 ms). The old 0.3 build had 54.15–117.86 ms p99 (median 73.64 ms) on the same harness. A separate one-minute 500/s run had 4.87 ms p99 and zero loss. The 10,000/s overload case still lost 25,367 offers, and the single-client mixed p99 remained 147.72 ms. These shared-desktop results do not qualify a production service envelope.

Three alternating in-process probes at 50,000 stored batch IDs reduced median exact-retry latency from 11.85 ms to 2.8 microseconds. A full 100,000-ID test verifies capacity, reopen, exact replay and checksums. New-ID catalog rewrite endurance remains work. Grouped query timings improved on the tested 1M-row fixture, while the unordered-filter probe regressed; all query results and timings are retained.

## Why this direction

The opportunity is the combination of embedding, fresh committed data, and automatically maintained exact range aggregates. For example, an application can ask for a count, total, and average for any interval of its event timeline immediately after ingestion.

DuckDB documents that its ART indexes do not accelerate aggregation, although its zonemaps help skip data. SQLite documents range scans through covering indexes. Materialize already maintains query results incrementally, and ClickHouse provides incremental materialized views. These are capable competitors; a blanket claim that popular databases lack live analytics would be incorrect. Our differentiator is a specific automatic embedded experience that needs validation with users.

Sources: [DuckDB indexing](https://duckdb.org/docs/guides/performance/indexing), [SQLite query planning](https://www.sqlite.org/queryplanner.html), [Materialize indexes](https://materialize.com/docs/fundamentals/concepts/indexes/), [ClickHouse incremental views](https://github.com/ClickHouse/clickhouse-docs/blob/main/docs/materialized-view/incremental-materialized-view.md). Aggregate range indexes also have [published prior art](https://arxiv.org/abs/1910.11754).

## Run it

Rust 1.89 or later is required to build. Cargo.lock pins the dependencies used in this run. Commands below assume PowerShell in this project directory.

```powershell
cargo build --release --locked
.\target\release\kestrel.exe --file examples\live_metrics.sql
.\target\release\kestrel.exe --db ..\..\work\my-events
```

The second command executes a sample in memory. The third opens a durable database and reads one SQL statement per input line. Output is JSON lines. An unfinished transaction is discarded when the process exits. A supplied `bin/kestrel.exe` runs the same engine without a local Rust build; it has been tested on this Windows machine.

```sql
CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL);
INSERT INTO events VALUES (100, 12, 1), (101, 18, 2), (102, 25, 1);
SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= 100 AND ts < 102;
EXPLAIN SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 102;
```

The result is `[[2, 30, 15.0]]`. EXPLAIN reports `prefix-range-aggregate` and the query result includes `rows_scanned: 0`. Prefix entries are current, including a transaction's own staged writes.

The CLI also accepts `--sql "..."` and `--help`. File input uses one complete statement per line, with blank lines and SQL line comments allowed. It is a development interface; there is no network listener.

## Embed it in Rust

```rust
use kestrel_sql::Database;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut db = Database::open("my-events")?;
    db.execute("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL)")?;
    // The batch API accepts columns in schema order.
    db.append("events", vec![vec![100, 101, 102], vec![12, 18, 25]])?;
    let result = db.query("SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 102")?;
    println!("{:?}", result.rows);
    Ok(())
}
```

Use `Database::memory()` for an ephemeral database. The schema example requires a fresh directory. Use `begin`, `commit`, and `rollback` to batch durable writes. One Database owns one transaction context; Rust borrowing protects mutation, and application synchronization is needed when sharing it. Concurrent independent sessions and MVCC are future work.

## Implemented SQL and behavior: Database API

- CREATE TABLE with 1–64 unique `BIGINT NOT NULL` columns.
- INSERT INTO ... VALUES with multiple complete rows, and a column batch API.
- SELECT columns or `*`; COUNT(*), SUM, AVG, MIN, MAX; explicit AS aliases.
- WHERE column comparisons against integer literals, combined with AND.
- GROUP BY one column; ORDER BY one selected name or alias; LIMIT.
- BEGIN, COMMIT, ROLLBACK, EXPLAIN SELECT.

Identifiers are unquoted ASCII and case insensitive in SQL. Values are signed 64-bit integers. Application code chooses the time unit for a `ts` column. Sums use 128-bit integers and may exceed BIGINT; averages are floating point. Empty aggregate inputs return SQL NULL, except COUNT which returns zero. Unsupported grammar is rejected, including trailing statements. A failed statement leaves the surrounding explicit transaction open; earlier successful statements remain staged.

Strings, nullable input columns, decimal money, native timestamps, joins, UPDATE, DELETE, uniqueness constraints, parameter binding, foreign keys, and query cancellation remain unimplemented. The source is ordinary Rust with unsafe code forbidden in this crate; dependencies have their own implementations.

## Why the RAM fast path works

Each column stores its values and exact cumulative sums. For nondecreasing filter columns, binary search finds the two row boundaries of a contiguous range. Subtracting the cumulative sums gives an exact range total; the boundary difference gives its count. AVG uses those two quantities. No row scan or query-result cache is needed.

An eligible range aggregate takes O(log n + a), where `a` is the number of requested aggregate expressions. Whole-table totals take O(a). Appending a batch costs O(rows × columns), plus serialization and synchronization in durable mode. This moves work and memory to ingestion, which is the central tradeoff.

The fast path accepts AND predicates on one nondecreasing column, with `=`, `<`, `<=`, `>`, or `>=`. Contradictory bounds yield an empty range. MIN/MAX and grouped queries use scans. Multiple filter columns and `<>` also use scans. If a late event breaks ordering, filtered queries on that column automatically fall back to a correct scan. Whole-table sums still use prefixes. Rollback restores the prefixes and ordering detection, but recalculating ordering during rollback can scan existing data.

Values and prefixes occupy **24 logical bytes per column per row**, compared with 8 bytes for raw BIGINT data. This excludes allocation slack, transaction buffers, WAL buffers, query state, and process runtime. The measured one-million-row, three-column table uses 72,000,048 logical bytes. This Database implementation is entirely RAM-resident, with per-table limits of 10 million rows, 64 tables, and 100,000 materialized result rows/groups. ORDER BY currently materializes within that result budget before LIMIT; it does not implement a bounded top-k sort. There is no global memory governor or disk spilling. The separate Archive implementation has different storage and limits; see [ARCHIVE.md](ARCHIVE.md).

## Durable storage

`--db` opens a directory containing `events.ksql` and a held OS lock in `writer.lockfile`. A second cooperating opener fails while the lock is held; the lock is released on close or process termination.

Each committed transaction is one length-delimited WAL frame with a magic value, length complement, and CRC32 checksum. Commit attempts `sync_all()` before acknowledging success. Recovery rebuilds values and indexes from valid committed frames. A structurally incomplete final frame is discarded and its tail truncated; complete corrupt frames are rejected. An I/O failure poisons the live handle and reports an **unknown commit outcome**. A complete frame may survive even when its caller did not receive acknowledgment, so the application must reconcile before retrying.

The current on-disk format is version 1 and has no migration commitment. CRC32 detects accidental changes and does not authenticate data. Recovery cannot distinguish a crash-truncated tail from external file truncation. The WAL grows without checkpointing or retention, and reopen time grows with its history. `sync_all` relies on operating-system and storage behavior; process termination and simulated truncations are tested, but physical power-loss behavior and Windows directory-entry durability are not qualified.

## Verify and benchmark

```powershell
$env:KESTREL_TEST_ROOT = "..\..\work\cargo-tests"
cargo fmt --all -- --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --release --locked
python -m pip install -r benchmarks\requirements.txt
python benchmarks\compare.py
```

The reference benchmark needs Python 3 and the pinned DuckDB dependency. SQLite comes with Python. `compare.py --binary PATH --rows 1000000 --repeats 31 --output PATH` overrides defaults. On Linux, pass `--binary target/release/kestrel`.

The benchmark uses a deterministic three-column event dataset. SQLite receives a `(ts,value)` covering index and a `value` index; DuckDB receives a `ts` ART index. All engines use one execution thread. There are three warmups and 31 measured repetitions. Query timings include parsing, execution, and result materialization. Direct Rust and Python bindings have different boundary costs; a second Kestrel measurement includes the Python caller, pipe round trip, and JSON encoding/decoding. Dataset construction and index maintenance differ by engine, so their recorded load times are diagnostic and must not be presented as fair ingestion rankings.

See [BENCHMARK.md](BENCHMARK.md) for the measured results and limitations, and [raw results](benchmarks/results.json) for every sample and reference query plan. The deterministic differential test compares 1,002 queries against both DuckDB and SQLite, including grouped/empty inputs, late arrivals, and reopening after process termination. Rust tests cover integer extremes, malformed statement atomicity, rollback, locking, partial final records, complete corruption, and injected commit failures.

## Production work and release gates

1. **Validate the product need.** Test actual app traces, especially late arrivals, device cardinality, event sizes, and retention. Establish which API latency matters and compare with existing engines plus equivalent maintained indexes/views. Publish costs of maintenance, storage, and restarts alongside query latency.
2. **Bound storage and recovery.** Implement checkpoints, compaction/retention, snapshot backup/restore, format migration, and a global memory budget. Test interrupted checkpoints, damaged snapshots, disk exhaustion, and directory-entry durability on supported filesystems.
3. **Preserve speed under realistic ingestion.** The Archive combines exact aggregates across independently sorted segments, including late batches, with bounded small-run compaction. Selective index policies, compression and faster grouping remain future work. Benchmark additional batch sizes, write amplification, ingest stalls and tail latency; repeated durable-write service performance remains a gate.
4. **Finish the application contract.** Batch retry identifiers and immutable read views are implemented. Required types and constraints, parameter binding, schema evolution, cancellation and complete session semantics remain work. Add stable error codes and production health metrics. Authentication is necessary if a network service is introduced.
5. **Qualify correctness and operations.** Add coverage-guided parser/recovery fuzzing, independent SQL differential suites, filesystem fault injection, long mixed-workload stress tests, Linux verification, and real power-loss testing. Demonstrate backup restoration and upgrades with real datasets. Define supported environments and measurable release criteria before deployment.

The useful result today is a runnable engine and evidence for one design bet. Production suitability is a further engineering and qualification milestone.
