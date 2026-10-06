# Changes

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
