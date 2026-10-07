# Bounded writer catalog buffer: development 067

Measured 2026-10-07T09:53:32.029492+00:00. Baseline **released 0.3.16**, candidate **0.3.17-dev.67**. The candidate does not advance to service qualification or the supported release. Supported source and binaries remain 0.3.16.

The engine shows **17.1% less catalog encoding time at 50K receipts and 19.8% less at 99K**, using matched ratios; the corresponding unchanged-engine encoding ratios are 1.0055 and 1.0048. All six candidate memory guards pass. End-to-end qualification fails: the 50K total ratio is 1.5189 and multiple latency/calibration checks fail. The large 99K apparent total win is also unqualified because its A/A total ratio is 0.5751. These outcomes do not establish a reliable overall speedup or attribute a slowdown solely to the code change.

This is the first real engine test after the fixed-input encoder models in [065/066](ENCODER_PROFILES_065_066.md). It excludes the parser, SDK and larger-compaction experiments. Every prior result, failed trial, asset and frozen morning report remains accessible in [history](BENCHMARK_HISTORY.md) and [archive navigation](ARCHIVE.md).

The writer uses the same serde JSON serializer with reusable private scratch memory. It clears the buffer after successful and failed publication, retains capacity at most **16 MiB**, and drops larger allocations. Reader snapshots never own the buffer. On-disk signatures, catalog ordering, receipt generations, checkpoint/delta rules, metadata budget, synchronization and merge fan-in are unchanged. Oversized valid catalog output still works; the cap limits retained memory, not output size.

## Fresh before/after measurements

Six matched Latin-square rounds × three starting receipt histories × A/B/candidate = **54 sequential native cases**. A and B execute one exact released binary at one path. Each case appends **256 identified batches × 100 rows**, then uses the existing live 64-small-run trigger with released **32-run** compaction. All labels perform seven maintenance calls and end with 39 small runs, plus one prefill segment for nonempty histories.

The exact released native driver is reused from 064, SHA-256 `75467d1f1fb7558aedac6c28fc2fbc78fd61de0778a46dc22f72595335ef544a`; the candidate links the same driver source to its freshly qualified library. No baseline rebuild occurred in 067. The preserved auditor's inherited scope phrase "newly linked identical driver" describes shared driver logic; [build provenance](benchmarks/buffer-067/native-driver-build.json) records the reuse explicitly. All raw metadata remains unchanged.

**13,824 durable append samples; 1,382,400 new rows; 162 cold duplicate retries; 195,091,200 bytes CRC scrubbed.** Setup, receipt prefill, stats, reference checks and cold reopen sit outside append timers. The primary total charges all append and compact/reclaim timings. Large-history buffers may already be allocated by prefill; this is not a cold-start encoding claim. Full-process peak memory and process wall time include setup and validation. No compilation, qualification, audit, package or Git work overlaps the timed cohort. No sample is dropped or overwritten.

Times below are milliseconds unless marked MiB. Before/after display columns are medians of per-case measurements. Decision ratios are **medians of six matched per-round ratios**, rather than ratios of the display medians. Quantiles use Type7 interpolation over all 256 samples, including tails.

| Starting receipts/rows | Metric | Released A | Candidate | Candidate/A paired | Identical B/A paired |
|---:|---|---:|---:|---:|---:|
| 0 | Append + maintenance | 5732.0120 | 7633.7335 | 0.932386 | 1.032412 |
| 0 | Catalog encode stages | 2.5283 | 1.4108 | 0.561734 | 0.936341 |
| 0 | Append p50 | 16.9186 | 16.6751 | 0.987951 | 0.698218 |
| 0 | Append p99 | 193.1498 | 202.7163 | 0.998569 | 0.779437 |
| 0 | Append max | 341.3558 | 435.2772 | 1.414198 | 0.835637 |
| 0 | Cold reopen | 3.2844 | 3.2855 | 0.993543 | 0.977006 |
| 0 | Peak working set, MiB | 4.803 | 4.789 | 0.999597 | 1.002453 |
| 0 | Peak commit, MiB | 1.545 | 1.588 | 1.034774 | 1.009832 |
| 50,000 | Append + maintenance | 3440.8157 | 24798.7197 | 1.518861 | 3.908472 |
| 50,000 | Catalog encode stages | 126.6872 | 106.8426 | 0.829366 | 1.005518 |
| 50,000 | Append p50 | 7.6766 | 19.4737 | 1.859511 | 1.800520 |
| 50,000 | Append p99 | 91.7578 | 1015.3887 | 1.180294 | 7.381495 |
| 50,000 | Append max | 219.6170 | 1729.2653 | 1.834623 | 3.662312 |
| 50,000 | Cold reopen | 59.1312 | 59.0097 | 1.001658 | 1.016122 |
| 50,000 | Peak working set, MiB | 26.162 | 26.254 | 1.010379 | 1.000599 |
| 50,000 | Peak commit, MiB | 27.752 | 27.795 | 1.005675 | 1.001197 |
| 99,000 | Append + maintenance | 32713.3303 | 3786.9369 | 0.480885 | 0.575091 |
| 99,000 | Catalog encode stages | 252.0969 | 202.7531 | 0.801929 | 1.004818 |
| 99,000 | Append p50 | 23.8626 | 6.1059 | 0.312609 | 0.711893 |
| 99,000 | Append p99 | 1317.5508 | 145.4637 | 0.568514 | 0.684298 |
| 99,000 | Append max | 2840.8424 | 238.4165 | 0.645369 | 0.370914 |
| 99,000 | Cold reopen | 119.9718 | 121.6077 | 1.047096 | 0.959279 |
| 99,000 | Peak working set, MiB | 43.416 | 43.678 | 1.006070 | 1.000090 |
| 99,000 | Peak commit, MiB | 50.279 | 50.254 | 0.999379 | 0.999845 |

All per-round values, stage counters, histograms, oversized tails and raw bytes are in [native audit](benchmarks/buffer-067/native-audit.json), [case order and frozen hashes](benchmarks/buffer-067/native-policy.json), and [raw records](benchmarks/buffer-067/native-results.json). Individual stdout/status files are retained alongside these reports; the immutable ZIP also holds full stores.

## Predeclared decision

Failures: **1/4 speed goals, 4/19 candidate guards, 11/24 identical-baseline checks**. The candidate does not advance to service qualification or the supported release.

At 50K/99K histories the targets are 15% less summed catalog encoding time and 3% less append-plus-maintenance time. The small-history total guard is 1.05; all histories require p50≤1.05, p99/max/reopen≤1.10 and peak working set/commit≤1.15. A/A calibration must remain within 0.90–1.10 on each of eight metrics at each size. Unavailable memory fails the guard. These limits were saved [before execution](benchmarks/buffer-067/policy.json), and the independent auditor was hashed before the first timed case.

The smaller total goal follows the prior measured bottleneck: encoder model 066 saved 21–23% encoding CPU, while released 99K encoding in 064 was 18.33% of summed publication stages. That predicts a small end-to-end effect, not a 23% database speedup. Actual growing catalogs, allocations, disk sync, reclamation and memory must qualify independently. Stage totals do not explain a p99 sample causally.

| Result | Starting receipts | Gate | Metric | Matched ratio | Required |
|---|---:|---|---|---:|---|
| ✅ | 0 | guard | p50_ms | 0.987951149 | ≤ 1.05 |
| ✅ | 0 | guard | p99_ms | 0.998568688 | ≤ 1.1 |
| ❌ | 0 | guard | max_ms | 1.414197833 | ≤ 1.1 |
| ✅ | 0 | guard | reopen_ms | 0.993543048 | ≤ 1.1 |
| ✅ | 0 | guard | peak_working_set_bytes | 0.999597157 | ≤ 1.15 |
| ✅ | 0 | guard | peak_commit_bytes | 1.034774132 | ≤ 1.15 |
| ✅ | 0 | guard | append_plus_maintenance_ms | 0.932386207 | ≤ 1.05 |
| ✅ | 0 | identity | append_plus_maintenance_ms | 1.032411716 | 0.9–1.1 |
| ✅ | 0 | identity | catalog_encode_ms | 0.936340873 | 0.9–1.1 |
| ❌ | 0 | identity | p50_ms | 0.698218267 | 0.9–1.1 |
| ❌ | 0 | identity | p99_ms | 0.779436736 | 0.9–1.1 |
| ❌ | 0 | identity | max_ms | 0.835636548 | 0.9–1.1 |
| ✅ | 0 | identity | reopen_ms | 0.977005692 | 0.9–1.1 |
| ✅ | 0 | identity | peak_working_set_bytes | 1.002452984 | 0.9–1.1 |
| ✅ | 0 | identity | peak_commit_bytes | 1.009831508 | 0.9–1.1 |
| ❌ | 50,000 | goal | append_plus_maintenance_ms | 1.518861120 | ≤ 0.97 |
| ✅ | 50,000 | goal | catalog_encode_ms | 0.829365881 | ≤ 0.85 |
| ❌ | 50,000 | guard | p50_ms | 1.859510987 | ≤ 1.05 |
| ❌ | 50,000 | guard | p99_ms | 1.180293759 | ≤ 1.1 |
| ❌ | 50,000 | guard | max_ms | 1.834623477 | ≤ 1.1 |
| ✅ | 50,000 | guard | reopen_ms | 1.001658124 | ≤ 1.1 |
| ✅ | 50,000 | guard | peak_working_set_bytes | 1.010378567 | ≤ 1.15 |
| ✅ | 50,000 | guard | peak_commit_bytes | 1.005674992 | ≤ 1.15 |
| ❌ | 50,000 | identity | append_plus_maintenance_ms | 3.908471763 | 0.9–1.1 |
| ✅ | 50,000 | identity | catalog_encode_ms | 1.005517636 | 0.9–1.1 |
| ❌ | 50,000 | identity | p50_ms | 1.800520189 | 0.9–1.1 |
| ❌ | 50,000 | identity | p99_ms | 7.381494696 | 0.9–1.1 |
| ❌ | 50,000 | identity | max_ms | 3.662312164 | 0.9–1.1 |
| ✅ | 50,000 | identity | reopen_ms | 1.016121526 | 0.9–1.1 |
| ✅ | 50,000 | identity | peak_working_set_bytes | 1.000598711 | 0.9–1.1 |
| ✅ | 50,000 | identity | peak_commit_bytes | 1.001196677 | 0.9–1.1 |
| ✅ | 99,000 | goal | append_plus_maintenance_ms | 0.480885463 | ≤ 0.97 |
| ✅ | 99,000 | goal | catalog_encode_ms | 0.801929203 | ≤ 0.85 |
| ✅ | 99,000 | guard | p50_ms | 0.312608531 | ≤ 1.05 |
| ✅ | 99,000 | guard | p99_ms | 0.568514081 | ≤ 1.1 |
| ✅ | 99,000 | guard | max_ms | 0.645369033 | ≤ 1.1 |
| ✅ | 99,000 | guard | reopen_ms | 1.047096304 | ≤ 1.1 |
| ✅ | 99,000 | guard | peak_working_set_bytes | 1.006070375 | ≤ 1.15 |
| ✅ | 99,000 | guard | peak_commit_bytes | 0.999378734 | ≤ 1.15 |
| ❌ | 99,000 | identity | append_plus_maintenance_ms | 0.575090963 | 0.9–1.1 |
| ✅ | 99,000 | identity | catalog_encode_ms | 1.004817861 | 0.9–1.1 |
| ❌ | 99,000 | identity | p50_ms | 0.711892816 | 0.9–1.1 |
| ❌ | 99,000 | identity | p99_ms | 0.684297884 | 0.9–1.1 |
| ❌ | 99,000 | identity | max_ms | 0.370914268 | 0.9–1.1 |
| ✅ | 99,000 | identity | reopen_ms | 0.959278957 | 0.9–1.1 |
| ✅ | 99,000 | identity | peak_working_set_bytes | 1.000089985 | 0.9–1.1 |
| ✅ | 99,000 | identity | peak_commit_bytes | 0.999844624 | 0.9–1.1 |

## Correctness, durable retries and format compatibility

- ✅ **81 debug + 81 release tests**, format and strict default/fault Clippy; four new tests cover byte equivalence across size/order/escaping/extreme values, bounded release after oversized output and serializer errors, checkpoints/deltas/compaction/pinned readers/cold retries, and poisoning/recovery after a real post-encode I/O failure.
- ✅ **4,000 varied SQL cases against each reference**, full expanded/cache/dense/sparse/filter suites, wide integer JSON and 104 reader oracles.
- ✅ **56 publication cuts**, **22 rejected corruptions**, **32 concurrent forced kills**, **14 source publication cuts** and **8 source forced kills**. Original receipt generations, whole-batch results, source positions and second-reopen retry deduplication hold. All 32 validated group-kill stores are retained by the adapted harness.
- ✅ **30,000 Parquet rows / 300 source intervals / 42 DuckDB correctness oracles**; this is an oracle check, not a fresh DuckDB performance comparison.
- ✅ **76 catalog +76 segment files byte-for-byte identical** between the released and candidate writers. Both versions reopen each other's stores and preserve receipt generations/reject payload collisions. The four retained format fixtures include checkpoint/delta/compaction sequences and **70,001 receipts with 128-byte seed IDs**, producing a valid catalog larger than 16 MiB. Buffer reset and capacity bounds are checked inside the Rust tests.
- ✅ A [post-timing exact-file audit](benchmarks/buffer-067/native-format-audit.json) also compares every one of the 54 full native stores across all versions, labels and rounds at each history size. This adds correctness evidence and changes no timing decision.

See [independent qualification audit](benchmarks/buffer-067/qualification-audit.json), [all 13 suite commands](benchmarks/buffer-067/qualification.json), [Rust build proof](benchmarks/buffer-067/lab/outputs/kestrel-sql/benchmarks/rust-checks-067.json), and [exact format/reopen oracle](benchmarks/buffer-067/byte-equivalence.json). Forced process termination on a live filesystem does not establish physical-power-loss durability.

## DuckDB wins/losses and remaining work

**No fresh competitor timing in 067.** ✅/❌ above compare candidate with released Kestrel and unchanged A/A controls. Historical [061 DuckDB comparison](CORE_READ_PATH_061.md) remains separate:60 median analytic wins,59/60 wins in all three rounds; the closest result needs caution. Historical PostgreSQL/network losses remain visible in [multi-engine stress047](SERVICE_047.md) and later service trials. This trial does not change those wins/losses or qualify a production PostgreSQL replacement.

The model-only gain in 066 is not an engine-release gain. Native calibration/guard failures, when present, remain disqualifying; selecting a favorable round or ignoring memory is not an upgrade. Further work must follow the actual stage and memory evidence and keep this complete cohort intact. Service results cannot be inferred from sequential closed-loop native latency. The shared Windows host and external activity remain limitations; A/A checks measure repeatability without attributing stalls to another process.

Exact sources, frozen normal/fault executables, all qualification logs and failures, raw54-case reports and every surviving store are preserved. The source in this evidence bundle is development-only. [Preservation inventory](benchmarks/buffer-067-preservation.json) and [bundle checksum/CRC check](benchmarks/buffer-067-bundle-check.json) become available after packaging. [Reproduction instructions](benchmarks/buffer-067/REPRODUCE.md) explain how to build a new independent cohort without overwriting this one.

Private immutable [full writer-buffer evidence and stores](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-067-buffer-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-067-buffer-evidence.zip.sha256). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.
