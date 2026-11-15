# How KestrelSQL works, and why

This page explains the design in the order an interviewer would ask about it. Each answer gives the
idea, the cost, and the number that shows it. The code references point at the place to read.

## 1. Why are range totals so fast?

Each column keeps, next to its values, the exact running total up to every row
(`Column::prefix` in [src/lib.rs](../src/lib.rs)). The running total is 128 bits wide, so it cannot
overflow: 10 million values of at most 2^63 add up to less than 2^87.

For `SUM(value) WHERE ts >= a AND ts < b`, when `ts` is in nondecreasing order:

1. Two binary searches find the first row with `ts >= a` and the first with `ts >= b`.
2. The sum is `prefix[end] - prefix[start]`, the count is `end - start`, and the average is the two
   divided.

That is O(log n) work and reads no rows. At 9.5 million rows it answers in 0.057 ms against
DuckDB's 1.6 ms ([hard test](../benchmarks/hard-test/README.md)).

**The cost:** 24 bytes per value instead of 8, and the totals are computed on every append. Range
totals are the one query this engine is built for; everything else is an ordinary scan.

## 2. Why does DuckDB win when the whole table is read?

Grouping all 9.5 million rows takes 270 ms in `Database` and 5.6 ms in DuckDB. Running totals do not
help a query that has to look at every row, so the question becomes how fast each engine scans, and
DuckDB is much better at that:

- it processes vectors of values with SIMD instructions and compresses its columns;
- it uses every core (held to one thread it takes 66.5 ms, still 4× faster);
- KestrelSQL's grouped scan is a plain single-threaded loop over `Vec<i64>`.

The honest answer in an interview: KestrelSQL moves the work of range totals to write time. It
does not try to be a fast general scanner, and the README says so.

## 3. Why do late rows break the in-memory fast path?

The binary search needs the filter column to be sorted. `Column::append` keeps a `monotonic` flag,
and the first value smaller than the one before it clears it. After that, range queries on that
column fall back to a correct scan. With 5% late rows, range totals go from 0.057 ms to 43.9 ms.

`Archive` does not have this problem: every published batch is sorted and indexed on its own, and
each 4,096-row block stores its minimum, maximum and running total. A query binary-searches inside
each segment and skips the segments whose range cannot match, so it stays at 0.395 ms with the same
late rows.

## 4. Why is an acknowledged write safe when the process dies or the power goes?

**`Database`** ([src/wal.rs](../src/wal.rs)) writes each committed transaction as one frame:

```
"KTX1" | size u32 | !size u32 | CRC-32 of payload u32 | JSON payload
```

The frame is written and `fsync`ed before `COMMIT` returns. At open the log is replayed frame by
frame. A power cut can only damage the write that was in flight, so:

- damage with **no complete frame after it** is the unfinished last write: it is cut off and the cut
  is reported (`Database::recovered_tail_bytes`, and a warning from the CLI);
- damage **followed by a complete frame** cannot come from a power cut. The database refuses to
  open and leaves the file as it is.

The size and its complement catch a damaged length before it is trusted. Version 0.3.16 refused
the second case of a power cut (the file's end reading back as zeros) and would not open; that was
found and fixed while testing this ([what was found](#8-what-was-found-by-testing)).

**`Archive`** ([src/archive.rs](../src/archive.rs), `publish`) never changes a file in place:

1. write the new segment, `fsync` it;
2. write the new catalog to `catalog-N.pending`, `fsync` it;
3. rename it to `catalog-N.ks2`, `fsync` the directory (on Linux).

The catalog with the highest number is the state. A crash before step 3 leaves an orphan file that
is ignored; after it, the new state is complete. Every block of every segment has a CRC-32 that is
checked when it is read.

**After an I/O error the handle is poisoned.** If `fsync` fails, the data may or may not be on disk,
and on Linux a second `fsync` can report success without writing anything (PostgreSQL's
"fsyncgate", 2018). So the engine does not retry. It reports "commit outcome unknown" and refuses
further work until it is reopened and recovery decides.

## 5. How does the log stop growing? (checkpoints)

Without a checkpoint, reopening replays every transaction ever committed. A checkpoint writes all
tables to a snapshot and starts an empty log:

1. `snapshot-{g+1}.tmp` is written and synced;
2. it is renamed to `snapshot-{g+1}.ksnap` and the directory is synced;
3. `events-{g+1}.ksql` is created with its header and synced;
4. the files of generation `g` are deleted.

At open, the highest complete snapshot decides the generation, so a power cut at any step leaves
either the old pair or the new one. A failure after step 2 poisons the handle, because the new
snapshot may already be the recovery point and later commits to the old log would be lost.

A checkpoint runs automatically after a commit once the log is larger than both 64 MiB and the last
snapshot, so rewriting the snapshot never costs more than the log it replaces. `CHECKPOINT` runs one
by hand.

**A measurement that changed the design:** the first snapshot stored each value in 8 bytes and was
*bigger* than the log (240 MB against 151 MB for 10 million rows), because JSON writes small numbers
in fewer bytes. The snapshot now stores each value as the difference from the one before,
zigzag-encoded in as few bytes as it needs (`encode_run`): a clock that ticks by one takes one byte
per row. The same 10 million rows take 32 MB, 4.7× smaller than that log and 6.7× smaller than the
log of a million small commits.

## 6. Why is a retried batch stored only once?

A network client that times out does not know whether its write landed. In `Archive` a batch can
carry an ID, and the catalog keeps a SHA-256 digest of each ID's data. Sending the same batch again
returns the original receipt; sending different data under the same ID is refused. In the hard
test, 1,200 batches interrupted by a kill and re-sent were each stored exactly once.

`LiveArchive` ([src/live.rs](../src/live.rs)) puts concurrent writers in front of one archive and
groups their batches into one durable publish (group commit), so many writers share one `fsync`.
Readers take an immutable snapshot and never wait for writers.

## 7. How does a PostgreSQL client talk to it? (the server)

`kestrel-server` ([src/bin/kestrel-server/](../src/bin/kestrel-server/)) speaks the PostgreSQL v3
wire protocol, so `psql`, psycopg and other drivers connect without a KestrelSQL client library.
The protocol is message-based: one type byte, a 4-byte length, the body. The server implements the
simple query (`Q`) and the extended query (`Parse` / `Bind` / `Execute` / `Sync`), which is what
drivers use for prepared statements and parameters. One thread per connection.

**Login is SCRAM-SHA-256** (RFC 5802 and 7677), the PostgreSQL default since version 14. The
server never stores or receives the password itself: it keeps a salted, iterated key, and client
and server each prove they know it. HMAC, PBKDF2 and base64 are written by hand on top of `sha2`
([scram.rs](../src/bin/kestrel-server/scram.rs)) and checked against the RFC test vectors; the only
new dependency is `getrandom` for the nonces.

**Transactions without blocking other connections.** `Database` has one transaction state, so two
connections cannot both be inside `BEGIN` on it. Each connection therefore queues its writes and
validates them when they are issued. At `COMMIT` the server takes the lock once, applies the queue
inside one engine transaction and commits it: all of it or nothing. The cost, written down in
[SERVER.md](SERVER.md): a `SELECT` inside a transaction does not see that transaction's own
uncommitted rows.

**What a hostile or broken client cannot do** (each found by a review told to break the server,
each with a test in [tests/server.rs](../tests/server.rs)):

| Attack | Defence |
| --- | --- |
| Open sockets and send nothing, to use up the connection slots | Connections still logging in have their own cap; the startup message must arrive within 2 s and login finish within 10 s |
| Prepare huge statements or queue millions of rows until memory runs out | 256 MiB budget per connection for everything kept between messages; over it is an ordinary error (`54000`) and the connection stays usable |
| Find out which user names exist | An unknown user goes through the same SCRAM exchange as a real one and fails at the same step |
| Guess passwords quickly | Every failed login is answered after 1 s |
| Make the queue check slower with every statement (O(n²)) | Running counters; queueing costs the same at 20,000 statements as at the first |
| A failed `COMMIT` leaving the shared database inside a transaction | The server rolls back after every commit error |

Not defended: no TLS (it listens on loopback unless `--allow-remote` is given), and the memory used
while one statement of up to 16 MiB is parsed is not counted against the budget.

## 8. What was found by testing

| Found | How | What changed |
| --- | --- | --- |
| A power cut that leaves zeros at the end of the log made `Database` refuse to open | Building every power-cut state byte by byte ([tests/durability.rs](../tests/durability.rs)) | Damage with nothing valid after it is cut and reported |
| An 8-byte snapshot is bigger than the JSON log | Measuring it ([examples/restart_probe.rs](../examples/restart_probe.rs)) | Delta and zigzag encoding, 32 MB instead of 240 MB |
| The SQL fuzzer first reached the parser's valid paths 52 times in 20,000 | Counting accepted statements | Grammar-based generation; 4,510 of 20,000 now parse |
| A torn log header longer than 16 bytes, a leftover file that could not be deleted, and an oversized transaction left half-applied | A review told to break the checkpoint code | One test per finding in [tests/durability.rs](../tests/durability.rs), then the fix |
| Silent sockets, memory growth, user-name probing and an O(n²) queue in the server | A review told to break the server | The defences in section 7; 10 of the 13 new tests failed on the code before the fix |

## 9. How it is tested

- **Against five other engines:** 4,000 random queries compared with DuckDB, SQLite, PostgreSQL,
  MySQL and MariaDB; 0 differences ([hard test](../benchmarks/hard-test/README.md)).
- **Power-cut states, built byte by byte:** every cut inside the last write, zeros, garbage, damage
  in the middle of the log, and a crash at each step of a checkpoint
  ([tests/durability.rs](../tests/durability.rs)).
- **Process kills:** 300 kills during writes in the hard test, plus a kill test in `cargo test`.
- **Fuzzing:** 25,000 random statements, 700 damaged logs and snapshots, 300 damaged archive files.
  Each must give an error or the correct answer, never a panic or a wrong answer
  ([tests/fuzz.rs](../tests/fuzz.rs)).
- **The server:** 27 tests that drive it over real sockets, including every attack in section 7,
  plus by hand with `psql` 17 (correct answers, `ROLLBACK`, `CHECKPOINT`, a restart that keeps
  every row, wrong passwords refused with `28P01`).
- **Platforms:** Windows and Linux, the newest stable Rust and the oldest supported (1.89): 130
  tests on both.

What is not tested: a real power cut on real hardware, and a filesystem-level simulator such as
LazyFS. The byte-by-byte states cover the standard model (only synced data survives); they cannot
cover a disk that lies about `fsync`.

## 10. What I would do next

- **Decimals** as scaled integers (`DECIMAL(18,3)` stored as `i64` thousandths), which keeps sums
  exact. Floating-point running totals would not be exact, because floating-point addition is not
  associative.
- **Parallel scans** over segments, the cheapest way to close part of the gap to DuckDB on
  whole-table queries.
- **TLS** in the server, which needs a dependency (`rustls`) the project has avoided so far.
