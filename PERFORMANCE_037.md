# KestrelSQL 0.3.7: atomic archive-local source positions

`SourceArchive` commits a nonempty output batch and its half-open source interval in **one existing synchronized receipt publication**. Reopening derives the resume position from that same durable receipt history; no second checkpoint file, separate write or additional synchronization is added. New intervals must start at the current source position. Known exact intervals return their original receipts after later commits; changed output is rejected. This supplies a practical archive-local recovery boundary for an embedded pipeline, without claiming distributed consumer fencing, a Kafka transaction or end-to-end exactly-once delivery.

## Contract

The wrapper exclusively owns `Archive`; mutable Rust access (or a caller's Mutex) serializes submissions. Each source is a case-sensitive 1..1024-byte UTF-8 identity, SHA-256 hashed with the domain `kestrelsql.source.v1\0`. Receipts reserve `ksrc1:SOURCEHASH:STARTHEX:NEXTHEX`: 104 ASCII bytes, fixed-width lower-case 16-digit offsets. The source position is caller-supplied `u64`; it need not equal output row count. The first nonempty interval anchors a new source at its supplied start; subsequent new intervals must be contiguous. Source identity aliases/human names are not persisted, so callers retain their source configuration. Ordinary receipts remain supported but are ignored as source positions.

Opening rebuilds at most 4,096 source positions by a borrowed BTreeMap prefix range, avoiding a clone/scan of unrelated receipt IDs. Sorted fixed-width offsets validate continuity and strictly increasing original generations. Malformed reserved IDs, gaps, overlaps, branches and reversed history fail closed. Callers must use this wrapper for reserved source receipts; manually writing them through generic/older writers bypasses its guard. The file format is compatible, but typed source semantics do not add access control or a security boundary.

The catalog already stores exact payload digest, row count and generation with each ID. Canonical intervals therefore survive compaction, reclamation and reopening with their output. The convenience map advances only after successful synchronized publication. I/O unknown outcomes poison the owner: position reads and all further commits reject until reopening. Previously captured immutable snapshots stay readable. A retry returns its original receipt generation; `position(source)` gives the latest resume offset, which may be later than the retried interval.

`commit(source, start, next, columns)` retains Archive limits (1M rows/64MiB per batch; 1..64 schema columns), plus advancing intervals and nonempty output. It cannot advance an interval that produced zero rows. The global 100K receipt ceiling applies across ordinary and source IDs; history is not silently evicted. The wrapper has no background writer, automatic retention, lease epoch, source reset, filtered-empty checkpoint or offset transaction spanning another sink. Maintenance is explicit through `compact_small` / `reclaim`. Source stats count keys/positions logically and exclude tree/allocator overhead.

The design follows Kafka's documented external-sink coordination principle: keep the consumed position with the output. This release only implements that boundary inside this archive. [Kafka design and delivery semantics](https://kafka.apache.org/32/design/design/), [Rust BTreeMap iteration](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html).

## Measured costs, including stalls

Three rotating rounds on the same Windows desktop, each with a fresh 0/50K-ID fixture and 96 sequential synchronized 100-row commits over four source identities. `baseline` is frozen 0.3.6 with manual canonical IDs; `ordinary` is 0.3.7 with the same manual IDs; `checkpoint` uses the new wrapper. Manual source hashing/ID construction occurs inside the same timing boundary. Data allocation, maintenance every 32 commits, scrubs, reconciliation, reopen and map reconstruction are outside per-commit timing. One thousand separately timed exact retries per case retain raw samples. This is a storage/SDK cost probe, not open-loop req/s or big-data/service qualification.

| Retained IDs | Variant | Median run p50 ms | Median run p99 ms | Run p99 range ms | Median retry p50 us | Source-map rebuild us |
|---:|---|---:|---:|---:|---:|---:|
| 0 | baseline | 54.71 | 489.67 | 121.30-708.62 | 12.20 | 0.10 |
| 0 | ordinary | 55.52 | 314.77 | 49.91-442.33 | 12.30 | 0.20 |
| 0 | checkpoint | 56.45 | 148.42 | 53.93-536.06 | 12.20 | 21.90 |
| 50,000 | baseline | 56.83 | 1171.03 | 1149.32-1313.95 | 12.10 | 0.20 |
| 50,000 | ordinary | 7.58 | 113.45 | 91.96-1107.29 | 12.10 | 0.30 |
| 50,000 | checkpoint | 6.57 | 215.27 | 86.65-1145.21 | 12.20 | 25.90 |

Catalog byte arrays match exactly across all nine cases per ID fixture. The checkpoint changes validation/resume behavior without adding a metadata publication to matched manual IDs. It uses longer IDs than short ordinary business IDs; that separate cost is not removed by this comparison. Four-source reconstruction after Archive open is around 22 to 26us; Archive catalog reopen costs are separately retained and can be much larger. Retries still hash ordinary payloads; this API does not use the 0.3.6 prepared fast path.

Write latency varies materially and includes roughly one-second tails; no causal write-speed improvement is claimed. The source wrapper's 215.27ms median run p99 at 50K retained IDs still fails a 100ms target. Segment/catalog synchronization represents 89.59% of seven measured publication stage totals on those three cases, including explicit maintenance; stage totals do not identify a device-level cause. All raw times, catalog bytes, retry samples and unsuccessful setup evidence remain preserved.

## Current evidence

- 55 Rust tests pass in debug and release, with format/Clippy for default and fault builds. New cases cover position/data reopen, old receipt generations, gaps/overlaps/stale offsets, bad shapes/budgets, Unicode/case-sensitive source identities, `u64::MAX`, invalid reserved histories, the 4096-source limit, unrelated receipts, compaction/reclaim/pinned views and 32 serialized first-submission callers.
- Fourteen exact publication tests (seven process exits, seven disk-full OS errors) recover through the default non-instrumented source adapter. They verify data/position atomicity, original generations, retry after a second reopen and full scrubs; poisoned owners reject checkpoint reads and old/new commits, while pinned reads work.
- Eight forced source-adapter terminations at different progress points preserve every acknowledged interval/generation, recover a contiguous data/position pair and replay/resume all 32 intervals without extra rows. Full scrubs and a second reopen pass. These are live-filesystem failures, not physical power-loss tests.
- A 30K-row, two-source Parquet demo commits 300 intervals, replays both sources, rejects changed output and a gap, reopens at 25K/5K source positions, and matches 42 DuckDB SQL cases. The Rust SDK demo verifies a stable pinned view, gap rejection, late output, replay and position/data reopening.
- Eighteen sequential comparison cases reconcile 1,728 new commits and 18,000 known retry calls; all original receipts, row/sum totals, catalog bytes and full scrubs match. Only task-owned local processes run; all builds precede timed cases.
- The initial correctness runner used a wrong nested JSON field for the already-passing SDK demo. Its source/error are preserved; only the corrected demo assertion reran. Fault/Parquet suites were retained and not restarted.

Archive storage/query/publication code is byte-identical to 0.3.6 apart from health visibility and a read-only receipt prefix iterator. Live ingestion, prepared-batch, SQL/query/WAL source hashes are unchanged. The 0.3.6 ZIP/source/binaries/proof and all older comparisons remain preserved. Prior SQL/100M/Parquet/corruption/open-loop/7.85M prepared-retry results are historical, not fresh 0.3.7 claims.

**Production qualification remains incomplete.** The feature addresses a local data/position recovery boundary; it does not solve write stalls, receipt retention, distributed fencing, broad types/SQL, native Arrow/Parquet, access control, cancellation, backup/restore or endurance.

## Reproduce and continue

Run `python benchmarks/preserve_036.py` before edits, `python benchmarks/checks_037.py`, `python benchmarks/source_compare.py`, `python benchmarks/run_037.py`, then `python benchmarks/report_037.py`, then `python benchmarks/package_release.py`. Use pinned benchmark dependencies for Parquet/DuckDB. Timed cases run serially; compilation and package work must finish outside timing. Runners preserve existing reports; `--demo-only` resumes that isolated check after successful prior suites.

Run `cargo run --release --example source_ingest -- FRESH_DIRECTORY` for the SDK demonstration. The stdin adapter is task-only benchmark tooling with limited error handling, not a production service/API. No database deployment or external messages are performed.

Continue profiling synchronized new-write/checkpoint tails; compare an append-only publication design only after defining a new fault-tested format. Extend the source contract with empty-output checkpoints, source registration/reset, bounded receipt retention and explicit lease epochs before calling it consumer fencing. Keep the receipt index disabled by default and retain the prior preparation-inclusive controls.

[Audit](benchmarks/source-037-audit.json), [build proof](benchmarks/rust-checks-037.json), [cost comparisons](benchmarks/source-037-comparison.json), [publication/kill checks](benchmarks/source-037-faults.json), [Parquet workflow](portfolio/source-pipeline-037-results.json), [SDK proof](benchmarks/source-037-demo.json), [correctness order](benchmarks/correctness-037-run-order.json), [preserved runner failure](benchmarks/source-037-initial-runner-failure.json), [baseline provenance](benchmarks/baseline-0.3.6-provenance.json), [prior performance](PERFORMANCE_036.md).
