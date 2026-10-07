# Balanced fast-Zstandard checkpoint byte model: development 071

Timed 2026-10-07T11:36:42.088243+00:00 to 2026-10-07T11:40:31.130442+00:00; audited 2026-10-07T11:41:32.273319+00:00. **Model only, configuration rejected.** Supported KestrelSQL 0.3.16, its engine source/dependencies/binaries, the frozen morning report and all prior raw results/reports/private ZIPs remain unchanged.

**Verified improvement: the benchmark scheduler now checks balanced order independently before and after timing.** The [069/070 correction](MODEL_ORDER_AUDIT_071.md) documents a flaw I introduced: size rotation cancelled variant rotation, leaving one fixed A/B/C order per size in their four rounds. Their original statistics remain visible as descriptive results; that ordering can confound codec, cache, position and host/storage effects. No original evidence was rewritten and neither model was promoted.

**Fast Zstandard level −5 saves about 46% of large stored frame bytes, but fails both charged-publication speed goals and five guards.** Four A/A checks also fail. Matched C/A totals are **0.940531 at 50,126 receipts** (fails the required ≤0.90) and **1.178224 at 99,126**. The small total/p50 and large 99K p50/p99/max guards fail. All six memory guards and absolute fresh-open guards pass. This configuration does not advance to engine design or integration. No SQL speedup follows.

## Workload and corrected method

The three unchanged retained generation-129 CAT4 checkpoints from diagnostic 068 contain **126/50,126/99,126 receipts** in **21,904/8,222,890/16,271,376 bytes**. Input envelope CRC, JSON/checkpoint type, receipt count and SHA pass through the retained 069/070 chain. No database workload recreates them. The frozen input provenance's `original_archive` field points to an intermediate 069 input, rather than directly to 068; the additive [origin note](benchmarks/compression-071/input-origin-note.json) records the verified original 068 path without rewriting frozen provenance.

Six complete permutations x three sizes x raw A/raw B/compressed C = **54 serial cases**, each with twelve publications and twelve fresh-open checks. For each fixed size, every variant occupies every position twice, all six variant orders appear once, and A-before-B/B-before-A occur three times each. Each size occupies each size position twice. A planner validates those counts before the first timer; the auditor verifies them independently of elapsed times afterward. Three regression-test groups reject the earlier cancelling rotation, duplicate variants and malformed size groups. One frozen executable, mode and input path serve both raw A/B labels.

All **648 full frames / 4,478,367,888 stored bytes** remain intact. Native decoding, a separate Python frame-boundary parser and Arrow's separate byte-decoding binding verify **5,295,492,720 exact original decoded bytes**. Fixed-input frame bytes are identical across all sequences/rounds for each mode. Every case and stall is included.

Native **Zstandard 1.5.7 / zstd-safe 7.2.4 / locked zstd-sys 2.0.16+zstd.1.5.7**, level **−5**, is built offline with wrapper default features disabled and std only. The library documents negative levels as a speed/compression tradeoff in its [pinned API](https://github.com/facebook/zstd/blob/v1.5.7/lib/zstd.h). Level −5 was selected independently before timing; no local level sweep or selected-case retuning occurred. The executable checks the linked native version. Twelve meaningful native tests pass in debug/release, formatting and strict Clippy pass.

The one-shot context, compressor CPU, allocations, stored/decoded payload CRCs plus header CRC, frame copies, create_new/write/flush, one sync_all, close, rename and frame release are all charged inside the outer timer. No dictionary, worker threads, reused context or buffer optimization is combined with the codec. Both modes use the same 32-byte model envelope. Canonical input read and final exact-byte comparison are excluded. All 47 thresholds are unchanged from 069/070; the new cohort uses six balanced rounds rather than their four fixed-order rounds. Earlier measurements are historical context, not a paired codec comparison.

Native decoding caps encoded/decoded payload at 64 MiB, validates standard magic, known content size and exactly one complete frame before output allocation, and passes a destination of exactly the validated raw size to one-shot decoding. Header/stored/decoded CRCs must match. Tests reject truncation, trailing/concatenated/skippable frames, unknown content size, corruption, unsupported codecs and invalid expanded lengths/budgets/CRCs. A separate Python parser checks frame limits and exact end against the [pinned format](https://github.com/facebook/zstd/blob/v1.5.7/doc/zstd_compression_format.md); three parser-test groups pass before timing. Apache Arrow **25.0.1** through its [Codec API](https://arrow.apache.org/docs/python/generated/pyarrow.Codec.html) decodes and compares exact original bytes. This separate language/binding can share the upstream codec implementation; it is not a separately implemented codec. Original Arrow binding/DLL hashes are recorded, but its installed distribution is not bundled.

`KCMP0711` is a model format rejected by Kestrel's archive reader. It excludes SQL, serde serialization, actual receipt mutations, source positions, migration, actual Archive retry/crash recovery, concurrent/pinned readers, compaction, service traffic and physical power loss. `.model` file behavior need not transfer to `.ks2`. Fresh-open reads occur in the same process after writes with possibly warm OS cache; they are not cold Archive reopen. Full-process peak memory includes setup and validation; the output bound is not a complete hostile-file ingestion qualification. No compile/test/audit/package/Git overlaps timed cases, and post-timing checks show no task-owned children left.

## Before/after measurements

Display values are medians of per-case metrics; decision ratios are medians of **six matched per-round ratios**, not ratios of display medians. Raw B is shown to expose variation. Type7 p99 uses twelve samples per case and cannot qualify service tails. A ratio above 1 takes more time/bytes/memory.

| Actual checkpoint receipts | Metric | Raw A display median | Identical raw B display median | Compressed display median | C/A matched | Identical B/A matched |
|---:|---|---:|---:|---:|---:|---:|
| 126 | Stored frame bytes | 21936.0000 | 21936.0000 | 12651.0000 | 0.576723 | 1.000000 |
| 126 | 12 charged publications, ms | 19.6476 | 20.6830 | 20.1181 | 1.136976 | 1.067486 |
| 126 | Publication p50, ms | 1.4836 | 1.5449 | 1.6331 | 1.095476 | 1.050754 |
| 126 | Publication p99, ms | 2.0067 | 2.5642 | 2.0637 | 1.081085 | 1.161377 |
| 126 | Publication max, ms | 2.0239 | 2.5869 | 2.0786 | 1.082884 | 1.169629 |
| 126 | Charged encode/compress, ms | 0.2946 | 0.3115 | 1.3716 | 4.572400 | 1.009196 |
| 126 | Fresh-open read/decode p99, ms | 2.8958 | 2.5903 | 2.1631 | 0.707630 | 1.002275 |
| 126 | Full-process peak working set, bytes | 4214784.0000 | 4210688.0000 | 4311040.0000 | 1.022838 | 0.998543 |
| 126 | Full-process peak commit, bytes | 933888.0000 | 899072.0000 | 1015808.0000 | 1.082990 | 0.962882 |
| 50,126 | Stored frame bytes | 8222922.0000 | 8222922.0000 | 4420418.0000 | 0.537573 | 1.000000 |
| 50,126 | 12 charged publications, ms | 6413.4207 | 419.7419 | 6801.1593 | 0.940531 | 0.928257 |
| 50,126 | Publication p50, ms | 509.1879 | 28.3579 | 559.7756 | 0.950858 | 1.004509 |
| 50,126 | Publication p99, ms | 648.0798 | 52.6988 | 653.5536 | 1.023366 | 0.790605 |
| 50,126 | Publication max, ms | 650.0431 | 53.7975 | 657.9986 | 1.034276 | 0.780103 |
| 50,126 | Charged encode/compress, ms | 63.7414 | 69.0149 | 273.1301 | 4.363588 | 1.045335 |
| 50,126 | Fresh-open read/decode p99, ms | 7.0894 | 6.8061 | 11.3276 | 1.639597 | 0.924876 |
| 50,126 | Full-process peak working set, bytes | 28372992.0000 | 28372992.0000 | 24809472.0000 | 0.874468 | 1.000000 |
| 50,126 | Full-process peak commit, bytes | 25520128.0000 | 25522176.0000 | 22683648.0000 | 0.889174 | 1.000161 |
| 99,126 | Stored frame bytes | 16271408.0000 | 16271408.0000 | 8733953.0000 | 0.536767 | 1.000000 |
| 99,126 | 12 charged publications, ms | 818.6127 | 783.7817 | 1053.4968 | 1.178224 | 0.997672 |
| 99,126 | Publication p50, ms | 65.5439 | 61.2799 | 83.8621 | 1.116106 | 0.938140 |
| 99,126 | Publication p99, ms | 94.5689 | 96.5953 | 127.2221 | 1.196421 | 1.084809 |
| 99,126 | Publication max, ms | 96.8561 | 98.9027 | 129.5470 | 1.171280 | 1.089146 |
| 99,126 | Charged encode/compress, ms | 140.1911 | 139.2601 | 542.2910 | 3.981031 | 0.989643 |
| 99,126 | Fresh-open read/decode p99, ms | 14.0970 | 14.3100 | 28.3228 | 1.895457 | 1.053384 |
| 99,126 | Full-process peak working set, bytes | 52518912.0000 | 52518912.0000 | 45221888.0000 | 0.861059 | 1.000000 |
| 99,126 | Full-process peak commit, bytes | 49713152.0000 | 49713152.0000 | 43180032.0000 | 0.868702 | 0.999959 |

At 99K, all eight A/A aggregate checks pass, but C's total/p50/p99/max ratios are **1.178224/1.116106/1.196421/1.171280**. At 50K, total/p50 controls pass while tail controls fail (p99 0.790605, max 0.780103). The apparent 50K total reduction falls short of the 10% goal and does not establish a general speedup. Its six individual total ratios span **0.528627–28.197634**. Small p99/max controls fail at 1.161377/1.169629. Balanced ordering removes the confirmed fixed-position flaw; it does not remove shared-host variability or qualify every timing metric.

Charged encoding remains **4.3636x/3.9810x raw** at 50K/99K. Large fresh-open read/decode ratios are **1.6396/1.8955**, though all absolute candidate p99 guards ≤200 ms pass. Byte ratios are **0.537573/0.536767**; all six memory guards pass. Keep every stalled and fast round:

| Actual receipts | Round | C/A total | C/A p50 | C/A p99 | C/A max | Identical B/A total |
|---:|---:|---:|---:|---:|---:|---:|
| 126 | 0 | 1.157675 | 1.186180 | 1.072224 | 1.072093 | 1.055177 |
| 126 | 1 | 0.987369 | 1.039777 | 0.880096 | 0.879503 | 0.983378 |
| 126 | 2 | 1.116278 | 1.113932 | 1.191078 | 1.191067 | 1.079795 |
| 126 | 3 | 0.998348 | 0.984295 | 1.055494 | 1.060553 | 1.087041 |
| 126 | 4 | 1.442752 | 1.077020 | 1.519167 | 1.568461 | 1.890801 |
| 126 | 5 | 1.355066 | 1.145279 | 1.089946 | 1.093676 | 0.929004 |
| 50,126 | 0 | 0.528627 | 0.563987 | 0.427793 | 0.418730 | 0.034371 |
| 50,126 | 1 | 0.559639 | 0.497307 | 0.344099 | 0.330026 | 0.034391 |
| 50,126 | 2 | 1.321422 | 1.337730 | 1.474571 | 1.490251 | 0.914895 |
| 50,126 | 3 | 1.462308 | 1.432363 | 1.927140 | 1.999071 | 1.221599 |
| 50,126 | 4 | 28.197634 | 32.845578 | 24.097061 | 23.706325 | 0.941619 |
| 50,126 | 5 | 0.532063 | 0.503730 | 0.572161 | 0.578300 | 1.100800 |
| 99,126 | 0 | 0.553316 | 0.558840 | 0.573728 | 0.576534 | 1.084994 |
| 99,126 | 1 | 1.082623 | 1.069789 | 1.060266 | 1.048115 | 0.882967 |
| 99,126 | 2 | 1.540110 | 1.697170 | 1.332576 | 1.294445 | 1.096638 |
| 99,126 | 3 | 1.372516 | 1.278110 | 1.759636 | 1.806042 | 0.984804 |
| 99,126 | 4 | 1.273825 | 1.162423 | 1.373910 | 1.374348 | 1.010541 |
| 99,126 | 5 | 0.576764 | 0.521439 | 0.705906 | 0.700555 | 0.881277 |

## Every predeclared gate

Failures: **2/4 goals, 5/19 guards, 4/24 A/A checks**. Large stored-byte goal ≤0.65; large charged-total goal ≤0.90. Small total ≤1.10, p50 ≤1.05, p99/max ≤1.10, peak working set/commit ≤1.35. Every C case's fresh-open p99 must be ≤200 ms. A/A intervals are 0.90–1.10 for eight metrics per size. No threshold changed after timing.

| Result | Starting history | Kind | Metric | Matched ratio or absolute ms | Required |
|---|---:|---|---|---:|---|
| ❌ | 0 | guard | total_ms | 1.136976442 | ≤ 1.1 |
| ❌ | 0 | guard | p50_ms | 1.095475913 | ≤ 1.05 |
| ✅ | 0 | guard | p99_ms | 1.081085079 | ≤ 1.1 |
| ✅ | 0 | guard | max_ms | 1.082884377 | ≤ 1.1 |
| ✅ | 0 | guard | peak_working_set_bytes | 1.022837707 | ≤ 1.35 |
| ✅ | 0 | guard | peak_commit_bytes | 1.082990084 | ≤ 1.35 |
| ✅ | 0 | guard | fresh_read_decode_p99_absolute_ms | 2.851965000 | ≤ 200 |
| ✅ | 0 | identity | total_ms | 1.067485978 | [0.9, 1.1] |
| ✅ | 0 | identity | p50_ms | 1.050754042 | [0.9, 1.1] |
| ❌ | 0 | identity | p99_ms | 1.161377118 | [0.9, 1.1] |
| ❌ | 0 | identity | max_ms | 1.169628550 | [0.9, 1.1] |
| ✅ | 0 | identity | encode_total_ms | 1.009196370 | [0.9, 1.1] |
| ✅ | 0 | identity | fresh_read_decode_p99_ms | 1.002275011 | [0.9, 1.1] |
| ✅ | 0 | identity | peak_working_set_bytes | 0.998542745 | [0.9, 1.1] |
| ✅ | 0 | identity | peak_commit_bytes | 0.962882096 | [0.9, 1.1] |
| ✅ | 50,000 | goal | stored_bytes_per_frame | 0.537572654 | ≤ 0.65 |
| ❌ | 50,000 | goal | total_ms | 0.940530671 | ≤ 0.9 |
| ✅ | 50,000 | guard | p50_ms | 0.950858395 | ≤ 1.05 |
| ✅ | 50,000 | guard | p99_ms | 1.023366101 | ≤ 1.1 |
| ✅ | 50,000 | guard | max_ms | 1.034275634 | ≤ 1.1 |
| ✅ | 50,000 | guard | peak_working_set_bytes | 0.874467900 | ≤ 1.35 |
| ✅ | 50,000 | guard | peak_commit_bytes | 0.889174236 | ≤ 1.35 |
| ✅ | 50,000 | guard | fresh_read_decode_p99_absolute_ms | 12.982823000 | ≤ 200 |
| ✅ | 50,000 | identity | total_ms | 0.928257402 | [0.9, 1.1] |
| ✅ | 50,000 | identity | p50_ms | 1.004508785 | [0.9, 1.1] |
| ❌ | 50,000 | identity | p99_ms | 0.790605061 | [0.9, 1.1] |
| ❌ | 50,000 | identity | max_ms | 0.780103471 | [0.9, 1.1] |
| ✅ | 50,000 | identity | encode_total_ms | 1.045335477 | [0.9, 1.1] |
| ✅ | 50,000 | identity | fresh_read_decode_p99_ms | 0.924876171 | [0.9, 1.1] |
| ✅ | 50,000 | identity | peak_working_set_bytes | 1.000000000 | [0.9, 1.1] |
| ✅ | 50,000 | identity | peak_commit_bytes | 1.000160501 | [0.9, 1.1] |
| ✅ | 99,000 | goal | stored_bytes_per_frame | 0.536766886 | ≤ 0.65 |
| ❌ | 99,000 | goal | total_ms | 1.178224024 | ≤ 0.9 |
| ❌ | 99,000 | guard | p50_ms | 1.116106295 | ≤ 1.05 |
| ❌ | 99,000 | guard | p99_ms | 1.196421181 | ≤ 1.1 |
| ❌ | 99,000 | guard | max_ms | 1.171279809 | ≤ 1.1 |
| ✅ | 99,000 | guard | peak_working_set_bytes | 0.861059117 | ≤ 1.35 |
| ✅ | 99,000 | guard | peak_commit_bytes | 0.868701853 | ≤ 1.35 |
| ✅ | 99,000 | guard | fresh_read_decode_p99_absolute_ms | 30.623597000 | ≤ 200 |
| ✅ | 99,000 | identity | total_ms | 0.997672336 | [0.9, 1.1] |
| ✅ | 99,000 | identity | p50_ms | 0.938139505 | [0.9, 1.1] |
| ✅ | 99,000 | identity | p99_ms | 1.084808875 | [0.9, 1.1] |
| ✅ | 99,000 | identity | max_ms | 1.089145741 | [0.9, 1.1] |
| ✅ | 99,000 | identity | encode_total_ms | 0.989642716 | [0.9, 1.1] |
| ✅ | 99,000 | identity | fresh_read_decode_p99_ms | 1.053383785 | [0.9, 1.1] |
| ✅ | 99,000 | identity | peak_working_set_bytes | 1.000000000 | [0.9, 1.1] |
| ✅ | 99,000 | identity | peak_commit_bytes | 0.999958807 | [0.9, 1.1] |

## Verification and preserved evidence

- ✅ Twelve native tests pass in debug/release; formatting and strict Clippy pass. Every malformed-stream/framing case and exact original-byte roundtrip is retained.
- ✅ Three scheduling regression groups and three Python framing groups pass before timers, with logs preserved. Both pre/post balance proofs and frozen code hashes pass.
- ✅ All 648 frame checks, three CRCs, exact native/Arrow decoding, input/raw/frame hashes, stages/counts/order and full-process memory counters pass. No case restarted or overwritten.
- ❌ Both large speed goals, five guards and four calibration checks fail. Model rejected; no engine edit, service qualification or supported promotion.
- The older 069/070 variant-order claim was incorrect. Read [its additive correction](MODEL_ORDER_AUDIT_071.md) alongside their unchanged reports/raw archives. The defect is scoped to those two model cohorts; no inference about other benchmark ordering follows.

**No new DuckDB, PostgreSQL or other SQL benchmark ran here.** Prior wins/losses remain in [analytical 046](PERFORMANCE_046.md), [development 061](CORE_READ_PATH_061.md), [six-engine service 047](SERVICE_047.md) and [complete history](BENCHMARK_HISTORY.md). Existing SQL/source retry/crash evidence in 068 remains separate and is not extended by this byte model. [Adoption assessment](ADOPTION_STATUS.md). No universal-superiority, Facebook-scale, PostgreSQL-replacement or production-readiness claim follows.

[Policy](benchmarks/compression-071/policy.json), [frozen order](benchmarks/compression-071/cohort-policy.json), [balance proof](benchmarks/compression-071/order-balance-pre-timing.json), [raw case index](benchmarks/compression-071/model-results.json), [all ratios and gates](benchmarks/compression-071/model-audit.json), [full frame inventory](benchmarks/compression-071/fixture-inventory.json), [input provenance](benchmarks/compression-071/input-provenance.json), [build/test proof](benchmarks/compression-071/build-proof.json), [oracle provenance](benchmarks/compression-071/oracle-provenance.json), [runtime](benchmarks/compression-071/runtime-provenance.json), [locked crates](benchmarks/compression-071/dependency-provenance.json), [reproduction](benchmarks/compression-071/REPRODUCE.md) and [next work](benchmarks/compression-071/NEXT_WORK.md). Individual raw stdout/status/error files, source, frozen executable and compiler/test logs are preserved alongside these. Core/input and three variant-frame ZIPs together retain every full file.

Further work should investigate a separately specified structural checkpoint approach, preserving durable idempotency/source offsets and explicit format/reader bounds. Do not turn these failures into a blind codec parameter search or trivial unchanged-page reuse comparison. A later engine candidate still needs compatibility and full SQL/source/retry/crash/concurrency/service qualification. English only; this computer only; no deployment/messages to others.

Private immutable evidence parts (all required for complete reproduction):

- [kestrel-sql-development-071-core-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-core-evidence.zip).
- [kestrel-sql-development-071-core-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-core-evidence.zip.sha256).
- [kestrel-sql-development-071-raw-a-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-a-evidence.zip).
- [kestrel-sql-development-071-raw-a-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-a-evidence.zip.sha256).
- [kestrel-sql-development-071-raw-b-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-b-evidence.zip).
- [kestrel-sql-development-071-raw-b-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-raw-b-evidence.zip.sha256).
- [kestrel-sql-development-071-zstd-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-zstd-evidence.zip).
- [kestrel-sql-development-071-zstd-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-071-zstd-evidence.zip.sha256).

Every server digest matches. All 106 previous assets and 20 engine tags/releases remain unchanged. The four ZIPs contain reports before these upload-link paragraphs.
