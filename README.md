# KestrelSQL

**Supported version 0.3.16. Research prototype. Version 0.3.17 is unreleased.**

Rust embedded SQL and append-only analytics with exact range aggregates,
immutable archive snapshots, checksummed segments and retryable batch ingestion.
The Archive and RAM-resident transactional Database APIs have different contracts.
[Archive API](ARCHIVE.md), [live ingestion](LIVE_METRICS.md),
[version and benchmark summary](VERSION_SUMMARY.md).

Completed experiments use short Markdown reports in [benchmark history](BENCHMARK_HISTORY.md).
Large historical artifacts remain in private Git history. To download only the
current project: `git clone --depth 1 https://github.com/fizzexual/kestrel-sql.git`. [Storage policy](STORAGE_POLICY.md).

[Complete writer comparison135](COMPACTION_WRITE_COMPARE_135.md) rejects write-through:
216 correct cases,24 controls/35 guards/all6 goals fail.0.3.17 is unreleased.

[Isolated bounded compaction writer134](COMPACTION_WRITE_134.md) passed344 tests,
exact legacy wire and14 recovery cases; speed is unmeasured.

[Complete comparison133](COMPACTION_COMPARE_133.md) finds controlled clustered
whole compaction10.80% lower;7/72 controls and1/72 guard fail.0.3.17 is unreleased.

[Interrupted comparison132](COMPACTION_PREFIX_132.md) preserves88 independently
correct cases;128 remain unstarted after an activity hold between timers.

[Experimental lazy compaction workspace131](COMPACTION_PHASE_131.md) passed340
fresh tests/two lints/eight independent store audits; speed qualification is pending.

[Comparison130](COMPACTION_PREFIX_130.md) preserves44 independently correct cases;
172 timings remain unstarted after a new activity hold. Performance stays pending.

[Stopped comparison129](COMPACTION_PREFIX_129.md) preserves all seven independently
correct cases;209 timings are unstarted. A status-query false alarm held the run.

[Fresh comparison preflight128](COMPACTION_PREFLIGHT_128.md) passed six independent checks;
a new external build held all216 timings before case0. Performance remains pending.

Latest [experimental compaction phase repair](COMPACTION_PHASE_127.md) passed
correctness prerequisites; its performance and release qualification are pending.

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

- CREATE TABLE with 1â€“64 unique `BIGINT NOT NULL` columns.
- INSERT INTO ... VALUES with multiple complete rows, and a column batch API.
- SELECT columns or `*`; COUNT(*), SUM, AVG, MIN, MAX; explicit AS aliases.
- WHERE column comparisons against integer literals, combined with AND.
- GROUP BY one column; ORDER BY one selected name or alias; LIMIT.
- BEGIN, COMMIT, ROLLBACK, EXPLAIN SELECT.

Identifiers are unquoted ASCII and case insensitive in SQL. Values are signed 64-bit integers. Application code chooses the time unit for a `ts` column. Sums use 128-bit integers and may exceed BIGINT; averages are floating point. Empty aggregate inputs return SQL NULL, except COUNT which returns zero. Unsupported grammar is rejected, including trailing statements. A failed statement leaves the surrounding explicit transaction open; earlier successful statements remain staged.

Strings, nullable input columns, decimal money, native timestamps, joins, UPDATE, DELETE, uniqueness constraints, parameter binding, foreign keys, and query cancellation remain unimplemented. The source is ordinary Rust with unsafe code forbidden in this crate; dependencies have their own implementations.

## Why the RAM fast path works

Each column stores its values and exact cumulative sums. For nondecreasing filter columns, binary search finds the two row boundaries of a contiguous range. Subtracting the cumulative sums gives an exact range total; the boundary difference gives its count. AVG uses those two quantities. No row scan or query-result cache is needed.

An eligible range aggregate takes O(log n + a), where `a` is the number of requested aggregate expressions. Whole-table totals take O(a). Appending a batch costs O(rows Ã— columns), plus serialization and synchronization in durable mode. This moves work and memory to ingestion, which is the central tradeoff.

The fast path accepts AND predicates on one nondecreasing column, with `=`, `<`, `<=`, `>`, or `>=`. Contradictory bounds yield an empty range. MIN/MAX and grouped queries use scans. Multiple filter columns and `<>` also use scans. If a late event breaks ordering, filtered queries on that column automatically fall back to a correct scan. Whole-table sums still use prefixes. Rollback restores the prefixes and ordering detection, but recalculating ordering during rollback can scan existing data.

Values and prefixes occupy **24 logical bytes per column per row**, compared with 8 bytes for raw BIGINT data. This excludes allocation slack, transaction buffers, WAL buffers, query state, and process runtime. The measured one-million-row, three-column table uses 72,000,048 logical bytes. This Database implementation is entirely RAM-resident, with per-table limits of 10 million rows, 64 tables, and 100,000 materialized result rows/groups. ORDER BY currently materializes within that result budget before LIMIT; it does not implement a bounded top-k sort. There is no global memory governor or disk spilling. The separate Archive implementation has different storage and limits; see [ARCHIVE.md](ARCHIVE.md).

## Durable storage

`--db` opens a directory containing `events.ksql` and a held OS lock in `writer.lockfile`. A second cooperating opener fails while the lock is held; the lock is released on close or process termination.

Each committed transaction is one length-delimited WAL frame with a magic value, length complement, and CRC32 checksum. Commit attempts `sync_all()` before acknowledging success. Recovery rebuilds values and indexes from valid committed frames. A structurally incomplete final frame is discarded and its tail truncated; complete corrupt frames are rejected. An I/O failure poisons the live handle and reports an **unknown commit outcome**. A complete frame may survive even when its caller did not receive acknowledgment, so the application must reconcile before retrying.

The current on-disk format is version 1 and has no migration commitment. CRC32 detects accidental changes and does not authenticate data. Recovery cannot distinguish a crash-truncated tail from external file truncation. The WAL grows without checkpointing or retention, and reopen time grows with its history. `sync_all` relies on operating-system and storage behavior; process termination and simulated truncations are tested, but physical power-loss behavior and Windows directory-entry durability are not qualified.

## Verify

```powershell
cargo fmt --all -- --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --release --locked
```

Reusable baseline harnesses remain under `benchmarks/`; completed run data is
archived. No new benchmark was run during cleanup. No universal speed,
production-service or physical power-loss claim is qualified.

[Cleanup result](STORAGE_CLEANUP_FINAL.md), [benchmark history](BENCHMARK_HISTORY.md).
