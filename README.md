# KestrelSQL

A small embedded analytics engine in Rust for **append-only integer time series**.

It answers `COUNT`, `SUM` and `AVG` over a time range in a few microseconds without reading the
rows. It runs embedded in a Rust program or as a server that `psql` and ordinary PostgreSQL drivers
connect to. Every on-disk state a power cut can leave behind is built in the tests, and 300 power
cuts on a file system that loses unsynced data (LazyFS) were survived: committed data is always
there, and a write cut off halfway is detected and removed on the next open.

**Status: version 0.4.0, built for production use in one narrow job:** append-only integer time
series on a single machine, with one table per query. It is not a general SQL database: no text,
no `UPDATE`, no joins, no replication. [What it does not do](#what-it-does-not-do) and
[what the tests do not cover](#crash-safety-and-tests) are part of the description, not footnotes.
How it works and why, written for a design review or an interview: [docs/DESIGN.md](docs/DESIGN.md).

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

## Two APIs and a server

- **`Database`** keeps tables in memory and writes every committed transaction to a log. It speaks
  the SQL subset below and has `BEGIN` / `COMMIT` / `ROLLBACK`. `CHECKPOINT` (also run
  automatically once the log reaches 64 MiB) writes a compact snapshot and starts a new log, so
  reopening does not have to replay the whole history. The benchmark in the next section measures
  this API.
- **`Archive`** is the on-disk store: sorted immutable segments, snapshots, compaction, and batches
  that can be retried safely. It answers totals and groupings through the same parser, but it does
  not list rows. `LiveArchive` puts concurrent writers in front of it.
- **`kestrel-server`** serves either one over the PostgreSQL wire protocol (simple and extended
  query, so `psql`, psycopg and JDBC-style prepared statements work), with SCRAM-SHA-256 password
  login. It listens on loopback only unless told otherwise, and it has no TLS. Details, limits and
  error codes: [docs/SERVER.md](docs/SERVER.md).

```
$ psql -h 127.0.0.1 -p 5433 -U kestrel
kestrel=> SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts >= 2 AND ts <= 4;
 count(*) | sum(value) | avg(value)
----------+------------+------------
        3 |         90 |         30
```

## How fast

One million rows, three columns, in memory, the `Database` API. Same data and the same SQL text in
both engines; every answer is compared and all of them agree.

SQLite is **not the fair rival** here: it is a row store built for transactions. It is in the table
because everyone has it and can check the result with one command. The fair comparison, against
DuckDB and three database servers at 10 million rows, is in the
[next section](#hard-test-against-five-engines).

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

## Hard test against five engines

Four tests that try to make it fail, run once on 2026-11-15 against DuckDB 2.0.0, SQLite 3.50.4,
PostgreSQL 17.12, MySQL 8.4.13 and MariaDB 11.4.13. Scripts, commands and raw results are in
[benchmarks/hard-test/](benchmarks/hard-test/README.md).

**Correctness.** 4,000 random queries over two datasets of 100,000 rows, one of them with 5% of the
rows arriving late. The five other engines agreed with each other on every query, and KestrelSQL
matched them on every query it accepts: 4,000 of 4,000 through `Database`, 3,554 of 3,554 through
`Archive` (which refuses the other 446 because they list rows).

**Crash.** The process was killed 300 times in the middle of writing. `Archive`: 150 kills under 8
concurrent writers; all 47,663 acknowledged batches were present and complete after every reopen,
and all 1,200 interrupted batches, re-sent with the same ID, ended up stored exactly once.
`Database`: 150 kills; all 15,491 acknowledged inserts were present and complete.

**Speed at 10 million rows.** Median milliseconds per query as the client sees it, 9.5 million rows
in time order. Every engine returned the same answers on all 792 queries.

| Query | KestrelSQL `Database` | KestrelSQL `Archive` | DuckDB | DuckDB, 1 thread | SQLite | PostgreSQL | MySQL | MariaDB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Totals over a random time range (300 queries) | 0.057 | 0.172 | 1.6 | 1.9 | 2.0 | 2.5 | 7.7 | 5.4 |
| `MIN`, `MAX` over a random time range (40) | 10.1 | 0.201 | 1.7 | 5.2 | 88.5 | 35.5 | 224 | 144 |
| Totals per device over a random time range (40) | 37.2 | 8.2 | 3.5 | 15.7 | 443 | 66.7 | 1,460 | 1,189 |
| Totals per device, whole table | 270 | 44.8 | 5.6 | 66.5 | 3,517 | 234 | 3,004 | 1,990 |
| Filter on unsorted columns (10) | 44.7 | 39.7 | 3.6 | 33.0 | 439 | 97.3 | 1,637 | 959 |
| Totals over a random time range, after adding 5% late rows | 43.9 | 0.395 | 1.9 | 3.6 | 2.3 | 2.6 | 7.4 | 6.2 |

**Load.** The project's own paced test with 64 clients and one million rows, 95% reads and 5%
appends. At 2,000 requests per second every engine served everything; KestrelSQL's 99th percentile
was 3.3 ms, SQLite's 2.0 ms. At 10,000 requests per second, an overload, KestrelSQL served 9,989 per
second and dropped nothing, SQLite served 9,588 and the other four between 6,907 and 7,534. Every
engine kept all its acknowledged writes in all 30 cases.

What this says:

- **It wins the query it was built for.** Totals over a time range are about 28 times faster than
  DuckDB through `Database` and 9 times faster through `Archive`.
- **It loses to DuckDB on everything that reads the whole table.** Grouping 9.5 million rows takes
  270 ms through `Database` against 5.6 ms, and DuckDB held to one thread still wins there.
- **`Database` depends on time order.** After 5% late rows its range totals go from 0.057 ms to
  43.9 ms, slower than every other engine in the table. `Archive` keeps its speed because each
  batch is sorted and indexed on its own.
- **Read it with these limits.** The table is one run. The three servers ran in Docker with near-default
  settings. DuckDB and SQLite ran inside the test process while KestrelSQL paid a round trip. The
  load test holds DuckDB to one thread and is partly limited by its Python client. A killed process
  is not a power cut. All data is synthetic integers that fit in memory.

**Repeated.** The speed test was run three more times on 2026-11-15 for the in-process engines
(the servers were not repeated), 0 disagreements in all three runs. Median of the three runs, with
the lowest and highest in brackets, in milliseconds:

| Query | KestrelSQL `Database` | KestrelSQL `Archive` | DuckDB | DuckDB, 1 thread | SQLite |
| --- | ---: | ---: | ---: | ---: | ---: |
| Totals over a random time range | 0.065 (0.052–0.068) | 0.218 (0.199–0.243) | 2.11 (1.85–2.19) | 1.83 (1.66–2.04) | 1.96 (1.96–2.08) |
| `MIN`, `MAX` over a random time range | 10.1 (5.3–11.9) | 0.186 (0.182–0.203) | 2.46 (2.17–2.66) | 6.42 (6.0–8.4) | 78.5 (77–92) |
| Totals per device over a random time range | 39.7 (28.5–60.3) | 8.49 (8.33–9.87) | 4.28 (4.01–5.42) | 19.5 (14.9–26.1) | 500 (478–660) |
| Filter on unsorted columns | 45.3 (27.2–77.4) | 45.3 (44.8–45.4) | 5.04 (4.77–6.64) | 42.5 (39.9–60.6) | 433 (389–448) |
| Totals over a random time range, after 5% late rows | 45.3 (18.0–64.3) | 0.373 (0.314–0.497) | 2.15 (2.08–2.36) | 4.24 (4.12–5.63) | 2.50 (2.14–2.72) |

The order is the same as in the single run: KestrelSQL wins range totals by about 30 times and
loses scans to DuckDB. The wide ranges in the `Database` scan rows are run-to-run noise on a
desktop machine.

**Restart time.** 10 million rows, reopened 7 times per run, three runs, median of each run:

| Log written as | Log size | Reopen from the log | After `CHECKPOINT` (32 MB snapshot) |
| --- | ---: | ---: | ---: |
| 1,000,000 commits of 10 rows | 216 MB | 2.45–2.81 s | 0.82–0.90 s |
| 1,000 commits of 10,000 rows | 151 MB | 1.28–1.44 s | 0.75–1.01 s |

The checkpoint itself took 153–180 ms. Reproduce with
`cargo run --release --example restart_probe -- DIR 10000000 10 7 synthetic`.

Older results from the project's history, including a mixed-load test that version 0.2 failed
(881 of 2,000 requests per second, [HARD_TESTS.md](lab-notebook/HARD_TESTS.md)) and the 0.3.16
service comparison ([SERVICE_047.md](lab-notebook/SERVICE_047.md)), are in the
[lab notebook](lab-notebook/README.md).

## What is inside

About 9,100 lines of Rust (2,700 of them the server), five direct dependencies (`serde`,
`serde_json`, `crc32fast`, `sha2`, and `getrandom` for login nonces), and `unsafe` code is
forbidden for the whole crate. The SCRAM, HMAC, PBKDF2 and base64 code is written on top of `sha2`
and checked against the RFC test vectors.

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

`cargo test` runs 147 tests; they pass on Windows with current Rust and on Linux with Rust 1.89,
the minimum version. The CI workflow in [.github/workflows/ci.yml](.github/workflows/ci.yml) runs
format, clippy and the tests on Windows and Linux, the tests with the minimum Rust version,
`cargo audit` against the RustSec advisory database, and 60 LazyFS power cuts. The
tests that say most about the design:

- **Power cuts, state by state** ([tests/durability.rs](tests/durability.rs)). A power cut can only
  leave a few kinds of state on disk: a last write cut at some byte, a file created but empty, a
  rename done or not done. The tests build each of them byte by byte, for the log and for every
  step of a checkpoint, and check that every acknowledged transaction is back after the open.
- **Power cuts on a real file system that loses data** ([benchmarks/lazyfs/](benchmarks/lazyfs/README.md)).
  [LazyFS](https://github.com/dsrhaslab/lazyfs), the fault-injecting file system Jepsen uses,
  drops every byte that was not `fsync`ed. 300 cuts at random moments, in the middle of
  checkpoints and as torn writes with holes: all 12,838,010 acknowledged rows came back, no run
  had a missing or half row. CI runs 60 cuts on every push.
- **The torn-tail rule.** Damage at the end of the log with no complete, checksummed transaction
  after it is an unfinished last write: it is cut off and reported (`recovered_tail_bytes`, and a
  warning in the CLI and the server). Damage followed by a valid transaction is real corruption:
  the open is refused and no file is changed. PostgreSQL and SQLite draw the same line.
- **Fuzzing** ([tests/fuzz.rs](tests/fuzz.rs)). 25,000 generated SQL statements (20,000 of them
  built from the grammar, of which 4,510 are valid), 700 damaged logs and snapshots, and 300 byte flips in archive files. No panic, and
  every damaged file is either refused or gives exactly an acknowledged prefix.
- **The server** ([tests/server.rs](tests/server.rs)): login, wrong passwords and unknown users
  (refused at the same step, after the same delay), prepared statements, concurrent transactions,
  restarts, connection and memory limits, and clients that stay silent or send garbage.
- `process_kill_preserves_acknowledged_commit_and_releases_lock`
  ([tests/engine.rs](tests/engine.rs)): kills a child process and checks that acknowledged commits
  survive and the lock is released.
- `concurrent_ingestion_retries_and_snapshot_reads_reconcile`
  ([tests/archive.rs](tests/archive.rs)): several writers and a reader at once, with an invariant
  checked on every snapshot.

When a write or sync fails, the handle is poisoned and reports **"commit outcome unknown"** instead
of guessing. A complete frame can survive even when its caller never got the acknowledgement, so
the application has to reconcile before retrying.

What the tests do not cover:

- **Real hardware.** Nobody pulled a plug. The tests assume the disk keeps what `fsync` said it
  kept; a disk that lies about `fsync` defeats any database.
- LazyFS drops unsynced file data; whether it also drops unsynced directory changes is not
  documented, so the rename steps of a checkpoint rest on the state-by-state tests.
- The archive's on-disk format gets fuzzing and single-offset corruption tests, not the every-byte
  sweep the log gets.
- The comparison against SQLite and DuckDB lives in `benchmarks/`, not in `cargo test`.

## What it does not do

- Values are signed 64-bit integers only. No text, no decimals, no native timestamps, no `NULL`
  input.
- One table per query. No joins, no subqueries.
- No `UPDATE` and no `DELETE`. Data is append-only.
- `WHERE` is a list of `column <op> integer` comparisons joined by `AND`. No `OR`, no `BETWEEN`, no
  arithmetic in expressions.
- Aggregates are `COUNT(*)`, `SUM`, `AVG`, `MIN` and `MAX` of a column. No `COUNT(column)`, no
  `DISTINCT`. `GROUP BY` takes one column.
- The `Database` API keeps everything in memory (up to 10 million rows per table). The `Archive`
  API is the on-disk store and has its own limits: it returns totals and groupings only and does
  not list rows.
- One machine. No replication, no backups other than copying the folder while it is closed.
- The server has no TLS (keep it on loopback or behind a tunnel), one user, no query cancellation,
  and runs one writer at a time. Its memory has a written worst case: each connection keeps at
  most 256 MiB, and all requests in flight share one `--max-memory` budget (1024 MiB by default);
  the formula is in [docs/SERVER.md](docs/SERVER.md#memory).

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

To serve it over the PostgreSQL protocol, put a password on the first line of a file and run:

```
./target/release/kestrel-server --db demo-db --password-file kestrel.pw
psql -h 127.0.0.1 -p 5433 -U kestrel
```

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
that process; 0.4.0 (checkpoints, the server, the power-cut and fuzz tests) did not, and is
described in the changelog. None of the candidates for 0.3.17 was adopted: where a gain was measured, it came
with regressions elsewhere or did not hold up against the identity (A/A) controls, and the reports
say so.

The reports, the experiment scripts and the charts are in [lab-notebook/](lab-notebook/README.md).
The release notes are in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
