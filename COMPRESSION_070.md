# Zstandard checkpoint byte model: development 070

Timed 2026-10-07T11:20:12.784256+00:00 to 2026-10-07T11:20:56.058754+00:00; audited 2026-10-07T11:21:18.551968+00:00. **Model only, configuration rejected.** Supported KestrelSQL 0.3.16, its engine source/dependencies/binaries, the morning report and all earlier results remain unchanged.

**Zstandard level 1 cuts large stored frame bytes by about 70%, but increases matched charged publication time by 15.0% at 50,126 receipts and 20.6% at 99,126.** Both large time goals fail, with four latency guard failures and five A/A control failures. It does not advance to engine design or integration. All native/Python/Arrow byte checks and six memory guards pass. Smaller files do not establish a faster SQL engine.

This follows [069's rejected zlib trial](COMPRESSION_069.md), motivated by [068's per-call catalog synchronization diagnostics](TRACE_068.md). All inputs, cost accounting and acceptance thresholds are identical, but 070 uses a new frozen executable and independently measured raw controls. The older zlib total ratios 1.7061/1.8874 come from a different cohort; comparing them with 070's 1.1501/1.2058 is historical context, not a paired codec speedup. Shared host/storage behavior varies between rounds.

## Workload, costs and limits

Three actual retained generation-129 CAT4 checkpoint files from 068/069 contain **126/50,126/99,126 receipts**, occupying **21,904/8,222,890/16,271,376 bytes**. Input CRC, JSON/checkpoint type, receipt count and SHA-256 pass. No database workload was repeated to create these inputs.

Four rotated rounds x three sizes x raw A/raw B/Zstandard C = **36 serial cases**. Each performs twelve publications and twelve subsequent fresh-open checks. All **432 full frames / 2,705,553,696 stored bytes** remain preserved, with **3,530,328,480 decoded bytes** exactly equal to canonical inputs. One executable and the same raw mode/input path serve both A/B labels. Every round and stall counts.

Compression is **zstd-safe exactly 7.2.4, locked zstd-sys 2.0.16+zstd.1.5.7, native Zstandard 1.5.7, level 1**, built offline with default wrapper features disabled and std enabled. The executable checks the linked native version. One-shot context creation, compressor CPU, buffers, CRCs, frame copies and releases are charged on every publication; no dictionary, multi-worker codec or reused context is combined with this trial. Both modes use the same 32-byte model envelope and create_new/write/flush, one sync_all, close and rename. The outer timer includes all that work. Canonical input read and exact result comparison are excluded. The inherited policy's phrase "both CRCs" refers to stored/decoded payload CRCs; source code also computes and charges the header CRC in both modes.

The native wrapper checks standard magic, exactly one complete frame and a known frame content size equal to its outer declared length before allocating the bounded output. Encoded/decoded payloads are capped at 64 MiB; one-shot decompression receives a destination of exactly the validated raw length. Header, stored and decoded CRCs are checked. [Pinned frame-size API](https://docs.rs/zstd-safe/7.2.4/zstd_safe/fn.find_frame_compressed_size.html), [content-size API](https://docs.rs/zstd-safe/7.2.4/zstd_safe/fn.get_frame_content_size.html) and [native 1.5.7 API](https://github.com/facebook/zstd/blob/v1.5.7/lib/zstd.h) informed the wrapper; the preserved code and tests establish its checks.

A separate Python parser validates exact frame termination, known content size, dictionary-free framing and block bounds from the [pinned format specification](https://github.com/facebook/zstd/blob/v1.5.7/doc/zstd_compression_format.md). Apache Arrow **25.0.1** decodes each compressed payload through [its Python Codec API](https://arrow.apache.org/docs/python/generated/pyarrow.Codec.html), followed by exact original-byte and CRC comparison. This is a separate language/binding and independent framing oracle; Arrow can share the upstream codec implementation, so it is not claimed to be a separately implemented codec. Its original module/DLL hashes are recorded; its installed binary distribution is not part of the evidence ZIP.

`KCMP0701` is a standalone model format, not accepted by Kestrel's archive reader. It excludes SQL, serde serialization, growing receipts, source positions, old-format migration, Archive retries/recovery, concurrent readers, compaction, service traffic and physical power-loss qualification. Model files use `.model`, so filesystem behavior need not transfer to `.ks2`. Fresh-open read/decode runs in the same process after publication with potentially warm OS cache; it is not cold Archive reopen. Full-process peak memory includes setup and validation, not isolated codec allocations. The decoder takes an already loaded frame; its output bound is not a full hostile-file ingestion qualification.

No compilation, tests, audit, packaging or Git overlaps timed workloads. Only one task-owned child runs at a time, and structured post-timing checks show none left active.

## Before/after measurements

Display columns are medians of per-case values; decision ratios are medians of **four matched per-round ratios**, not ratios of the display medians. A ratio above 1 takes more time/bytes/memory. Type7 p99 uses only twelve samples per case and cannot qualify service tails.

| Actual checkpoint receipts | Metric | Raw A display median | Zstandard display median | Zstandard/A matched | Identical B/A matched |
|---:|---|---:|---:|---:|---:|
| 126 | Stored frame bytes | 21936.0000 | 6871.0000 | 0.313229 | 1.000000 |
| 126 | 12 charged publications, ms | 18.9285 | 17.7073 | 0.865312 | 0.885736 |
| 126 | Publication p50, ms | 1.5346 | 1.4701 | 0.941452 | 0.888524 |
| 126 | Publication p99, ms | 1.8749 | 2.0033 | 1.040463 | 0.921389 |
| 126 | Publication max, ms | 1.8863 | 2.0506 | 1.047225 | 0.921478 |
| 126 | Charged encode/compress, ms | 0.2752 | 1.4902 | 5.432816 | 0.967692 |
| 126 | Fresh-open read/decode p99, ms | 1.8190 | 0.1438 | 0.080300 | 0.827698 |
| 126 | Full-process peak working set, bytes | 4210688.0000 | 4327424.0000 | 1.027725 | 0.996608 |
| 126 | Full-process peak commit, bytes | 911360.0000 | 1036288.0000 | 1.124184 | 1.024724 |
| 50,126 | Stored frame bytes | 8222922.0000 | 2459396.0000 | 0.299090 | 1.000000 |
| 50,126 | 12 charged publications, ms | 362.6834 | 427.4421 | 1.150126 | 1.017800 |
| 50,126 | Publication p50, ms | 27.3897 | 33.8761 | 1.218026 | 1.003392 |
| 50,126 | Publication p99, ms | 42.9091 | 48.6542 | 1.048523 | 1.103985 |
| 50,126 | Publication max, ms | 43.1461 | 49.7259 | 1.062081 | 1.114489 |
| 50,126 | Charged encode/compress, ms | 64.1857 | 316.4280 | 5.057263 | 1.014866 |
| 50,126 | Fresh-open read/decode p99, ms | 7.0462 | 12.3265 | 1.731751 | 0.971883 |
| 50,126 | Full-process peak working set, bytes | 28377088.0000 | 22919168.0000 | 0.807723 | 1.000000 |
| 50,126 | Full-process peak commit, bytes | 25511936.0000 | 20766720.0000 | 0.814116 | 1.000321 |
| 99,126 | Stored frame bytes | 16271408.0000 | 4866903.0000 | 0.299108 | 1.000000 |
| 99,126 | 12 charged publications, ms | 675.9507 | 815.0667 | 1.205832 | 0.982105 |
| 99,126 | Publication p50, ms | 54.1854 | 64.4152 | 1.188815 | 1.000878 |
| 99,126 | Publication p99, ms | 71.4753 | 84.7108 | 1.206129 | 0.929619 |
| 99,126 | Publication max, ms | 71.6638 | 86.4069 | 1.229650 | 0.932390 |
| 99,126 | Charged encode/compress, ms | 128.7611 | 624.3214 | 4.835380 | 0.996802 |
| 99,126 | Fresh-open read/decode p99, ms | 12.3547 | 26.2027 | 2.113113 | 1.060641 |
| 99,126 | Full-process peak working set, bytes | 52523008.0000 | 41316352.0000 | 0.786633 | 1.000039 |
| 99,126 | Full-process peak commit, bytes | 49719296.0000 | 39374848.0000 | 0.791910 | 0.999918 |

At 50K, publication total/p50 A/A controls pass, while p99/max controls fail at 1.103985/1.114489. At 99K, all eight A/A checks pass and candidate total/p50/p99/max still regress. Small total/p50/fresh-open decode A/A controls fail. The small candidate's apparent gains are not qualified by those controls. Every compressed case passes the absolute fresh-open p99 ≤200 ms guard, but large fresh-open ratios are 1.7318/2.1131 versus raw.

The first 50K round favors compression at total ratio 0.324414, while later rounds are 1.099552/1.331299/1.200701. The first 99K candidate stalls at ratio 2.827412; later rounds remain slower at 1.214141/1.197523/1.188890. Both favorable and unfavorable stalls remain visible:

| Actual receipts | Round | C/A total | C/A p50 | C/A p99 | C/A max | Identical B/A total |
|---:|---:|---:|---:|---:|---:|---:|
| 126 | 0 | 0.739107 | 1.051201 | 1.007532 | 1.007978 | 0.651125 |
| 126 | 1 | 0.893407 | 0.887935 | 1.140339 | 1.171562 | 0.860704 |
| 126 | 2 | 1.011225 | 0.994970 | 1.073395 | 1.086471 | 0.920974 |
| 126 | 3 | 0.837216 | 0.804386 | 0.860545 | 0.857719 | 0.910767 |
| 50,126 | 0 | 0.324414 | 0.327089 | 0.321221 | 0.323150 | 1.024404 |
| 50,126 | 1 | 1.099552 | 1.175525 | 0.989190 | 1.007720 | 0.976099 |
| 50,126 | 2 | 1.331299 | 1.348683 | 1.372284 | 1.388332 | 1.057042 |
| 50,126 | 3 | 1.200701 | 1.260526 | 1.107857 | 1.116441 | 1.011196 |
| 99,126 | 0 | 2.827412 | 1.123417 | 7.807120 | 7.706077 | 0.955509 |
| 99,126 | 1 | 1.214141 | 1.184964 | 1.207200 | 1.229157 | 0.992491 |
| 99,126 | 2 | 1.197523 | 1.280863 | 1.064791 | 1.066715 | 0.982243 |
| 99,126 | 3 | 1.188890 | 1.192667 | 1.205057 | 1.230144 | 0.981967 |

## All 47 predeclared checks

Failures: **2/4 goals, 4/19 guards, 5/24 A/A checks**. Large byte goals ≤0.65 and charged-total goals ≤0.90; small total guard ≤1.10, p50 ≤1.05, p99/max ≤1.10, peak working set/commit ≤1.35. Every compressed case's fresh-open p99 must be ≤200 ms. A/A intervals are 0.90–1.10 for eight metrics at each size. None were relaxed.

| Result | Starting history | Kind | Metric | Matched ratio or absolute ms | Required |
|---|---:|---|---|---:|---|
| ✅ | 0 | guard | total_ms | 0.865311538 | ≤ 1.1 |
| ✅ | 0 | guard | p50_ms | 0.941452206 | ≤ 1.05 |
| ✅ | 0 | guard | p99_ms | 1.040463379 | ≤ 1.1 |
| ✅ | 0 | guard | max_ms | 1.047224619 | ≤ 1.1 |
| ✅ | 0 | guard | peak_working_set_bytes | 1.027724787 | ≤ 1.35 |
| ✅ | 0 | guard | peak_commit_bytes | 1.124183778 | ≤ 1.35 |
| ✅ | 0 | guard | fresh_read_decode_p99_absolute_ms | 0.161822000 | ≤ 200 |
| ❌ | 0 | identity | total_ms | 0.885735789 | [0.9, 1.1] |
| ❌ | 0 | identity | p50_ms | 0.888524260 | [0.9, 1.1] |
| ✅ | 0 | identity | p99_ms | 0.921389065 | [0.9, 1.1] |
| ✅ | 0 | identity | max_ms | 0.921478297 | [0.9, 1.1] |
| ✅ | 0 | identity | encode_total_ms | 0.967692424 | [0.9, 1.1] |
| ❌ | 0 | identity | fresh_read_decode_p99_ms | 0.827697984 | [0.9, 1.1] |
| ✅ | 0 | identity | peak_working_set_bytes | 0.996607619 | [0.9, 1.1] |
| ✅ | 0 | identity | peak_commit_bytes | 1.024724276 | [0.9, 1.1] |
| ✅ | 50,000 | goal | stored_bytes_per_frame | 0.299090275 | ≤ 0.65 |
| ❌ | 50,000 | goal | total_ms | 1.150126338 | ≤ 0.9 |
| ❌ | 50,000 | guard | p50_ms | 1.218025737 | ≤ 1.05 |
| ✅ | 50,000 | guard | p99_ms | 1.048523266 | ≤ 1.1 |
| ✅ | 50,000 | guard | max_ms | 1.062080687 | ≤ 1.1 |
| ✅ | 50,000 | guard | peak_working_set_bytes | 0.807722551 | ≤ 1.35 |
| ✅ | 50,000 | guard | peak_commit_bytes | 0.814115947 | ≤ 1.35 |
| ✅ | 50,000 | guard | fresh_read_decode_p99_absolute_ms | 13.870099000 | ≤ 200 |
| ✅ | 50,000 | identity | total_ms | 1.017799694 | [0.9, 1.1] |
| ✅ | 50,000 | identity | p50_ms | 1.003392450 | [0.9, 1.1] |
| ❌ | 50,000 | identity | p99_ms | 1.103984996 | [0.9, 1.1] |
| ❌ | 50,000 | identity | max_ms | 1.114489437 | [0.9, 1.1] |
| ✅ | 50,000 | identity | encode_total_ms | 1.014866096 | [0.9, 1.1] |
| ✅ | 50,000 | identity | fresh_read_decode_p99_ms | 0.971882665 | [0.9, 1.1] |
| ✅ | 50,000 | identity | peak_working_set_bytes | 1.000000000 | [0.9, 1.1] |
| ✅ | 50,000 | identity | peak_commit_bytes | 1.000321182 | [0.9, 1.1] |
| ✅ | 99,000 | goal | stored_bytes_per_frame | 0.299107674 | ≤ 0.65 |
| ❌ | 99,000 | goal | total_ms | 1.205832227 | ≤ 0.9 |
| ❌ | 99,000 | guard | p50_ms | 1.188815418 | ≤ 1.05 |
| ❌ | 99,000 | guard | p99_ms | 1.206128750 | ≤ 1.1 |
| ❌ | 99,000 | guard | max_ms | 1.229650218 | ≤ 1.1 |
| ✅ | 99,000 | guard | peak_working_set_bytes | 0.786633393 | ≤ 1.35 |
| ✅ | 99,000 | guard | peak_commit_bytes | 0.791910370 | ≤ 1.35 |
| ✅ | 99,000 | guard | fresh_read_decode_p99_absolute_ms | 29.625704000 | ≤ 200 |
| ✅ | 99,000 | identity | total_ms | 0.982104802 | [0.9, 1.1] |
| ✅ | 99,000 | identity | p50_ms | 1.000878229 | [0.9, 1.1] |
| ✅ | 99,000 | identity | p99_ms | 0.929619200 | [0.9, 1.1] |
| ✅ | 99,000 | identity | max_ms | 0.932389853 | [0.9, 1.1] |
| ✅ | 99,000 | identity | encode_total_ms | 0.996801640 | [0.9, 1.1] |
| ✅ | 99,000 | identity | fresh_read_decode_p99_ms | 1.060640587 | [0.9, 1.1] |
| ✅ | 99,000 | identity | peak_working_set_bytes | 1.000038992 | [0.9, 1.1] |
| ✅ | 99,000 | identity | peak_commit_bytes | 0.999917621 | [0.9, 1.1] |

## Correctness, failures and benchmark status

- ✅ Twelve native tests pass in debug and release, plus formatting and strict Clippy. Coverage includes raw/compressed roundtrip, all truncations/trailing file data, header/payload corruption, unsupported codec, decoded-size/budget/CRC errors, trailing compressed bytes, concatenated valid frames, skippable frames, unknown content size and damage with recomputed outer CRCs.
- ✅ Three Python framing test groups pass before timing: handmade raw/RLE frames and truncation/concatenation, malformed headers/blocks, and Arrow-produced frames across size transitions.
- ✅ All 432 frames pass native exact decoding, Python frame boundaries, Arrow decoding and every outer CRC. Fixed-input bytes are identical across sequences and rounds for each mode. All input/frame/raw/policy/source/executable/oracle hashes pass; memory counters are available for all 36 cases.
- ❌ Both charged-publication time goals, four latency guards and five A/A checks fail. This configuration is rejected.
- The initial debug build's API comparison failed because ContentSizeError lacks PartialEq. Initial source, logs and build order are preserved; the fixed checks passed before any timer. No case was restarted or replaced.

**No new DuckDB, PostgreSQL or other SQL benchmark ran in 070.** Previous wins/losses remain in [analytical 046](PERFORMANCE_046.md), [development 061](CORE_READ_PATH_061.md), [six-engine service 047](SERVICE_047.md) and [complete history](BENCHMARK_HISTORY.md). Existing SQL/source retry/crash qualification in 068 is separate; this byte model does not extend it. No supported promotion, universal superiority, Facebook-scale qualification, PostgreSQL replacement or production-readiness claim follows. [Adoption assessment](ADOPTION_STATUS.md).

[Declared policy](benchmarks/compression-070/policy.json), [frozen case order](benchmarks/compression-070/cohort-policy.json), [raw case index](benchmarks/compression-070/model-results.json), [every round and gate](benchmarks/compression-070/model-audit.json), [full frame inventory](benchmarks/compression-070/fixture-inventory.json), [input provenance](benchmarks/compression-070/input-provenance.json), [build/test proof](benchmarks/compression-070/build-proof.json), [oracle provenance](benchmarks/compression-070/oracle-provenance.json), [parser-test proof](benchmarks/compression-070/frame-oracle-test-proof.json), [runtime provenance](benchmarks/compression-070/runtime-provenance.json), [locked crates](benchmarks/compression-070/dependency-provenance.json), [pre-timing notes](benchmarks/compression-070/PRE_TIMING_NOTES.md), [reproduction](benchmarks/compression-070/REPRODUCE.md) and [next work](benchmarks/compression-070/NEXT_WORK.md). Raw stdout/status/error files, compiler logs, initial failed source, final source and frozen executable are alongside them. Every frame and all three inputs are retained in the immutable ZIP.

Further codec configurations require a fresh independently declared trial with all costs, bounds, synchronization and gates retained. Only passing all model checks motivates a separately designed engine candidate; that candidate still needs format compatibility and full SQL/durable retry/crash/concurrency/service qualification. English only; this computer only; no deployment or messages to others.

Private immutable [full compression-model evidence and frames](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-070-compression-model-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-070-compression-model-evidence.zip.sha256). The supplemental ZIP contains this report before the upload-link paragraph; all 104 previous assets and 20 engine tags/releases remain unchanged.
