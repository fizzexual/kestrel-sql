# Live metrics and replayable ingestion

KestrelSQL 0.3 adds `LiveArchive`, a concurrent embedded wrapper around the disk-backed `Archive`. Version 0.3.1 improves retry and compaction costs and exposes publication-stage timings. It is intended to demonstrate exact time-window metrics during ingestion, with durable batch retries and stable read views. SQL coverage remains the narrow BIGINT aggregate subset documented in [ARCHIVE.md](ARCHIVE.md).

## Try the Rust workflow

```powershell
cargo run --release --example live_ingest -- path-to-a-fresh-store
```

[live_ingest.rs](examples/live_ingest.rs) appends two events, captures a snapshot, retries the same batch, and inserts a late event. The pinned view continues to see two rows totaling 30; a new view sees three totaling 37. Use a fresh directory for this demonstration. The persisted IDs can also be retried after reopening.

Clone `LiveArchive` to share it between application threads. `append(IngestBatch { id, columns })` blocks until durable publication and a new read view are complete. Column vectors must have identical lengths and match the store schema. `snapshot()` returns an `Arc<ArchiveSnapshot>` that can be queried without holding the writer's execution lock. Its generation is fixed; acquiring a new snapshot observes subsequent publications.

## Retry contract

An ID identifies one exact payload within one archive. Valid IDs contain 1–128 ASCII letters, digits or `-_.:/`. Identified batches must be nonempty. SHA-256 covers column count, row count and every original column value in original order, before sorting. Same ID and same payload returns `duplicate: true` and its original receipt generation; a changed payload is rejected. IDs are preserved through compaction and reopening. Anonymous appends always insert again.

The catalog stores rows and receipts in one publication. A lost connection or publication I/O error can leave an unknown outcome: reopen and retry the same ID and exact payload. There is no silent receipt eviction; after 100,000 distinct IDs, new identified batches fail. A capacity test verifies that old exact retries still succeed after reopening a full ledger. Version 0.3.1 checks replay-only groups without copying committed receipts; new publications still serialize the entire receipt ledger, whose long-term write cost remains unqualified. This is batch idempotency, not a transaction spanning an external source offset and multiple sinks. Different IDs with the same rows are deliberately distinct batches.

Up to 64 already queued requests share a synchronized segment/catalog publication. No fixed batching delay is imposed. An invalid or conflicting member causes its entire group to fail before publication; independent callers in that group can retry. I/O failure poisons the writer and requires reopening. Graceful destruction of the last wrapper drains the accepted queue and joins the writer.

## Resource and maintenance behavior

The wrapper admits at most 256 requests and 64 MiB of payload bytes, with at most 10,000 rows per request. A full admission queue reports that the batch was not accepted. This bounds queued payload, not all client memory or process RSS.

At 64 small segments, the writer merges up to 32 runs under a 65,536-row/64 MiB payload ceiling. Reads continue on immutable snapshots; compaction itself occupies the writer and can delay later appends. Every 32 groups the writer reclaims superseded catalogs and retired segments that no snapshot pins. Caller-held old snapshots can retain disk files. Crash orphans and pending files are left for inspection; automatic complete orphan cleanup and retention policies are not delivered.

A shared FIFO cache retains at most 32 MiB of decoded boundary pages and exact i128 page prefixes. It avoids repeat file reads and prefix construction; it does not cache complete query results. Generic scans, compaction and full integrity scrubs bypass it. Active queries can retain evicted pages, and OS caches are additional memory. A full scrub failure clears the shared cache. External edits to an open archive are unsupported; cached pages may reflect earlier validated bytes until a scrub detects damage.

Each live or pinned segment retains one file handle for boundary reads at explicit offsets. Those reads do not depend on a shared file cursor or repeatedly reopen segment paths. Version 0.3.1 also uses these handles for checked compaction input reads. Long generic queries and verification use independent scan handles; this avoids serializing long scans on one synchronous Windows handle. Snapshots retain boundary handles until their segment references are released. Old snapshots can therefore retain file handles as well as disk files; this is not a global handle-budget guarantee.

`live.stats()` reports queue bytes, durable groups, committed/duplicate batches, compactions, maintenance failures and total/maximum publication time. Snapshot stats include generation, row/segment counts, durable ID count, retained cache bytes and cache hits/misses. `publication_profile` adds stage counts, totals, maxima and eight histogram buckets; compare counters before and after a workload. Inclusive boundaries are 0.1, 1, 5, 20, 100, 500 and 1,000 ms, followed by an unbounded bucket. The preparation stage includes validation and sorting, or compaction input reads and sorting. Timings are process-local and shared across pinned snapshots, rather than part of their fixed data generation. These are diagnostics; a complete production health and admission-control interface remains work.

## Executed pipeline demonstration

[live_pipeline_demo.py](benchmarks/live_pipeline_demo.py) generates two Parquet sources, reads them through DuckDB, and feeds source-hash/chunk-ID microbatches through the loopback test adapter. It replays both files, appends late data, reopens, checks results against DuckDB and rejects changed content under an existing ID. The 0.3.1 results are saved in [live-pipeline-031-results.json](portfolio/live-pipeline-031-results.json); [live-pipeline-results.json](portfolio/live-pipeline-results.json) preserves the 0.3 run.

```powershell
python benchmarks/live_pipeline_demo.py
```

This requires the pinned benchmark dependencies. It is a runnable ingestion example; Kestrel has no native Parquet or Arrow SDK yet. `kestrel-stress.exe` is an unauthenticated loopback JSON test adapter, with no production server/API contract.

## Format and readiness

0.3 reads legacy `KSQLCAT2` catalogs and writes `KSQLCAT3` catalogs containing batch receipts. Segment payloads remain `KSQLSEG2`. A 0.2 binary must reject a 0.3 catalog; it must not silently erase receipt history. Take backups before experimental upgrades. The RAM-resident `Database` API remains a separate engine path with its earlier SQL/WAL behavior.

Current tests, forced process kills and repeated comparisons are reported in [PERFORMANCE_031.md](PERFORMANCE_031.md); [V03_RESULTS.md](V03_RESULTS.md) preserves the earlier release. Physical power loss, Windows directory-entry durability, long endurance, backups, replication, broad SQL types and a stable migration contract remain unqualified. See [RESEARCH.md](RESEARCH.md) for the next evidence gates.
