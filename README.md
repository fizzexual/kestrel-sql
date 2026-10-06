# KestrelSQL

**Current source: 0.3.2 experimental scan candidate.** Three fresh alternating runs reduced the unordered-filter median from 6.49 to 3.69 ms on a 1M-row fixture. Repeated service tests still failed the zero-loss/100 ms target and exposed long file synchronization/publication stalls. Read [PERFORMANCE_032.md](PERFORMANCE_032.md) for all new cases. The previous 0.3.1 package and its evidence remain preserved; its earlier service measurements below describe that release and run.

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
