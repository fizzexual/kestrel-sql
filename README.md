# KestrelSQL

A small embedded analytics engine in Rust for **append-only integer time series**.

It answers `COUNT`, `SUM` and `AVG` over a time range in a few microseconds without reading the
rows. Its storage is designed and tested so that a write cut off halfway is detected and discarded
on the next open, without touching data that was already committed.

**Status: research prototype, version 0.3.16.** It is not a general SQL database and it is not
production-qualified. [What it does not do](#what-it-does-not-do) and
[what the tests do not cover](#crash-safety-and-tests) are part of the description, not footnotes.

```sql
CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL);
INSERT INTO events VALUES (100, 12, 1), (101, 18, 2), (102, 25, 1);
SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= 100 AND ts < 102;
EXPLAIN SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 102;
```

The result is `[[2, 30, 15.0]]`. `EXPLAIN` reports `prefix-range-aggregate`, and the query result
carries `rows_scanned: 0`.

## The idea

Every column stores its values and, next to them, the exact running total up to each row. When the
filter column is in nondecreasing order (time usually is), a range such as `ts >= a AND ts < b` is
two binary searches. The sum of the range is one subtraction of two running totals, the count is the
distance between the two positions, and the average is those two divided. No row is read and there
is no result cache to go stale.

The price is paid when data is loaded: 24 bytes per value (8 for the value, 16 for a 128-bit running
total) instead of 8, and the totals are computed on every append. If a late event breaks the order,
filtered queries on that column fall back to a correct scan.

## Two APIs

- **`Database`** keeps tables in memory and writes every committed transaction to a log. It speaks
  the SQL subset below and has `BEGIN` / `COMMIT` / `ROLLBACK`. The benchmark in the next section
  measures this API.
- **`Archive`** is the on-disk store: sorted immutable segments, snapshots, compaction, and batches
  that can be retried safely. It answers `SELECT` queries through the same parser. `LiveArchive`
  puts concurrent writers in front of it.

## How fast

One million rows, three columns, in memory, the `Database` API. Same data and the same SQL text in
both engines; every answer is compared and all of them agree.

SQLite is **not the fair rival** here: it is a row store built for transactions. It is in the table
because everyone has it and can check the result. The fair comparison is a column store such as
DuckDB, and the script adds a DuckDB column when it is installed.

| Query | KestrelSQL | SQLite | SQLite with an index on `(ts, value)` |
| --- | ---: | ---: | ---: |
| `COUNT`, `SUM`, `AVG` of the whole table | 2.1–2.3 µs | 30–33 ms | 33–45 ms |
| The same over half of the time range | 2.7–2.9 µs | 54–56 ms | 33–36 ms |
| `COUNT`, `SUM` over the last 1,000 rows | 2.1–2.2 µs | 24–25 ms | 0.05–0.06 ms |
| `COUNT`, `SUM` with a filter on an unsorted column | 3.4–3.6 ms | 39–42 ms | 39–41 ms |
| `SUM` per device (97 groups), sorted | 12.8–13.4 ms | 261–284 ms | 264–277 ms |
| `MIN`, `MAX` over half of the time range | 1.9–2.1 ms | 46–53 ms | 28–32 ms |

Medians of 21 timed runs after 3 warm-ups; each cell is the range across three consecutive runs of
the script on 2026-11-15 (Intel Core i9-13900KF, Windows 11, Rust 1.99.1, SQLite 3.50.4). With
other work running on the same machine both engines were up to about twice as slow, with similar
ratios.

Reproduce it:

```
cargo build --release --locked
python benchmarks/quick_compare.py
```

It needs only the Python standard library (on Linux the command is usually `python3`).
`pip install duckdb` adds the DuckDB column.

How to read the table:

- **The first three rows are the running-total path.** That work was moved to load time and to
  memory. The last three rows are ordinary column scans.
- **The timers are not identical.** KestrelSQL reports its own in-process time. SQLite is timed in
  Python around `execute` and `fetchall`, which adds a few microseconds per call.
- **Earlier DuckDB comparisons** are summarised in the [lab notebook](lab-notebook/README.md). Their
  drivers are not all in this repository, so treat them as history, not as a claim you can check
  here.
- **Where it loses.** As a service under concurrent load it is not the fastest. In the 0.3.16
  comparison against five other engines it recorded 3 of 5 mixed-p99 median wins, 4 of 5 for reads
  and 2 of 5 for appends, and it failed a 60-second soak test
  ([SERVICE_047.md](lab-notebook/SERVICE_047.md)). An older version (0.2) completed 881 of 2,000
  offered requests per second ([HARD_TESTS.md](lab-notebook/HARD_TESTS.md)).

## What is inside

About 5,700 lines of Rust, four direct dependencies (`serde`, `serde_json`, `crc32fast`, `sha2`),
and `unsafe` code is forbidden for the whole crate.

| Part | File | What it does |
| --- | --- | --- |
| SQL parser | [src/sql.rs](src/sql.rs) | Hand-written lexer and recursive-descent parser for the supported subset |
| Planner and executor | [src/query.rs](src/query.rs) | Picks one of four plans: running-total range, bounded scan, filtered scan, grouped scan |
| In-memory database | [src/lib.rs](src/lib.rs) | Tables, transactions, hard limits on rows, columns and tables |
| Write-ahead log | [src/wal.rs](src/wal.rs) | One checksummed frame per committed transaction, replayed on open |
| On-disk archive | [src/archive.rs](src/archive.rs) | Sorted immutable segments with a checksum, minimum, maximum and running total per 4,096-row block; compaction; snapshots |
| Live ingestion | [src/live.rs](src/live.rs) | Concurrent writers grouped into bounded durable commits; readers work on immutable snapshots |
| Source positions | [src/source.rs](src/source.rs) | Stores how far an input was consumed in the same atomic step as the data |

Two details worth reading in the code, both in the `Archive`:

- **Publishing a segment** (`Archive::publish` in `src/archive.rs`): the segment is written and
  synced, then the new catalog is written to a `.pending` file, synced, and renamed into place. A
  reader sees either the old catalog or the new one, never half of each.
- **Retried batches are stored once.** A batch can carry an ID. The archive keeps a SHA-256 digest
  per ID, so sending the same batch again returns the original receipt, and sending different data
  under the same ID is refused.

Longer descriptions: [Archive API](docs/ARCHIVE.md), [live ingestion](docs/LIVE_METRICS.md),
[source ingestion](docs/SOURCE_INGEST.md).

## Crash safety and tests

```
cargo fmt --all -- --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --release --locked
```

`cargo test` runs 77 tests. The ones that say most about the design:

- `every_partial_final_frame_is_discarded_and_all_prior_commits_survive`
  ([tests/engine.rs](tests/engine.rs)): cuts the last log frame at every byte offset and checks
  that everything committed before it is still there.
- `complete_corruption_is_rejected_without_modifying_the_wal`: flips one bit at every byte offset
  and checks that opening fails and the file is left untouched.
- `process_kill_preserves_acknowledged_commit_and_releases_lock`: kills a child process and checks
  that acknowledged commits survive and the lock is released.
- `random_ranges_match_an_independent_scan`: 1,000 random ranges checked against a plain scan.
- `concurrent_ingestion_retries_and_snapshot_reads_reconcile`
  ([tests/archive.rs](tests/archive.rs)): several writers and a reader at once, with an invariant
  checked on every snapshot.

When a write or sync fails, the handle is poisoned and reports **"commit outcome unknown"** instead
of guessing. A complete frame can survive even when its caller never got the acknowledgement, so
the application has to reconcile before retrying.

What the tests do not cover:

- Physical power loss. Torn writes are produced by truncating files, and the kill test stops the
  process between statements, not during a write.
- The archive's on-disk format gets single-offset corruption tests, not the every-byte sweep the
  log gets.
- There is no fuzzing and no property-based testing of the SQL parser.
- The comparison against SQLite and DuckDB lives in `benchmarks/`, not in `cargo test`.
- Continuous integration builds with the current stable Rust only; the minimum version in
  `Cargo.toml` (1.89) is not built there.

## What it does not do

- Values are signed 64-bit integers only. No text, no decimals, no native timestamps, no `NULL`
  input.
- One table per query. No joins, no subqueries.
- No `UPDATE` and no `DELETE`. Data is append-only.
- `WHERE` is a list of `column <op> integer` comparisons joined by `AND`. No `OR`, no `BETWEEN`, no
  arithmetic in expressions.
- Aggregates are `COUNT(*)`, `SUM`, `AVG`, `MIN` and `MAX` of a column. No `COUNT(column)`, no
  `DISTINCT`. `GROUP BY` takes one column.
- The `Database` API keeps everything in memory (up to 10 million rows per table). Its log grows
  without checkpointing, so reopening gets slower as history grows. The `Archive` API is the
  on-disk store and has its own limits.
- No network server, no parameter binding, no query cancellation.

## Run it

Rust 1.89 or later.

```
cargo build --release --locked
./target/release/kestrel --file examples/live_metrics.sql
./target/release/kestrel --db demo-db
```

The second command runs a sample in memory. The third opens a durable database in the folder
`demo-db` and reads one SQL statement per input line; output is JSON lines. `--help` lists the
archive, import and benchmark modes.

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

This prints `[[Int(30)]]`. It creates the table in the folder `my-events`, so it needs a fresh
folder: a second run stops with `table already exists`. `Database::memory()` gives a database that
is not written to disk.

## How it was built: the lab notebook

The engine was developed as a series of numbered experiments. Each one has a short report: what
was changed, what was measured, and whether it was adopted. Versions 0.3.1 to 0.3.16 came out of
that process. None of the candidates for 0.3.17 was adopted: where a gain was measured, it came
with regressions elsewhere or did not hold up against the identity (A/A) controls, and the reports
say so.

The reports, the experiment scripts and the charts are in [lab-notebook/](lab-notebook/README.md).
The release notes are in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
