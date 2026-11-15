# kestrel-server: PostgreSQL wire protocol front end

`kestrel-server` lets `psql`, psycopg and other PostgreSQL drivers talk to KestrelSQL over TCP. It
speaks the PostgreSQL v3 frontend/backend protocol (simple and extended query, SCRAM-SHA-256) and
runs the KestrelSQL SQL subset. It is the supported network front end of KestrelSQL, with the
limits listed under [Limits](#limits) and [Limitations](#limitations): one user, no TLS, plain
TCP meant for loopback or a tunnel, and a deliberately small SQL subset.

It does not replace the engine's own limits. It is a front end for exactly the SQL that
`kestrel_sql::sql::parse` accepts: `CREATE TABLE`, `INSERT ... VALUES`, `SELECT` with `COUNT`,
`SUM`, `AVG`, `MIN`, `MAX`, `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`, `EXPLAIN`,
`BEGIN`/`COMMIT`/`ROLLBACK` and `CHECKPOINT`. Nothing is translated: a query that KestrelSQL cannot
parse is an error with SQLSTATE `42601`.

`CHECKPOINT` writes a snapshot of every table and starts an empty write-ahead log (command tag
`CHECKPOINT`). It is refused inside a transaction block (`25001`) and in `--archive` mode, which
has no log (`0A000`). The engine also checkpoints by itself when the log grows large.

## Run it

```
cargo build --release
printf '%s\n' 'choose-a-long-password' > server.pw
target/release/kestrel-server --db ./data --password-file server.pw
```

On start it prints one JSON line on stdout, then serves until killed:

```
{"listening":"127.0.0.1:5433","backend":"db","version":"0.4.0"}
```

Connect:

```
PGPASSWORD=choose-a-long-password psql -h 127.0.0.1 -p 5433 -U kestrel -d anything
```

```python
import psycopg
conn = psycopg.connect(host="127.0.0.1", port=5433, user="kestrel", dbname="x", password="...")
conn.execute("SELECT COUNT(*), SUM(value) FROM events WHERE ts >= %s AND ts < %s", (100, 200))
```

The database name in the startup packet is ignored.

## Flags

There are no environment variables; everything is a command-line flag.

| Flag | Default | Meaning |
| --- | --- | --- |
| `--db DIR` | | Serve a `Database` (in-memory tables, write-ahead log in `DIR`). Exactly one of `--db` / `--archive`. |
| `--archive DIR` | | Serve a `LiveArchive` in `DIR`: concurrent durable appends, `SELECT` through snapshots. |
| `--columns a,b,c` | `ts,value,device` | Archive column names (`--archive` only). |
| `--table NAME` | `events` | Archive table name (`--archive` only). |
| `--password-file FILE` | required | First line is the password (trailing newline stripped). The server refuses to start without it. Printable ASCII only. |
| `--user NAME` | `kestrel` | The one user name that may log in. Any other name gets `28P01`. |
| `--listen ADDR` | `127.0.0.1:5433` | Port `0` picks a free port; the JSON start line shows the real one. A host name is resolved once, and exactly the addresses that passed the loopback check are bound. |
| `--allow-remote` | off | Permit a non-loopback `--listen` address. Prints a warning on stderr. |
| `--max-connections N` | `64` | Authenticated sessions. A further login is told `53300` and closed. Connections still in startup or authentication do not count here; they have their own cap (see [Limits](#limits)). |
| `--max-memory MIB` | `1024` | Memory that all requests in flight may use together: message buffers, parsed statements, materialised results, encoded replies. A request that cannot get its share fails with `53200` or `54000` and the connection stays usable. See [Memory](#memory) for what it bounds and the worst case it adds up to. |

Exit status is `2` for any configuration error (nothing is printed on stdout in that case).

**Logging.** The server writes one line per event (open, authenticated, closed, refused) to
standard error with a plain blocking write. Standard error must be drained or redirected to a file
(`2>>server.log`); if it is a pipe that nobody reads, the connection threads stall once the pipe
is full.

## Authentication and TLS

* **SCRAM-SHA-256** (RFC 5802, RFC 7677) in the way PostgreSQL does it: `AuthenticationSASL`,
  `SASLContinue`, `SASLFinal`. The mechanism list is just `SCRAM-SHA-256`; channel binding is not
  offered. HMAC, PBKDF2 (4096 iterations) and base64 are implemented in `scram.rs` on top of the
  `sha2` crate and checked against the RFC 7677 test vector. The proof is compared in constant time.
* The server derives a SCRAM verifier (salt, stored key, server key) from the password file at start
  and keeps only that. The password is never logged. The client proves knowledge of the password
  without sending it, and the server proves it back (mutual authentication).
* **There is no TLS.** `SSLRequest` and `GSSENCRequest` are answered `N`. SCRAM protects the
  password, but queries and results travel in clear text, and a network attacker could still hijack
  an authenticated session. Keep the server on loopback, or put it behind an SSH tunnel or stunnel:

  ```
  ssh -N -L 5433:127.0.0.1:5433 user@db-host      # then connect to 127.0.0.1:5433 locally
  ```

  A non-loopback `--listen` address is refused unless `--allow-remote` is given, and the server then
  prints a one-line warning.
* The startup packet must arrive within **2 seconds** of the connection (a client that says
  nothing, or drips bytes, is cut off then), and the whole startup + authentication phase has a
  hard **10-second** deadline that a slow client cannot extend. Before authentication a message may
  be at most 64 KiB. Once authenticated there are no timeouts.
* A wrong user and a wrong password both give `28P01`, at the same step: an unknown user name is
  put through the same SCRAM exchange against a stand-in verifier (salt and keys derived from the
  name with a per-process secret, so the salt is stable per name and no password matches), so the
  reply does not tell which of the two was wrong. The log records only that authentication failed
  for a (sanitised, truncated) user name.
* A failed authentication is answered after a **1-second delay**, in that connection's own thread,
  which keeps its pre-authentication place for that second. This slows online guessing to about
  one guess per second per pre-authentication place.
* Non-ASCII passwords are refused at start because SASLprep is not implemented.

**Connection slots and the residual risk.** `--max-connections` counts authenticated sessions
only, so sockets that connect and stay silent cannot lock real users out. Connections that have
not authenticated yet are limited separately, to `max(16, 2 * --max-connections)`; one beyond that
is closed without an answer. A client that can reach the port can still keep that
pre-authentication pool full by opening sockets again as fast as they time out, and then new
logins are dropped. The server has no way to tell such a client from a real one before
authentication, which is why the default listen address is loopback: expose it only on a network
you control (SSH tunnel, firewall rule), never to the internet.

## Backends

### `--db DIR`

A `kestrel_sql::Database` behind a mutex. `CREATE TABLE` and `INSERT` work. If the database reports
that it is poisoned after an I/O failure, every statement returns `XX000` with the engine's
message. **The server must then be restarted**: the write-ahead log is reopened and recovered on
start. If a thread panics while holding the database, the same applies.

A `COMMIT` that fails with `XX000` and "commit outcome unknown" hit an I/O error while writing or
syncing the log. **The transaction may or may not have been persisted**: the record can be
complete on disk even though the call failed. Do not assume it was not applied; after restarting,
read the data back to find out. Every other commit error (for example another connection created
the same table first, or a transaction whose log record would exceed 64 MiB, `54000`) is
reported before anything is written, and nothing of the transaction is applied.

### `--archive DIR`

A `kestrel_sql::live::LiveArchive`: one fixed table (`--table`, `--columns`). `SELECT` runs on an
immutable snapshot without any lock. `INSERT INTO <table> VALUES (...),(...)` becomes one append
batch (one segment, durable before the reply), at most 10,000 rows per statement or transaction
(`54000` above that). `CREATE TABLE` is refused with a clear error (`42601`), as is `EXPLAIN`.
Archive queries do not list rows (see [ARCHIVE.md](ARCHIVE.md)).

## Transactions

`Database` has one transaction state shared by everything, so connections never use it
concurrently. Instead:

* Outside `BEGIN ... COMMIT` every statement is autocommit: it takes the lock, runs, releases it.
* Inside a transaction a connection **queues** its `INSERT` / `CREATE TABLE` statements. They are
  validated when issued (syntax, table exists, row width, duplicate table), so mistakes surface
  where they happen.
* **Reads inside a transaction do not see that transaction's own uncommitted writes.** `SELECT`
  always reads committed data, also data committed by other connections in the meantime.
* At `COMMIT` the server takes the lock, runs `begin()`, applies the queue, `commit()`. If a
  statement fails (for example another connection created the same table first) or the commit is
  refused, it rolls back, returns the error, and the session is idle again; nothing of the
  transaction is applied. The one exception is a commit that fails with "commit outcome unknown"
  (`XX000`, an I/O error): see [`--db DIR`](#--db-dir), the transaction may have been persisted.
  After any commit error the server also rolls the shared `Database` back, so it never stays
  inside a transaction. In `--archive` mode the queued inserts are appended as **one** batch, so
  one atomic segment.
* As in PostgreSQL, any error inside a transaction block puts it in the failed state: every
  statement answers `25P02` until `ROLLBACK`, and `COMMIT` of a failed transaction returns the tag
  `ROLLBACK` and applies nothing. `ReadyForQuery` reports `T` (in a transaction), `E` (failed) or `I`.
* Several statements in one simple-query string form one implicit transaction (all or nothing)
  unless the string contains `BEGIN`/`COMMIT`/`ROLLBACK` itself. The same read rule applies: a
  `SELECT` in that string does not see the string's own inserts.
* In the extended protocol each `Execute` outside an explicit transaction is its own autocommit
  statement (there is no implicit transaction until `Sync`).
* A transaction may queue at most 100,000 statements and 1,000,000 rows (`54000`). Queueing a
  statement costs the same however long the queue already is.
* **Memory per connection.** Everything a connection keeps between messages is counted against a
  budget of 256 MiB: the text of prepared statements, the statements and parsed rows queued in a
  transaction, and the rows of portals that were suspended with a row limit. The count is an
  estimate of real memory (8 bytes per integer plus per-row and per-object overhead, the SQL text
  itself). A request that would pass the budget fails with `54000`; it is an ordinary error
  (`ERROR`, not `FATAL`), so **the connection stays usable**. Inside a transaction block it puts
  the transaction in the failed state like any error, which also frees the queue. `Close`,
  `DEALLOCATE`, `ROLLBACK` or `COMMIT` give the memory back.
  Prepared statements keep only their text and parameter types; the statement is parsed again at
  `Bind` and `Execute`. This budget is for what a connection *keeps*; what a request needs *while
  it runs* comes from the shared `--max-memory` budget, see [Memory](#memory).
* **Portals follow the protocol.** A new `Bind` to the unnamed portal replaces the previous
  unnamed portal. Every portal ends with its transaction: at `COMMIT` or `ROLLBACK` inside a
  transaction block, and at `Sync` (or the end of a simple query) outside one. A portal cannot be
  executed again after that (`34000`); bind it again in the same batch.

## Protocol support

* Startup, `SSLRequest`/`GSSENCRequest` (answered `N`), `CancelRequest` (accepted and ignored),
  `Terminate`. Protocol 3.x minor versions and `_pq_.` options get `NegotiateProtocolVersion`.
* Simple query (`Q`) with several `;`-separated statements, trailing `;`, comments, and
  `EmptyQueryResponse` for an empty string.
* Extended query: `Parse`, `Bind`, `Describe` (statement and portal), `Execute` (with row limits and
  `PortalSuspended`), `Close`, `Sync`, `Flush`; named and unnamed statements and portals. After an
  error everything is discarded until `Sync`.
* Parameters `$1..$n` must be integers. Text format must parse as `i64` (anything else, including
  `NULL`, `1.5`, `1e3` and surrounding spaces, is `22P02`); binary format is accepted for
  `int2`/`int4`/`int8`. The server substitutes the values as integer literals.
* Result columns: `int8` (OID 20) for integer values, `float8` (701) for `AVG`, `text` (25) for
  `EXPLAIN`. Text and binary result formats are supported (binary `int8` is 8 bytes big-endian).
  An integer that does not fit `bigint` (a `SUM` above 2^63-1) is `22003`, never a wrong number.
* `DEALLOCATE [PREPARE] name|ALL` as plain SQL (psycopg sends it).
* Command tags: `SELECT n`, `INSERT 0 n`, `CREATE TABLE`, `EXPLAIN`, `BEGIN`, `COMMIT`, `ROLLBACK`,
  `CHECKPOINT`, `DEALLOCATE`.
* ParameterStatus: `server_version` (`16.0 (KestrelSQL <version>)`), `client_encoding` `UTF8`,
  `DateStyle`, `integer_datetimes` `on`, `standard_conforming_strings` `on`, and a few more.

## Limits

| Limit | Value | Result |
| --- | --- | --- |
| Message size after authentication | 16 MiB | `54000`, connection closed |
| Message size before authentication | 64 KiB | `54000`, connection closed |
| Startup packet | 10,000 bytes | `08P01`, connection closed |
| Startup packet arrives within | 2 s | connection closed |
| Startup + authentication time | 10 s | connection closed |
| Delay before a failed login is answered | 1 s | `28P01` after the delay |
| Authenticated sessions | `--max-connections` (64) | `53300`, connection closed |
| Connections still authenticating | `max(16, 2 * --max-connections)` | dropped without an answer |
| Prepared statements / portals per connection | 1,000 each | `54000` |
| Memory kept by one connection (statement text, queued writes, suspended portal rows) | 256 MiB (estimated) | `54000`, connection stays usable |
| Memory used by all requests in flight together (message buffers, parsed statements, results, replies) | `--max-memory` (1024 MiB) | `53200` if it is in use by others right now, `54000` if the request alone is more than all of it; connection stays usable |
| Statements queued in one transaction | 100,000 | `54000` |
| Rows queued in one transaction | 1,000,000 | `54000` |
| Log record of one commit (`--db`) | 64 MiB (engine) | `54000`, nothing applied |
| Archive rows per `INSERT` / transaction | 10,000 | `54000` |
| Rows in a result | 100,000 (engine) | `54000` |

A malformed message closes that connection only; the server and every other connection keep
running. One thread serves each connection.

## Memory

The server's memory is bounded by a formula, and both parts of it are enforced in code.

**What is counted where**

* *Kept* memory is what a connection holds between messages (prepared statement text, queued
  transaction writes, rows of suspended portals): at most **256 MiB per connection**, `54000` past
  it (see [Transactions](#transactions)).
* *Transient* memory is what one request needs while it runs and gives back when it ends. All
  connections draw it from **one shared budget, `--max-memory` (default 1024 MiB)**. A request
  reserves its bytes before it allocates them and gives them back when the request ends. The
  reservation is an RAII ticket, so it is returned on an error, an early return, a closed socket
  and a panic alike. What is reserved, in the order a request meets it:
  1. **The message body.** It is reserved as the bytes arrive (the buffer doubles, and the old
     block is counted while it is copied), so a client that announces 16 MiB and sends nothing
     holds nothing.
  2. **Copies out of the message** (a `Parse` copies its text, a `Bind` builds a list entry per
     parameter): a fixed multiple of the message size.
  3. **Parsing.** `kestrel_sql::sql::parse_estimate` reads the text once without allocating and
     bounds the token vector and the syntax tree (below). The tokens are given back when the parse
     returns; the tree stays reserved until the request ends.
  4. **The queued copy of a write and the work of applying it**: the columns the engine builds, its
     second parse of the text, and the JSON log record (`serde_json` builds it in a vector that
     doubles, so it is counted three times, and it is built before the 64 MiB limit is checked).
  5. **The result.** Before a `SELECT` runs, its rows are bounded from the statement and from the
     table's size, read under the same lock the query runs under: at most 100,000 rows, one row for
     aggregates without `GROUP BY`, `LIMIT` when no `ORDER BY` needs every row. After it ran the
     reservation shrinks to what the rows really hold.
  6. **The encoded reply.** Reserved before the rows are encoded; the output buffer is cut back to
     1 MiB after it was flushed.
* Every request may use `FREE_ALLOWANCE` = 256 KiB without reserving. That keeps `Sync`,
  `ROLLBACK` and small statements working when the budget is used up.

**What a refusal looks like.** The request fails as an ordinary `ERROR`, so the connection stays
usable and the reservation is already back. Two codes:

* `53200` (`out_of_memory`): the budget is in use by other requests right now. Try again.
* `54000`: this request alone is more than the whole `--max-memory`; retrying cannot help.
  Send less at a time, or start the server with more.

The server does not wait for memory to become free; it answers at once. A request that holds part
of its memory while waiting for the rest can deadlock against another that does the same (a
half-received message holds its buffer), and a client can retry as cheaply as the server can wait.
A message that is refused part-way is still read to its end and thrown away, so the connection
stays in step with the protocol. Each refusal is logged (`refused 53200 ...`), and every
connection logs `transient memory: N in use, peak P, limit L bytes` after it closed and returned
everything: the last one to close reports 0, and `peak` never passes `limit`.

**The worst case.** With `C` = `--max-connections` and `M` = `--max-memory`:

```
resident memory  <=  database data
                     + C * (256 MiB + 1.5 MiB)          kept per connection, and its fixed part
                     + M                                 transient, all connections together
                     + max(16, 2C) * 80 KiB              connections still authenticating
```

The fixed part of a connection is 1 MiB of pending output (`OUT_KEEP`), the 8 KiB read buffer, the
256 KiB free allowance and a little for error texts. A connection that has not authenticated
yet holds one message of at most 64 KiB and its buffers. Thread stacks are not counted here: one
thread per connection, 2 MiB of address space each, of which only the touched part is resident.
`database data` is the tables themselves (the engine bounds them per table, not in bytes), and the
automatic checkpoint that follows a commit works in proportion to them, not to the request.

With the defaults (`C` = 64, `M` = 1024 MiB): 64 * 257.5 MiB + 1024 MiB + 128 * 80 KiB =
16,480 + 1,024 + 10 = **17,514 MiB (about 17.1 GiB) plus the data**, of which only the 1,024 MiB
is spent in bursts; the 256 MiB per connection is a ceiling that an idle or ordinary client never
comes near. To size a host, lower `--max-connections` (kept memory scales with it) and
`--max-memory`. For example `--max-connections 8 --max-memory 256` is at most
8 * 257.5 + 256 + 1 = 2,317 MiB plus the data.

**How the estimates were made, and checked.** Each is an upper bound derived from the code that
allocates, not a typical figure:

* The lexer keeps one 32-byte token per token in a vector that doubles, so a statement costs up to
  32 bytes per byte of text (a token needs at least one byte), 48 with the old block that exists
  while the vector doubles, plus a string for each word and operator. A bulk `INSERT` also builds
  one `Vec<i64>` per row (the vector starts at one value and grows by doubling from four); any other
  statement builds at most about 116 bytes of tree per token (a column list `a,a,a`), bounded as 160.
  The text is read once to count tokens, rows and values, so a typical insert is charged about 50
  bytes per byte of text (the densest one 79) instead of a flat worst case. A column list is
  charged 450, because the engine parses the text again when it runs the query.
* Result rows: a `Value` is 32 bytes, a grouped query also holds one map entry and one state vector
  (64 bytes per expression) per group, and the row vector doubles while it grows.
* `size_of::<Token>() == 32`, `Item == 56`, `Value == 32` and the state size are asserted by tests,
  and tests build real statements and results (dense and sparse inserts, wide rows, column lists,
  garbage text, 300 random strings, grouped and sorted queries) and compare the capacities of what
  they really hold with the estimate. A heap allocation is assumed to take up to 32 bytes more than
  asked (header and rounding).
* The whole request was measured on the release binary (Windows 11, Rust 1.99): a script starts the
  server, sends one 16 MiB statement from 1, 8 or 32 connections, and reads the process's peak
  working set and peak commit with `GetProcessMemoryInfo`; the server's own `peak` log line is the
  reservation. `--max-memory 16384` so that nothing is refused:

| Request (16 MiB of SQL) | Real peak commit | Real peak working set | Reserved |
| --- | --- | --- | --- |
| bulk `INSERT`, rows like `(1700000000, 42, 7)` | 525 MiB | 387 MiB | 778 MiB |
| `INSERT` of `(1),(1),(1),...` (the densest) | 786 MiB | 689 MiB | 1,264 MiB |
| `INSERT` of 64-column rows | 143 MiB | 111 MiB | 233 MiB |
| `SELECT a,a,a,...` (a column list) | 2,472 MiB | 2,393 MiB | 7,200 MiB |
| `!!!!...` (a token each, fails to parse) | 929 MiB | 787 MiB | 3,872 MiB |
| `begin;begin;...` (2.8 million statements) | 552 MiB | 509 MiB | 1,352 MiB |
| 8 connections, bulk `INSERT` each | 2,585 MiB | 1,965 MiB | 4,668 MiB |

  The reservation is above the real figure in every row. Version 0.4.0 allowed all of this: a
  single `SELECT a,a,a,...` took 2.4 GiB of working set and eight bulk inserts took 1.9 GiB, with
  `--max-connections 64` allowing 64 of them. With the default budget, the same eight bulk inserts
  peak at 525 MiB commit (387 MiB working set): one runs and seven are told `53200`; 32
  connections peak at 614 MiB commit (409 MiB working set) with 31 told `53200`; the `SELECT a,a,a,...`
  is refused with `54000` and the server grows by 17 MiB, the message itself.
  `benchmarks/server_memory.py` repeats the measurement.

**What is not covered.**

* A client that stops reading its results keeps its reservation while the server waits to write
  to it (there is no timeout after authentication), so enough of them can make other requests
  fail with `53200`. They cannot make the server use more memory.
* The live archive's own ingest queue and the working memory of its `GROUP BY` are the engine's;
  the server reserves the columns it hands over (24 bytes per value) and, for a grouped query on
  an archive, rows for the 100,000-group maximum because it does not know the table size.
* Checkpoints and everything else the engine does in proportion to the stored data.

## SQLSTATE codes

| Code | When |
| --- | --- |
| `42601` | Syntax error, unsupported statement, wrong number of values, `CREATE TABLE`/`EXPLAIN` in archive mode |
| `42P01` | Unknown table |
| `42703` | Unknown column |
| `42P07` / `42701` | Table exists / duplicate column |
| `42P05` / `42P03` / `26000` / `34000` | Duplicate or missing prepared statement / portal |
| `42P18` | Parameter number used inconsistently |
| `22P02` | Parameter is not an integer (text) or is `NULL` |
| `22P03` / `0A000` | Binary parameter with the wrong length / of an unsupported type |
| `22003` | Result does not fit `bigint` |
| `28P01` | Wrong user or password |
| `28000` | No user name, or an SASL mechanism that is not offered |
| `25P02` | Statement in a failed transaction |
| `25001` | `CHECKPOINT` inside a transaction block |
| `0A000` | `CHECKPOINT` in `--archive` mode (also: binary parameter type, protocol version, replication) |
| `53200` | The shared `--max-memory` budget is in use by other requests right now; try again |
| `53300` | Too many authenticated sessions |
| `54000` | A limit above was exceeded, including a request that alone needs more than `--max-memory` |
| `08P01` | Protocol violation |
| `XX000` | Internal error, including a poisoned database (restart the server) and "commit outcome unknown" (the transaction may have been persisted) |

## Limitations

* No TLS (see above), no GSSAPI, no other authentication methods, one user.
* Only the KestrelSQL SQL subset. There is no `SET`, `SHOW`, `pg_catalog`, `information_schema`,
  `SELECT 1`, `COPY`, cursors or savepoints, so tools that introspect the catalog on connect (many
  GUI clients, JDBC's `SET extra_float_digits`) will fail. `psql`, psycopg (use `autocommit=True`
  with `conn.transaction()`, or plain `commit()`/`rollback()`; nested transaction blocks use
  savepoints) and drivers that only run queries work.
* Reads inside a transaction do not see its own writes (see above).
* `CancelRequest` is ignored; a running query cannot be cancelled.
* Results are materialised before they are sent (at most 100,000 rows), and their memory is reserved
  from `--max-memory` first (see [Memory](#memory)).
* `NULL` parameters are rejected; there are no `NULL` columns, only `SUM`/`AVG`/`MIN`/`MAX` of no rows.
* After an I/O failure the `--db` database must be restarted (see above), and a commit that failed
  with "commit outcome unknown" may have been persisted.
* A client that can reach the port can keep the pre-authentication pool full (see
  [Authentication and TLS](#authentication-and-tls)); this is why the default is loopback.
* Standard error must be drained or redirected to a file (see [Flags](#flags)).
