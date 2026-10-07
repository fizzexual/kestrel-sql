# Individual publication-stage diagnostics: development 068

Measured 2026-10-07T10:34:07.662038+00:00. **Development 0.3.17-dev.68** is the exact released **0.3.16** core with an opt-in one-slot trace. It remains development-only. Supported source and binaries remain unchanged; no engine release or performance promotion occurs.

**Ten appends exceeded 500 ms. Eight checkpoint appends spent 91.88–98.01% of the call in `catalog_sync`. Two delta appends were dominated by `catalog_write` or `segment_write`.** The slowest append took 1935.4281 ms: 1896.9459 ms in catalog synchronization, while encoding took 29.9631 ms. These per-call observations identify the measured stage, not a physical device, filesystem, OS or antivirus cause.

This fresh cohort has **768 durable appends × 100 rows**,18 compactions and 18 separately timed reclaims, across six serial cases: two rounds with 0/50K/99K existing receipts/rows. There is no default-versus-trace, competing-engine or before/after speed comparison. Feature overhead remains unmeasured. All six stores and every event are preserved; no stalled case was discarded or retried.

## What changed

| Before: released 016 | After: opt-in diagnostic 068 |
|---|---|
| Aggregate stage totals, maxima and histograms across attempts | One current publication record correlates all seven existing stage durations with the same attempt/generation |
| Totals cannot say which stage dominated a particular long call | Per-call outer latency and recorded stages identify the largest measured stage and its fraction of that call |
| Released stats and snapshots | Same stats JSON and snapshot contract; the feature adds a writer-only getter and one 144-byte `Option<PublicationTrace>` |
| Same sync calls, receipt rules and disk format | Identical sync calls, receipt/checkpoint rules, output ordering, compaction fan-in and exact files |

The feature is disabled by default and its field/getter are absent in normal builds. It copies the durations already collected by the released engine rather than adding per-stage clocks or a history buffer. The probe buffers observations in memory and prints JSON once after the calls and validation. It creates no per-call diagnostic disk log.

`completed=false` represents an unknown durable outcome. No-op retries and calls rejected before publication leave the prior trace unchanged; callers must compare attempt/generation. Cold reopen resets the slot. Byte fields describe intended encoded payload/envelope sizes, not independently confirmed persisted bytes. The three new tests cover success/checkpoint/delta/compaction, failed publication/poison/reopen, bounded storage and unchanged stats schema. The original commentary's premature 136-byte estimate was corrected before timing; the measured slot is 144 bytes, under the predeclared 192-byte bound.

## Fresh measurements

Each case contains 128 named 100-row appends, maintenance at 64 live small runs, and the released 32-run merge cap. Input generation, getter/event capture, stats, SQL checks, CRC scrubs and cold reopen are outside append/compaction timers. The feature assignment itself is inside the engine call. Reclaim is timed separately. Prefill is captured separately and excluded from the 786 diagnostic publication events. No compilation, qualification, audit, packaging or Git work overlaps these timed calls; structured pre/post checks record no active task-owned processes.

The table is descriptive. All 128 append samples are included, and p99 uses Type7 interpolation. The same executable produces markedly different tails in the two rounds; these are not paired speedup ratios or latency guarantees.

| Case | Starting receipts/rows | Append p50, ms | Append p99, ms | Append max, ms | Appends >500 ms |
|---|---:|---:|---:|---:|---:|
| 00-r0-0 | 0 | 29.5058 | 169.1848 | 180.6474 | 0 |
| 01-r0-50000 | 50,000 | 2.5459 | 956.2964 | 1278.2685 | 4 |
| 02-r0-99000 | 99,000 | 2.3893 | 1868.3260 | 1935.4281 | 4 |
| 03-r1-50000 | 50,000 | 2.4272 | 574.5612 | 1906.1965 | 2 |
| 04-r1-99000 | 99,000 | 2.1096 | 87.4621 | 106.7827 | 0 |
| 05-r1-0 | 0 | 1.9452 | 3.0212 | 3.1783 | 0 |

All 18 compactions remain below500 ms, with maximum 112.2853 ms. None of the 18 reclaims exceeds500 ms. Cold reopen and full setup/validation runtime are recorded separately in each raw case.

Every slow append follows. Each named largest stage occupies more than half of its own outer call. The two delta stalls show why attributing every tail to large checkpoint serialization would be wrong.

| Case | Batch | Generation | Catalog | Outer, ms | Largest measured stage | Stage, ms | Fraction of this call |
|---|---:|---:|---|---:|---|---:|---:|
| 01-r0-50000 | 31 | 33 | checkpoint | 1278.2685 | catalog_sync | 1174.4273 | 91.88% |
| 01-r0-50000 | 63 | 65 | checkpoint | 906.4385 | catalog_sync | 885.9597 | 97.74% |
| 01-r0-50000 | 94 | 97 | checkpoint | 908.9363 | catalog_sync | 888.2760 | 97.73% |
| 01-r0-50000 | 125 | 129 | checkpoint | 973.8132 | catalog_sync | 952.2996 | 97.79% |
| 02-r0-99000 | 31 | 33 | checkpoint | 1894.6434 | catalog_sync | 1830.5880 | 96.62% |
| 02-r0-99000 | 63 | 65 | checkpoint | 1935.4281 | catalog_sync | 1896.9459 | 98.01% |
| 02-r0-99000 | 94 | 97 | checkpoint | 1778.4963 | catalog_sync | 1740.7540 | 97.88% |
| 02-r0-99000 | 125 | 129 | checkpoint | 1797.1716 | catalog_sync | 1758.8709 | 97.87% |
| 03-r1-50000 | 27 | 29 | delta | 1906.1965 | catalog_write | 1758.8893 | 92.27% |
| 03-r1-50000 | 28 | 30 | delta | 667.5434 | segment_write | 485.4155 | 72.72% |

Across all 768 appends, synchronization stages account for 82.95% of summed outer time, encoding 1.41%, and unmeasured residual work 1.13%. These are sums over this cohort, not a decomposition of a quantile or evidence of a physical cause. `segment_write` and `catalog_write` include creation/opening and writes; `catalog_sync` measures the existing catalog `sync_all` call.

| Stage | Summed append time, ms | Fraction of summed outer time |
|---|---:|---:|
| prepare | 20.9597 | 0.08% |
| segment_write | 910.0297 | 3.46% |
| segment_sync | 5202.3306 | 19.80% |
| catalog_encode | 371.5919 | 1.41% |
| catalog_write | 2539.1262 | 9.66% |
| catalog_sync | 16596.1634 | 63.15% |
| catalog_rename | 343.8426 | 1.31% |

## Correctness and durability

- ✅ **80 tests in debug and 80 in release**, format check, strict Clippy for default/trace/fault-only/trace+fault. All 77 existing tests execute with the three new feature tests in both modes. Default mode is compiled/linted; its 77 tests were not repeated without tracing.
- ✅ Full 13-suite qualification: **4,000 varied SQL cases per reference**, 56 publication cuts, 22 rejected corruptions, 32 concurrent forced-kill cycles, 14 source cuts, 8 source forced kills, 30,000 Parquet rows/300 source intervals/42 DuckDB oracles, 104 reader oracles and wide JSON/sparse-reopen checks.
- ✅ Every timed append and compaction passes. Exact COUNT/SUM, full CRC validation before and after cold reopen, and **18 known retries** preserve original generations. Cold retries leave the trace slot empty. **17,990,400 bytes** scrubbed across both passes.
- ✅ Every event conserves stage counts, totals, maxima and histograms against the released aggregate profile, plus catalog byte/checkpoint/delta counters. Seven stage durations fit within the corresponding outer call.
- ✅ Untimed released/default/traced archive comparison: **six full stores**,76 catalog and76 segment names byte-identical across all three builds; grouped receipt order, compaction, collisions, cold retries and catalogs over 16 MiB pass. Released/default code reopens traced files. The released control executable is reused from 067, not rebuilt.
- ✅ All **236 final diagnostic file instances / 58,153,438 bytes** independently hashed; both rounds at each history produce identical retained files. All32 group-kill stores and surviving qualification/test stores are retained in the private ZIP.
- ❌ No feature-overhead, end-to-end speed, service-load, competing-engine, physical power-loss or production qualification was attempted in 068. No supported promotion.

## Older performance evidence remains separate

[Buffer067](BUFFER_067.md) previously measured 17.1% less catalog encoding time at 50K receipts and 19.8% less at 99K. It failed one of four speed goals, four of 19 candidate guards and 11 of 24 identical-baseline checks, so it did not advance. Its writer buffer is absent from068. [Encoder models 065/066](ENCODER_PROFILES_065_066.md) and [compaction064](COMPACTION_064.md) also remain separate with every failed calibration/outlier preserved.

DuckDB wins/losses have **no new performance update** here; DuckDB is a correctness oracle in 068. Use the preserved [supported analytical comparison046](PERFORMANCE_046.md), [60-shape development061 result](CORE_READ_PATH_061.md) and [six-engine service047 wins/losses](SERVICE_047.md). Do not infer a PostgreSQL replacement or universal SQL victory from these diagnostics. [Adoption assessment](ADOPTION_STATUS.md).

## Reproduce and inspect

[Predeclared policy](benchmarks/trace-068/policy.json), [frozen case order/hashes](benchmarks/trace-068/diagnostic-policy.json), [raw case index](benchmarks/trace-068/diagnostic-results.json), [independent per-event audit](benchmarks/trace-068/diagnostic-audit.json), [final full-file inventory](benchmarks/trace-068/diagnostic-file-inventory.json), [qualification audit](benchmarks/trace-068/qualification-audit.json), [byte/reopen oracle](benchmarks/trace-068/byte-equivalence.json), [exact source provenance](benchmarks/trace-068/source-provenance.json), [runtime provenance](benchmarks/trace-068/runtime-provenance.json), [reproduction steps](benchmarks/trace-068/REPRODUCE.md) and [next work](benchmarks/trace-068/NEXT_WORK.md).

Individual stdout/status records, all build/qualification logs, original released core source and frozen normal/trace/fault/control binaries sit alongside these reports. Full stores are in the immutable private evidence ZIP. Earlier benchmarks, releases and the frozen morning report remain accessible through [history](BENCHMARK_HISTORY.md) and [archive](ARCHIVE.md).

The next performance experiment should reduce the work identified by individual events while preserving every synchronization and receipt guarantee, then pass independently declared calibration, tail, memory, cold-reopen and service gates. The tracer itself needs an independent overhead comparison before supported adoption. English only; this computer only; no deployment or messages to others.
