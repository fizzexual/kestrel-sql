# Changes

## 0.4.0 (2026-11-15)

- **PostgreSQL-protocol server, `kestrel-server`.** Serves a `Database` or a `LiveArchive` to
  `psql`, psycopg and other PostgreSQL drivers: simple and extended query, prepared statements,
  binary integers, transactions, `CHECKPOINT`. Login is SCRAM-SHA-256 (hand-written on `sha2`,
  checked against the RFC test vectors); a password file is required, and it listens on loopback
  unless `--allow-remote` is given. Limits on logins in progress, authenticated sessions, memory per
  connection (256 MiB) and statements per transaction. No TLS. See [docs/SERVER.md](docs/SERVER.md).
  New dependency: `getrandom`, for login nonces.
- **Design and interview guide** in [docs/DESIGN.md](docs/DESIGN.md).

- **Fixed: `Database` could refuse to open after a power cut.** A log whose end read back as zeros or
  garbage (the write in flight when the power went) was treated as corruption. Damage with no
  complete, checksummed frame after it is now cut off as the unfinished last write and reported by
  `Database::recovered_tail_bytes()` and a CLI warning. Damage followed by a complete frame is still
  refused, and the file is left untouched. A log whose header was never finished opens as empty.
- **Checkpoints.** `Database::checkpoint()`, the `CHECKPOINT` statement, and an automatic checkpoint
  once the log is larger than both 64 MiB and the last snapshot. The snapshot stores each column as
  zigzag-encoded differences: 10 million rows take 32 MB instead of a 151 to 216 MB log. Directories
  written by 0.3.16 open unchanged as generation 0.
- **Tests:** power-cut states built byte by byte (`tests/durability.rs`), and fuzzing of SQL, logs,
  snapshots and archive files (`tests/fuzz.rs`). The every-byte corruption test now expects a damaged
  last frame to be cut instead of refused.
- **CI** also runs on Linux, the fault-injection build and Rust 1.89, the minimum in `Cargo.toml`.
  130 tests pass on Windows (current Rust) and on Linux with Rust 1.89.
- **Measured three times:** range totals at 9.5 million rows 0.065 ms (`Database`) against DuckDB's
  2.11 ms; reopening 10 million rows 0.82–1.01 s after a checkpoint instead of 1.28–2.81 s from the
  log. Tables in the README.

## 0.3.16 post-release service qualification (2026-10-07)

- Added 52 fresh million-row service cases, 1,327,600 offered operations and independently audited raw accounting/read/write percentiles. The current six-engine comparison has 3/5 mixed-p99 median wins, 4/5 read-p99 wins and 2/5 append-p99 wins; all slower results and dropped/failed requests remain visible.
- Preserved the failed 60-second soak, all 27 existing-policy experiments, original harness snapshots, 0.3.16 source/binaries/qualification, and validated old-debug-cache cleanup records. Reconciliation checked 66,569 acknowledged batches and 171 uncertain committed batches.
- Engine source, binaries, default policy and release packages remain unchanged. Documented a research-backed publication-format hypothesis with explicit recovery, compatibility and reclamation gates; no candidate format is implemented. See [SERVICE_047.md](lab-notebook/SERVICE_047.md).


## 0.3.16 experimental packed medium key-cache candidate

- Store exact signed keys and checked u32 group indexes plus one in 16-byte entries, reducing the promoted table from 384 to 256 KiB on this 64-bit build. Preserve cache promotion/demotion/budgets, HashMap authority, counts, exact i128 reductions, reader ownership and durable formats/source/writer policy.
- Select the trial under predeclared primary/guard criteria, then independently rebuild and remeasure all 60 DuckDB shapes and paired 1M/tiny/10M/100M controls. Preserve every slower guard and both initial build failures.
- Pass 77 Rust tests in both modes and both Clippy configurations, including zero/signed keys, real tag collisions, wide sums/AVG and the new footprint. Pass 4,000 SQL cases against each reference, 104 manual bridge oracles and current crash/retry/source/Parquet checks. [Every result and limit](lab-notebook/PERFORMANCE_046.md).

## 0.3.15 experimental bounded reader reuse candidate

- Retain at most one idle, exclusively owned stream file per segment, with a 128-idle-file shared archive budget. Concurrent readers never share a file cursor. Fresh full scrubs bypass reuse; I/O/checksum failures invalidate handles. Segment retirement releases the budget without adding snapshot references.
- Preserve an unselected offset-only trial and every slower guard. Independently rebuild and measure 60 DuckDB shapes, fragmented/tiny queries and dense/sparse/high-cardinality/scan/10M/100M controls. Group kernels, serialized formats, publication policy and source contracts retain exact preceding source identity.
- Pass 76 Rust tests in debug/release, both Clippy configurations, 4,000 SQL cases against each DuckDB/SQLite and 104 manual bridge oracles, including eight concurrent clients. Verify bounded retention, snapshot retirement, warm corruption/truncation, cold reopen, confirmed retries and current fault/process-kill/Parquet checks. [Every result and limit](lab-notebook/PERFORMANCE_045.md).

## 0.3.14 experimental adaptive sparse SUM candidate

- Avoid rewriting exact cache-hit tags. Fuse a shared SUM/AVG into sparse lookup only for blocks entered with the small cache active; retain the preceding wider and fallback mapper, dense kernels, readers and storage policy.
- Preserve four trials, including wide/high-cardinality fusion regressions. Rebuild and compare the selected adaptive kernel with 60 fresh shapes and small/wide/irregular/high-cardinality/dense/scan/tiny/10M/100M controls.
- Pass 74 Rust tests in both modes, both Clippy configurations and 4,000 SQL cases against each DuckDB/SQLite. Confirm exact signed wide shared SUM/AVG JSON, retry/reopen and current publication/source/process-kill/Parquet checks. Preserve and repair a test-only Clippy failure. [Every result and limit](lab-notebook/PERFORMANCE_044.md).

## 0.3.13 experimental fused dense SUM candidate

- Fuse key validation, exact row counts and shared i128 SUM/AVG updates in one pass over selected dense-group rows. Retain existing mixed-reduction and sparse paths; no additional query allocation or storage-format change.
- Preserve released-baseline profiles, development trial source/binary and final 10M/100M pairs, all guards and 60 fresh query shapes with every win/loss.
- Pass 73 Rust tests in both modes, both Clippy configurations, 3,400 SQL cases against each DuckDB/SQLite, exact dense/sparse wide JSON, confirmed retry/reopen and current publication/source/process-kill/Parquet checks. [All measurements and limits](lab-notebook/PERFORMANCE_043.md).

## 0.3.12 experimental medium sparse-cache candidate

- Promote a 16,384-slot exact-tag cache only after measured key reuse and another nonempty block. Limit it to 8,192 keys, one promotion attempt and a 50% hit-rate gate; retain the authoritative randomized HashMap and exact i128 reductions.
- Preserve the first trial's 75–79% tiny-query regression, then defer allocation to recover this guard. Retain source, binaries, raw trials, 60 fresh query shapes and final paired controls.
- Pass 72 Rust tests in both modes and both Clippy configurations, 2,800 SQL cases against each DuckDB/SQLite, signed wide JSON, confirmed retry/reopen and current publication/source/process-kill/Parquet checks. Promoted queries add 384 KiB on this computer. Every loss and guard stays visible in [PERFORMANCE_042.md](lab-notebook/PERFORMANCE_042.md).

## 0.3.11 experimental seeded group-cache candidate

- Index sparse-group cache slots with a per-query odd multiplier derived once from the existing randomized HashMap state. Retain exact signed tags, authoritative mapping, typed i128 state, cache bounds and fallback.
- Replace obsolete fixed-slot collision assumptions with real collisions generated for each actual seed. Verify counts/sums, fallback and cache release without weakening the tests.
- Preserve released 0.3.10 sources/binaries and the trial. Retain 55 fresh query shapes, 21 alternating collision/guard pairs and separate stage profiles.
- Pass 70 Rust debug/release tests and both Clippy configurations, 2,200 SQL cases against each DuckDB/SQLite, plus current retry, publication, corrupt catalog, forced kill, source, Parquet and wide JSON checks. Every loss remains in [PERFORMANCE_041.md](lab-notebook/PERFORMANCE_041.md).

## 0.3.10 experimental direct-filter candidate

- Build positions directly from the first scan predicate not already enforced by sorted bounds; keep later comparisons, aggregation, CRC reads and publication policy intact.
- Preserve the unsuccessful separate-function trial, initial profiles and pre-release direct-filter measurements. Rebuild final binaries and compare them against released 0.3.9, 0.3.8 and DuckDB.
- Add a public-API regression test for six operators, signed extremes, reordered filters and partial blocks across overlapping runs, including reopen. All 70 tests pass in debug/release and both Clippy configurations.
- Check 1,600 queries against each DuckDB/SQLite, current publication faults, corrupt catalogs, process kills, source retries, wide JSON and the Parquet workflow. Keep all 45 matrix shapes and losses. See [PERFORMANCE_040.md](lab-notebook/PERFORMANCE_040.md).

## 0.3.9 experimental sparse-grouping candidate

- Increase the direct-address ceiling to 65,536 slots while keeping the conservative 8 MiB budget. Expanded domains also fit the archive row count.
- Map arbitrary signed keys through the standard randomized HashMap to typed shared reductions, avoiding per-group Cell vectors and duplicate SUM/AVG work. Report `streamed-hash-group` for this fallback.
- Add a 256-entry tagged key cache, with exact collision checks, a 128-key ceiling and block hit-rate disabling. Specialize the disabled path so it has no per-row cache checks; preserve the measured first-cache regressions.
- Add six correctness tests; all 69 pass in debug/release and Clippy. Check 1,000 SQL cases against DuckDB/SQLite, wide JSON, publication failures, corrupt catalogs, forced kills, source replay and the Parquet pipeline.
- Preserve 81 current engine/fixture/round cases, all 45 shapes, 5,530 paired control samples and both intermediate candidates. Disclose the remaining unordered-scan regression; keep storage/publication/CLI/source formats and policy unchanged. See [PERFORMANCE_039.md](lab-notebook/PERFORMANCE_039.md).

## 0.3.8 experimental adaptive-grouping candidate

- Select query-local direct-address aggregation for bounded integer spans (4,096 slots, conservative 8 MiB limit), with hash fallback for sparse or wider domains and the existing result budget.
- Share membership/counts and exact i128 SUM/AVG reductions; use narrow MIN/MAX arrays and dispatch outside row loops. Report `streamed-dense-group` for the selected strategy.
- Preserve signed extrema, holes, filters, empty groups, aliases, limits, pinned snapshots, compaction/reopen and payload checksums. Add six tests; all 63 pass in debug/release and Clippy.
- Compare 0.3.7, 0.3.8 and DuckDB in 54 rotated cases at 1M/10M/100M rows and real taxi data. Preserve the initial candidate, fixture mistake, every loss, short paired controls and separate profiles. See [PERFORMANCE_038.md](lab-notebook/PERFORMANCE_038.md).
- Fix existing CLI/bridge panics on wide SUM results by serializing typed JSON directly; preserve exact i128 numeric tokens without dependency-feature changes.
- Recheck current publication cut points, corrupt catalogs, concurrent kills, source retry/crash behavior and the Parquet pipeline. Keep storage/publication/live/source behavior unchanged; claim no new requests/s envelope or production qualification.

## 0.3.7 experimental source-checkpoint candidate

- Add `SourceArchive` with exclusive archive ownership, source positions and contiguous half-open interval commits. Publish source identity/offsets in a canonical durable receipt ID alongside its exact output, with no checkpoint file or extra sync.
- Recover at most 4096 source positions through a borrowed receipt prefix range. Reject malformed reserved IDs, gaps, overlaps, branches and reversed original generations; retain all receipts under the existing 100K ceiling.
- Preserve exact retries, original generations, source/data atomicity, poisoned-owner behavior, stable pinned views and compaction/reclaim. Source identifiers are bounded UTF-8 labels hashed under a versioned domain; positions are u64.
- Add 10 tests, a Rust SDK demo, exact failure/forced-kill checks and a Parquet/SQL workflow. Compare against matched manually encoded IDs and retain stalls; claim no durable-write speed fix.
- Keep live/prepared ingestion, SQL/query/WAL behavior and CAT4/SEG2 unchanged. Empty-output advances, source reset, consumer leases/fencing and retention are not implemented. See [PERFORMANCE_037.md](lab-notebook/PERFORMANCE_037.md).

## 0.3.6 experimental reusable-batch candidate

- Add immutable, process-local `PreparedBatch` and `LiveArchive::append_prepared` for embedded input reuse. Hash once inside the library, share caller-owned vectors through Arc, and compare confirmed original receipt identity without hashing/copying every retry.
- Keep fingerprints and payloads private; reject invalid IDs/shapes/limits and archive-width mismatch. Unknown/pending IDs retain ordinary bounded admission, publication hashing and synchronized ACKs. Prepared input is not a durable receipt.
- Preserve index-off and zero-delay defaults, writer health checks, original generations and CAT4/SEG2 compatibility. Add a prepared-hit counter as a subset of confirmed fast retries.
- Test immutable ownership, conflicts, reopen, cross-archive input and concurrent first submissions. Extend the feature-only driver to prepared submissions, stalled-writer checks, disk-full failures and exact process exits.
- Preserve a weak/slower chunked-hash CPU trial without adopting it. Publish ordinary, amortized-preparation and preparation-per-call controls with all raw samples. See [PERFORMANCE_036.md](lab-notebook/PERFORMANCE_036.md).

## 0.3.5 experimental opt-in live-retry candidate

- Offer `LiveArchive::with_retry_index` to validate confirmed retries independently of the live writer queue, optional collection window and publication I/O. Preserve exact submitted payload identity, original receipt generation and visibility before any success.
- Clone the bounded receipt lookup once at startup and extend only successfully published IDs after publishing their read view. Pending and unknown IDs retain writer admission and whole-group validation.
- Reject known and new appends after observed writer poisoning or exit. Keep old snapshots readable. Expose fast retry hits/conflicts, validation time, lookup logical memory and writer health.
- Add pending-ID races, order/shape/content/reopen regression tests and a feature-only deterministic stalled-writer/poison driver. Preserve the 0.3.4 package, source, binaries and initial retry evidence.
- Preserve the unsuccessful always-on trial and keep the added lookup off in `new` and `with_options`. Disabled wrappers allocate no second receipt map; compare final defaults and enabled behavior on the same binary.

## 0.3.4 experimental coalescing-policy candidate

- Add `LiveOptions.max_group_delay` and `LiveArchive::with_options`; keep `LiveArchive::new` at zero delay and reject optional windows above 20 ms.
- Use one deadline from the first received request, without extending it for arrivals, with at most 64 requests/group. Drain a disconnected queue without waiting. Preserve synchronized publication and read-view visibility before ACK.
- Expose exact configured nanoseconds, measured collection time, collected-group count and largest request group. Intentional waiting and actual ACK latency are separate quantities.
- Test concurrent delayed acknowledgments, pinned snapshots, retries, option limits, queue draining and crash/reopen behavior. Repeat every 0/2/8 ms policy on the same binary, retaining losses, slower settings and actual collection overshoot.
- Keep storage/query/WAL source unchanged; inherit the prior correctness evidence by verified source hashes rather than counting it as fresh testing. Preserve the 0.3.3 source, binaries and package. See [PERFORMANCE_034.md](lab-notebook/PERFORMANCE_034.md).

## 0.3.3 experimental receipt-catalog candidate

- Write CAT4 receipt deltas between full checkpoints, retaining at most 32 catalog dependencies. Every catalog still contains the complete current segment set.
- Serialize borrowed old/new receipt maps at checkpoints; eliminate the committed-ledger clone from new appends and compaction. Keep the 100K ID ceiling and original replay receipt generations.
- Read CAT2/CAT3/CAT4 and reject damaged/missing dependencies, duplicate receipt keys, invalid generations/parents and excessive chain depth. Older writers reject CAT4.
- Preserve buffer flush, segment/catalog synchronization, atomic publication, unknown-outcome poisoning and pinned-reader behavior. Reclaim retains the complete current catalog chain.
- Expose checkpoint/delta counts, published catalog bytes and snapshot chain length. Add sequential new-ID probes, concurrent 50K-ID fixtures and a separately feature-enabled cut-point driver.
- Preserve the 0.3.2 source/binaries, all raw baseline samples, service failures and older release artifacts. See [PERFORMANCE_033.md](lab-notebook/PERFORMANCE_033.md) for focused gains and remaining limitations.

## 0.3.2 experimental scan candidate

- Reuse query-local byte and decoded-column buffers across streamed pages, preserving CRC validation and independent long-scan handles.
- Apply residual predicates through reusable row selections, choosing the comparison operator outside the row loop. Reuse already established sorted bounds.
- Evaluate ungrouped COUNT/SUM/AVG/MIN/MAX by selected batches with exact i128 sums and existing empty-input behavior.
- Add opt-in `ArchiveSnapshot::query_profiled` with query-local scan counts and stage timings; ordinary queries use a specialization without per-block timing work.
- Add an independent oracle test for extreme integers, partial pages, empty selections, all comparison operators and profile counts. Preserve the original 0.3.1 binaries/source and separate instrumented baseline.

The focused alternating filter comparison improves, but repeated service cases fail the zero-loss/100 ms gate and expose long publication stalls. See [PERFORMANCE_032.md](lab-notebook/PERFORMANCE_032.md). The 0.3.1 package remains unchanged; this candidate is not production-qualified.

## 0.3.1

- Validate exact batch retries against the existing receipt ledger without cloning it. Copy committed receipts only when new rows require publication; keep conflicting retries and whole-group atomicity checks.
- Buffer segment and catalog writes, explicitly flush before synchronization, and preserve the existing durable acknowledgment and on-disk format.
- Reuse immutable segment handles for checked positional compaction reads. Long query scans and integrity verification retain independent handles.
- Skip duplicate-only snapshot publication and avoid a second ordinary GROUP BY hash lookup.
- Expose process-local publication-stage timings and histograms for preparation, writes, synchronization, catalog encoding and rename.
- Test the full 100,000-ID capacity, reopen and exact retries. Add three-round rotating comparisons against five other engines, host observations, direct query/retry probes, and preserved intermediate regressions.

See [PERFORMANCE_031.md](lab-notebook/PERFORMANCE_031.md) for versioned raw evidence and remaining failures. This release remains an experimental prototype.

## 0.3.0

- Add immutable `ArchiveSnapshot` views and a public concurrent `LiveArchive` wrapper. Readers keep a stable committed generation while a single writer ingests or compacts.
- Coalesce already queued requests into durable group publication; bound admission by request count, payload bytes and per-request rows. Publish the read view before acknowledging the append.
- Persist batch IDs, SHA-256 payload identities and original receipt generations. Exact retries are deduplicated across reopen and compaction; changed payloads are rejected.
- Add bounded small-run compaction and reclaim superseded catalogs/retired files when no snapshot pins them. Crash orphans remain inspectable.
- Cache decoded boundary pages and exact page prefixes under a 32 MiB retained-data budget. Full verification bypasses the cache and invalidates it on failure.
- Retain immutable segment handles and read payloads at explicit offsets, avoiding repeated file opens while preserving concurrent-reader correctness.
- Skip aggregate page work for an empty bounded range. Report cache, group publication and maintenance diagnostics.
- Read legacy version-2 catalogs; write version-3 receipt catalogs that older binaries reject. Segment payload format remains version 2.
- Add runnable Rust and Parquet replay/backfill examples, concurrent/snapshot/cache regression tests, identified retry testing after 24 forced process kills, fresh competing-engine results and a primary-source research notebook.

All performance evidence, including unsuccessful iterations and repeated-run variation, is retained. SQL coverage remains the existing integer aggregate subset. This release is a research prototype; durability tail latency and the operational gates in [RESEARCH.md](lab-notebook/RESEARCH.md) still require work. See [V03_RESULTS.md](lab-notebook/V03_RESULTS.md).

## Historical releases

0.1 explored full in-memory prefix indexes and a transactional WAL path. 0.2 introduced immutable disk-backed column segments, sparse aggregate indexes, late batches and 100M-row/NYC pipeline experiments. [BENCHMARK.md](lab-notebook/BENCHMARK.md), [SCALE.md](lab-notebook/SCALE.md) and [HARD_TESTS.md](lab-notebook/HARD_TESTS.md) retain those version-specific measurements.
