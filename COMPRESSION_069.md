# Checkpoint compression byte model: development 069

Measured 2026-10-07T10:57:35.110343+00:00. **Model only, configuration rejected.** This is not a new SQL engine or production catalog format. Supported KestrelSQL 0.3.16, its source/dependencies/binaries, all previous benchmarks and the frozen morning report remain unchanged.

**Large checkpoint frames are 62.8% smaller, but the median matched charged-publication ratios are 1.7061 at 50,126 receipts and 1.8874 at 99,126.** Encoding/compression costs 8.62×/8.69× the raw frame encoder. Both total-time goals and all six large-history p50/p99/max guards fail. This codec configuration does not advance to engine design or integration. Memory guards and exact decoding pass; smaller files alone do not establish a faster database.

The hypothesis follows [068 per-call diagnostics](TRACE_068.md): eight large-checkpoint stalls spent 91.88–98.01% of their call in catalog synchronization. Reducing bytes was worth testing, but that observation does not prove a physical cause or predict whether extra codec CPU pays off. Increasing checkpoint spacing would also exceed the released reader's 32-catalog receipt-chain budget; this model leaves it unchanged.

## Scope and accounting

Three exact retained CAT4 checkpoint files from 068, generation 129, contain **126/50,126/99,126 receipts**, occupying **21,904 / 8,222,890 / 16,271,376 bytes**. Input envelope CRC, JSON/checkpoint type, retained per-event metadata and SHA-256 all pass. The zero-seed checkpoint is a compaction, with 126 receipts after batch 125. An initial preparation assertion incorrectly expected 127, stopped before policy/timers, and was corrected using preserved metadata; its original code and copied input remain preserved. No database workload was rerun.

Four rotated rounds × three sizes × raw A/raw B/zlib C = **36 serial cases**. Each publishes 12 fixed-input frames; all **432 frames / 2,791,295,568 stored bytes** remain intact. One frozen executable and one raw mode/input path serve both A/B labels. Each case then performs 12 fresh-open read/decode checks. All **3,530,328,480 decoded bytes** independently match the canonical original checkpoint files using Python zlib; every native check also passes.

The raw and compressed modes use the same 32-byte model envelope and publication lifecycle: frame/checksum/allocate/copy, create_new/write/flush, one sync_all, close, rename and buffer release. Compression is **miniz_oxide exactly 0.8.9, zlib level 1**, available in the local offline cache. Every codec and frame-assembly cost is charged inside the outer publication. Canonical input read and final byte comparisons are outside the publication timer. All samples, including stalls, are included.

The model's `KCMP0691` frame is **not** a Kestrel archive format. It excludes SQL, serde serialization, growing receipt ledgers, source positions, migration, actual Archive recovery, pinned/concurrent readers, compaction, service load and physical power-loss qualification. Files end in `.model`, rather than actual archive `.ks2`; filesystem behavior need not transfer. Fresh-open read/decode timing runs in the same process after writes with a potentially warm OS cache. It is not cold Archive reopen. Full-process peak memory includes input read and validation, not isolated codec allocations. No compilation, test/audit, packaging or Git work overlaps timers; task-owned children are stopped afterward.

The standalone decoder validates header, stored and decoded CRCs, caps encoded and decoded payload at 64 MiB before output allocation, and requires the exact compressed stream to end with every input byte consumed. [Pinned library source](https://docs.rs/crate/miniz_oxide/0.8.9/source/Cargo.toml) documents the dependency; model code and tests establish this wrapper's bounds and strict checks.

## Before/after model measurements

Display columns are medians of per-case values. Decision ratios are medians of **four matched per-round ratios**, not ratios of display medians. p99 uses Type7 interpolation over only 12 samples per case; these descriptive model tails cannot qualify a service.

| Actual receipts in fixed checkpoint | Metric | Raw A display median | Compressed display median | Compressed/A matched | Identical B/A matched |
|---:|---|---:|---:|---:|---:|
| 126 | Stored frame bytes | 21936.0000 | 8378.0000 | 0.381929 | 1.000000 |
| 126 | 12 charged publications, ms | 21.2379 | 20.7527 | 0.908668 | 0.974889 |
| 126 | Publication p50, ms | 1.6214 | 1.6620 | 0.993883 | 0.869586 |
| 126 | Publication p99, ms | 3.0566 | 2.1397 | 0.613363 | 0.971400 |
| 126 | Publication max, ms | 3.1752 | 2.1463 | 0.593667 | 0.960811 |
| 126 | Charged encode/compress, ms | 0.3453 | 3.1730 | 9.713232 | 0.903177 |
| 126 | Fresh-open read/decode p99, ms | 1.9037 | 1.9391 | 1.028307 | 0.863987 |
| 50,126 | Stored frame bytes | 8222922.0000 | 3060721.0000 | 0.372218 | 1.000000 |
| 50,126 | 12 charged publications, ms | 444.1493 | 757.5824 | 1.706141 | 0.966008 |
| 50,126 | Publication p50, ms | 31.3283 | 60.6512 | 1.935416 | 0.986537 |
| 50,126 | Publication p99, ms | 71.0508 | 83.4175 | 1.174232 | 0.968500 |
| 50,126 | Publication max, ms | 73.6454 | 85.4423 | 1.160379 | 0.971904 |
| 50,126 | Charged encode/compress, ms | 69.7946 | 588.5974 | 8.624908 | 1.064500 |
| 50,126 | Fresh-open read/decode p99, ms | 7.2048 | 34.9915 | 4.960883 | 1.194754 |
| 99,126 | Stored frame bytes | 16271408.0000 | 6050360.0000 | 0.371840 | 1.000000 |
| 99,126 | 12 charged publications, ms | 790.9782 | 1492.6699 | 1.887376 | 1.011980 |
| 99,126 | Publication p50, ms | 65.0386 | 118.8920 | 1.827940 | 1.001454 |
| 99,126 | Publication p99, ms | 80.6857 | 156.1496 | 1.820615 | 1.052729 |
| 99,126 | Publication max, ms | 81.1561 | 157.0482 | 1.815201 | 1.055289 |
| 99,126 | Charged encode/compress, ms | 132.9741 | 1157.9905 | 8.685879 | 1.030754 |
| 99,126 | Fresh-open read/decode p99, ms | 13.4238 | 63.3601 | 4.604195 | 0.954508 |

The first large-history round favors compression (total ratios 0.3491 at 50K and 0.4227 at 99K), while the three later rounds have total ratios **1.6923–1.8355** and **1.8791–1.9294**. All rounds remain visible. Large-history A/A publication total/p50/p99/max checks pass; the candidate's large latency regression is not hidden by selecting the stalled raw first round. Across all sizes, three of 24 calibration checks still fail: small p50, small fresh-open decode p99 and 50K fresh-open decode p99. No claim of calibrated universal behavior follows.

## Every predeclared check

Failures: **2/4 goals, 6/19 guards, 3/24 A/A checks**. Large byte goals require a ratio ≤0.65 and total-time goals ≤0.90. Small total guard ≤1.10; p50 ≤1.05; p99/max ≤1.10; peak working set/commit ≤1.35. Every compressed case's fresh-open read/decode p99 must stay ≤200 ms. A/A intervals are 0.90–1.10 for eight metrics at each size. These were declared before the first case and were not relaxed.

| Result | Starting history | Kind | Metric | Matched ratio or absolute decode ms | Required |
|---|---:|---|---|---:|---|
| ✅ | 0 | guard | total_ms | 0.908667999 | ≤ 1.1 |
| ✅ | 0 | guard | p50_ms | 0.993882967 | ≤ 1.05 |
| ✅ | 0 | guard | p99_ms | 0.613362680 | ≤ 1.1 |
| ✅ | 0 | guard | max_ms | 0.593666658 | ≤ 1.1 |
| ✅ | 0 | guard | peak_working_set_bytes | 1.027378228 | ≤ 1.35 |
| ✅ | 0 | guard | peak_commit_bytes | 1.269495057 | ≤ 1.35 |
| ✅ | 0 | guard | fresh_read_decode_p99_absolute_ms | 2.422253000 | ≤ 200 |
| ✅ | 0 | identity | total_ms | 0.974888902 | [0.9, 1.1] |
| ❌ | 0 | identity | p50_ms | 0.869585974 | [0.9, 1.1] |
| ✅ | 0 | identity | p99_ms | 0.971399882 | [0.9, 1.1] |
| ✅ | 0 | identity | max_ms | 0.960810565 | [0.9, 1.1] |
| ✅ | 0 | identity | encode_total_ms | 0.903177085 | [0.9, 1.1] |
| ❌ | 0 | identity | fresh_read_decode_p99_ms | 0.863986949 | [0.9, 1.1] |
| ✅ | 0 | identity | peak_working_set_bytes | 1.000000000 | [0.9, 1.1] |
| ✅ | 0 | identity | peak_commit_bytes | 0.972602740 | [0.9, 1.1] |
| ✅ | 50,000 | goal | stored_bytes_per_frame | 0.372218173 | ≤ 0.65 |
| ❌ | 50,000 | goal | total_ms | 1.706141270 | ≤ 0.9 |
| ❌ | 50,000 | guard | p50_ms | 1.935416289 | ≤ 1.05 |
| ❌ | 50,000 | guard | p99_ms | 1.174232076 | ≤ 1.1 |
| ❌ | 50,000 | guard | max_ms | 1.160379013 | ≤ 1.1 |
| ✅ | 50,000 | guard | peak_working_set_bytes | 0.822008817 | ≤ 1.35 |
| ✅ | 50,000 | guard | peak_commit_bytes | 0.805214613 | ≤ 1.35 |
| ✅ | 50,000 | guard | fresh_read_decode_p99_absolute_ms | 38.738983000 | ≤ 200 |
| ✅ | 50,000 | identity | total_ms | 0.966007593 | [0.9, 1.1] |
| ✅ | 50,000 | identity | p50_ms | 0.986536742 | [0.9, 1.1] |
| ✅ | 50,000 | identity | p99_ms | 0.968499508 | [0.9, 1.1] |
| ✅ | 50,000 | identity | max_ms | 0.971903671 | [0.9, 1.1] |
| ✅ | 50,000 | identity | encode_total_ms | 1.064500359 | [0.9, 1.1] |
| ❌ | 50,000 | identity | fresh_read_decode_p99_ms | 1.194753633 | [0.9, 1.1] |
| ✅ | 50,000 | identity | peak_working_set_bytes | 1.000000021 | [0.9, 1.1] |
| ✅ | 50,000 | identity | peak_commit_bytes | 1.000321259 | [0.9, 1.1] |
| ✅ | 99,000 | goal | stored_bytes_per_frame | 0.371839978 | ≤ 0.65 |
| ❌ | 99,000 | goal | total_ms | 1.887375824 | ≤ 0.9 |
| ❌ | 99,000 | guard | p50_ms | 1.827939904 | ≤ 1.05 |
| ❌ | 99,000 | guard | p99_ms | 1.820614789 | ≤ 1.1 |
| ❌ | 99,000 | guard | max_ms | 1.815200952 | ≤ 1.1 |
| ✅ | 99,000 | guard | peak_working_set_bytes | 0.807636803 | ≤ 1.35 |
| ✅ | 99,000 | guard | peak_commit_bytes | 0.797866220 | ≤ 1.35 |
| ✅ | 99,000 | guard | fresh_read_decode_p99_absolute_ms | 64.694275000 | ≤ 200 |
| ✅ | 99,000 | identity | total_ms | 1.011979581 | [0.9, 1.1] |
| ✅ | 99,000 | identity | p50_ms | 1.001454181 | [0.9, 1.1] |
| ✅ | 99,000 | identity | p99_ms | 1.052728587 | [0.9, 1.1] |
| ✅ | 99,000 | identity | max_ms | 1.055289352 | [0.9, 1.1] |
| ✅ | 99,000 | identity | encode_total_ms | 1.030754198 | [0.9, 1.1] |
| ✅ | 99,000 | identity | fresh_read_decode_p99_ms | 0.954507534 | [0.9, 1.1] |
| ✅ | 99,000 | identity | peak_working_set_bytes | 0.999961001 | [0.9, 1.1] |
| ✅ | 99,000 | identity | peak_commit_bytes | 0.999917628 | [0.9, 1.1] |

## Verification and preserved evidence

- ✅ Eight meaningful decoder/framing tests pass in debug and release, plus format and strict Clippy. Tests cover exact raw/compressed roundtrip, all truncation points and trailing file data, corrupted header/payload, unsupported codec, bounded expansion, incorrect decoded length/CRC and compressed trailing bytes with valid outer checksums.
- ✅ All 432 frames pass native exact decoding and independent Python zlib decoding, all three CRCs, size/type/budget/stream-end checks. Fixed-input frame bytes are identical across all sequences and rounds for each mode. Every frame and input is retained in the private ZIP.
- ✅ Raw hashes, frozen policies/executable/auditor, case order, all 432 publication samples, stage sums and 432 fresh-open checks are independently verified. Full-process memory counters are available for every case.
- ❌ Both large charged-total goals and six large latency guards fail; three A/A checks fail. No engine integration, service qualification or supported promotion.

**No new DuckDB, PostgreSQL or other SQL performance comparison occurred.** Prior wins and losses remain accessible in [analytical 046](PERFORMANCE_046.md), [development 061](CORE_READ_PATH_061.md), [six-engine service 047](SERVICE_047.md) and [complete history](BENCHMARK_HISTORY.md). Existing SQL/source retry/crash checks in 068 remain separate; this model does not repeat or extend them. [Adoption assessment](ADOPTION_STATUS.md).

[Declared policy](benchmarks/compression-069/policy.json), [frozen case order](benchmarks/compression-069/cohort-policy.json), [raw case index](benchmarks/compression-069/model-results.json), [independent audit including every round](benchmarks/compression-069/model-audit.json), [full frame inventory](benchmarks/compression-069/fixture-inventory.json), [input provenance](benchmarks/compression-069/input-provenance.json), [build/test proof](benchmarks/compression-069/build-proof.json), [runtime provenance](benchmarks/compression-069/runtime-provenance.json), [locked crate archives](benchmarks/compression-069/dependency-provenance.json), [reproduction](benchmarks/compression-069/REPRODUCE.md) and [next work](benchmarks/compression-069/NEXT_WORK.md). Individual raw stdout/status/error files and compiler logs are alongside them; full frames and three canonical inputs are in the immutable ZIP.

A new codec hypothesis must charge its CPU and memory costs against the same raw controls, preserve all synchronization guarantees and pass independently declared gates before any real engine design. No inference of Facebook-scale, PostgreSQL replacement or production readiness is supported here. English only; this computer only; no deployment/messages to others.

Private immutable [full compression-model evidence and frames](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-069-compression-model-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-069-compression-model-evidence.zip.sha256). The supplemental ZIP contains this report before the upload-link paragraph; all 102 previous assets and 20 engine tags/releases remain unchanged.
