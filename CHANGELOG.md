# Changes

## 0.3.4 experimental coalescing-policy candidate

- Add `LiveOptions.max_group_delay` and `LiveArchive::with_options`; keep `LiveArchive::new` at zero delay and reject optional windows above 20 ms.
- Use one deadline from the first received request, without extending it for arrivals, with at most 64 requests/group. Drain a disconnected queue without waiting. Preserve synchronized publication and read-view visibility before ACK.
- Expose exact configured nanoseconds, measured collection time, collected-group count and largest request group. Intentional waiting and actual ACK latency are separate quantities.
- Test concurrent delayed acknowledgments, pinned snapshots, retries, option limits, queue draining and crash/reopen behavior. Repeat every 0/2/8 ms policy on the same binary, retaining losses, slower settings and actual collection overshoot.
- Keep storage/query/WAL source unchanged; inherit the prior correctness evidence by verified source hashes rather than counting it as fresh testing. Preserve the 0.3.3 source, binaries and package. See [PERFORMANCE_034.md](PERFORMANCE_034.md).

## 0.3.3 experimental receipt-catalog candidate

- Write CAT4 receipt deltas between full checkpoints, retaining at most 32 catalog dependencies. Every catalog still contains the complete current segment set.
- Serialize borrowed old/new receipt maps at checkpoints; eliminate the committed-ledger clone from new appends and compaction. Keep the 100K ID ceiling and original replay receipt generations.
- Read CAT2/CAT3/CAT4 and reject damaged/missing dependencies, duplicate receipt keys, invalid generations/parents and excessive chain depth. Older writers reject CAT4.
- Preserve buffer flush, segment/catalog synchronization, atomic publication, unknown-outcome poisoning and pinned-reader behavior. Reclaim retains the complete current catalog chain.
- Expose checkpoint/delta counts, published catalog bytes and snapshot chain length. Add sequential new-ID probes, concurrent 50K-ID fixtures and a separately feature-enabled cut-point driver.
- Preserve the 0.3.2 source/binaries, all raw baseline samples, service failures and older release artifacts. See [PERFORMANCE_033.md](PERFORMANCE_033.md) for focused gains and remaining limitations.

## 0.3.2 experimental scan candidate

- Reuse query-local byte and decoded-column buffers across streamed pages, preserving CRC validation and independent long-scan handles.
- Apply residual predicates through reusable row selections, choosing the comparison operator outside the row loop. Reuse already established sorted bounds.
- Evaluate ungrouped COUNT/SUM/AVG/MIN/MAX by selected batches with exact i128 sums and existing empty-input behavior.
- Add opt-in `ArchiveSnapshot::query_profiled` with query-local scan counts and stage timings; ordinary queries use a specialization without per-block timing work.
- Add an independent oracle test for extreme integers, partial pages, empty selections, all comparison operators and profile counts. Preserve the original 0.3.1 binaries/source and separate instrumented baseline.

The focused alternating filter comparison improves, but repeated service cases fail the zero-loss/100 ms gate and expose long publication stalls. See [PERFORMANCE_032.md](PERFORMANCE_032.md). The 0.3.1 package remains unchanged; this candidate is not production-qualified.

## 0.3.1

- Validate exact batch retries against the existing receipt ledger without cloning it. Copy committed receipts only when new rows require publication; keep conflicting retries and whole-group atomicity checks.
- Buffer segment and catalog writes, explicitly flush before synchronization, and preserve the existing durable acknowledgment and on-disk format.
- Reuse immutable segment handles for checked positional compaction reads. Long query scans and integrity verification retain independent handles.
- Skip duplicate-only snapshot publication and avoid a second ordinary GROUP BY hash lookup.
- Expose process-local publication-stage timings and histograms for preparation, writes, synchronization, catalog encoding and rename.
- Test the full 100,000-ID capacity, reopen and exact retries. Add three-round rotating comparisons against five other engines, host observations, direct query/retry probes, and preserved intermediate regressions.

See [PERFORMANCE_031.md](PERFORMANCE_031.md) for versioned raw evidence and remaining failures. This release remains an experimental prototype.

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

All performance evidence, including unsuccessful iterations and repeated-run variation, is retained. SQL coverage remains the existing integer aggregate subset. This release is a research prototype; durability tail latency and the operational gates in [RESEARCH.md](RESEARCH.md) still require work. See [V03_RESULTS.md](V03_RESULTS.md).

## Historical releases

0.1 explored full in-memory prefix indexes and a transactional WAL path. 0.2 introduced immutable disk-backed column segments, sparse aggregate indexes, late batches and 100M-row/NYC pipeline experiments. [BENCHMARK.md](BENCHMARK.md), [SCALE.md](SCALE.md) and [HARD_TESTS.md](HARD_TESTS.md) retain those version-specific measurements.
