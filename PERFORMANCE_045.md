# 0.3.15: bounded reuse of independent scan handles

Fragmented live archives repeatedly opened and closed one synchronous file per segment and query. The selected cache retains at most one idle independently opened File per immutable segment and 128 idle files per store. Borrowing removes the file from the cache, so concurrent readers keep exclusive ownership; a cold or concurrent miss opens another independent file. File::try_clone is not used. Cached files live inside their Segment, without another segment reference, so retirement follows the existing snapshot lifetime.

Every streamed payload block is still read and CRC-checked; existing indexed-page caching is unchanged. Streaming retains the preceding seek/read path. I/O and checksum errors discard the current stream; full verification opens fresh files, bypasses both page and handle reuse, and clears idle files in its snapshot on failure. The idle limit does not limit active query handles. Reuse adds per-segment bookkeeping and up to 128 idle kernel resources; its counts include pinned retired segments from the same store. New process-local stats expose retained_stream_handles, stream_handle_opens and stream_handle_reuses. Reopen starts with no cached handles. Writers, receipt/source contracts, persisted fields, parsing and group kernels remain unchanged.

An earlier owned-offset read trial removed a separate seek call. Rust 1.97.1 has separate seek and read implementations; this motivated the experiment, not a guaranteed speedup. Its target fragmented unordered scan improved only about 0.4% in the paired trial, despite other mixed gains and regressions. It was not selected on its own. The full source, binary, build-harness snapshot and seven timed workloads are preserved. The handle-cache trial instead reduced that target about 40%, and improved tiny queries, with some slower guards retained. The candidate below is independently rebuilt and remeasured. [Pinned Rust Windows filesystem source](https://raw.githubusercontent.com/rust-lang/rust/1.97.1/library/std/src/sys/fs/windows.rs), [Windows handle implementation](https://raw.githubusercontent.com/rust-lang/rust/1.97.1/library/std/src/sys/pal/windows/handle.rs), [FileExt cursor semantics](https://doc.rust-lang.org/std/os/windows/fs/trait.FileExt.html).

Fresh DuckDB matrix: **59 wins / 1 loss** over 60 shapes; released 0.3.14 measured 58 wins and two losses. The matrix retains 108 engine/fixture/round cases and 5,940 samples. Separate uninstrumented controls retain 23,030 samples; 1,078 instrumented samples are excluded from competitive totals. Three rotated orders, three warmups, eleven samples and one thread are used in the matrix. Rust timers measure ArchiveSnapshot::query; DuckDB includes Python execute/fetchall, and native storage layouts differ. Builds, setup, checks and scrubs are untimed; timed workloads run serially on this shared Windows computer.

## Final alternating controls

Times are medians of pair medians; the paired ratio is the median candidate/baseline ratio inside each pair. Desktop variance can make these summaries differ. Smaller ratios are faster. Controls use 21 pairs of eleven samples per binary, except tiny queries (21 pairs of 101) and 100M rows (seven pairs of five). Matrix and one-query-per-process controls have different process histories; compare their own paired measurements rather than combining absolute times. Every repeated result matches and final archives are fully scrubbed.

| Control | Rows | Query | 0.3.14 ms | 0.3.15 ms | Paired candidate / baseline |
|---|---:|---|---:|---:|---:|
| final-pairs | 1,000,000 | group_sum | 9.5628 | 10.8955 | 1.0145 |
| final-pairs | 1,000,000 | group_full | 14.7023 | 14.2121 | 0.9799 |
| final-pairs | 1,000,000 | filtered_group | 9.8983 | 9.4163 | 0.9699 |
| wide-pairs | 1,000,000 | group_sum | 17.2000 | 17.1457 | 1.0089 |
| wide-pairs | 1,000,000 | group_full | 20.7441 | 22.3772 | 1.0167 |
| wide-pairs | 1,000,000 | filtered_group | 13.6846 | 13.7655 | 1.0096 |
| irregular-pairs | 1,000,000 | group_sum | 20.4065 | 18.7336 | 0.9214 |
| irregular-pairs | 1,000,000 | group_full | 22.6843 | 21.1916 | 0.9372 |
| irregular-pairs | 1,000,000 | filtered_group | 13.9120 | 10.9163 | 0.7873 |
| irregular-pairs | 1,000,000 | unordered_control | 7.8298 | 4.5515 | 0.5806 |
| highcard-guard-pairs | 1,000,000 | group_sum | 40.8102 | 40.7582 | 0.9990 |
| highcard-guard-pairs | 1,000,000 | group_full | 52.1039 | 51.7576 | 0.9983 |
| dense-guard-pairs | 1,000,000 | group_sum | 7.8067 | 7.5753 | 0.9779 |
| dense-guard-pairs | 1,000,000 | group_full | 11.1658 | 11.0280 | 0.9914 |
| dense-guard-pairs | 1,000,000 | filtered_group | 7.0061 | 6.8755 | 0.9881 |
| scan-guard-pairs | 1,000,000 | unordered | 3.0299 | 2.9737 | 0.9702 |
| scan-guard-pairs | 1,000,000 | sparse | 4.7827 | 4.7509 | 0.9989 |
| scan-guard-pairs | 1,000,000 | multi | 4.5512 | 4.4609 | 0.9667 |
| scan-guard-pairs | 1,000,000 | dense_group_guard | 9.2747 | 9.1960 | 0.9848 |
| tiny-guard-pairs | 1,000 | group_sum | 0.1178 | 0.0654 | 0.5603 |
| tiny-guard-pairs | 1,000 | group_full | 0.1319 | 0.0779 | 0.5872 |
| tiny-guard-pairs | 1,000 | filtered_group | 0.1781 | 0.1010 | 0.5752 |
| 10m-guard-pairs | 10,000,000 | group_sum | 70.4817 | 67.8682 | 0.9801 |
| 10m-guard-pairs | 10,000,000 | group_full | 106.4950 | 104.4285 | 0.9915 |
| 10m-guard-pairs | 10,000,000 | filtered_group | 62.6755 | 61.7647 | 0.9885 |
| 100m-guard-pairs | 100,000,000 | group_sum | 659.8192 | 654.5173 | 0.9925 |
| 100m-guard-pairs | 100,000,000 | group_full | 932.8255 | 925.6104 | 0.9913 |

Observed slower controls remain visible. The largest is wide-pairs/group_full at 1,000,000 rows: paired ratio 1.0167, or 1.67% slower in this run. A faster target does not imply that every query improved.

## Stage diagnosis, excluded from competitive results

| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |
|---|---|---:|---:|---:|
| sparse19 | group_sum | 4.340 / 4.336 | 0.165 / 0.164 | 3.367 / 3.378 |
| sparse19 | group_full | 4.389 / 4.339 | 0.166 / 0.162 | 5.546 / 5.500 |
| sparse19 | filtered_group | 4.240 / 4.218 | 0.627 / 0.623 | 1.698 / 1.676 |
| irregular5003 | group_sum | 5.826 / 3.669 | 0.174 / 0.172 | 12.606 / 14.241 |
| irregular5003 | group_full | 5.874 / 3.703 | 0.174 / 0.171 | 14.636 / 16.406 |
| irregular5003 | filtered_group | 5.787 / 3.611 | 0.635 / 0.625 | 5.704 / 5.806 |
| irregular5003 | unordered_control | 5.008 / 2.694 | 0.814 / 0.816 | 0.270 / 0.263 |

## Matched matrix

| Fixture | Query | 0.3.14 ms | 0.3.15 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 6.253 | 6.213 | 7.596 | 1.006x | ✅; 3/3 rounds |
| dense97 | group_full | 9.181 | 9.141 | 11.296 | 1.004x | ✅; 3/3 rounds |
| dense97 | filtered_group | 5.922 | 5.918 | 8.057 | 1.016x | ✅; 3/3 rounds |
| dense97 | unordered_control | 3.026 | 2.933 | 3.768 | 1.002x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.006 | 0.006 | 1.653 | 1.000x | ✅; 3/3 rounds |
| sparse19 | group_sum | 8.299 | 8.127 | 11.209 | 1.013x | ✅; 3/3 rounds |
| sparse19 | group_full | 10.452 | 10.230 | 14.690 | 1.022x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 6.701 | 6.636 | 10.566 | 1.005x | ✅; 3/3 rounds |
| sparse19 | unordered_control | 3.038 | 2.957 | 3.841 | 1.020x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.006 | 1.706 | 0.967x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 7.761 | 7.392 | 18.995 | 1.057x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 11.208 | 11.146 | 27.518 | 1.006x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 6.791 | 6.991 | 17.590 | 0.989x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 2.985 | 2.941 | 3.842 | 1.042x | ✅; 3/3 rounds |
| cardinality5003 | prefix_control | 0.006 | 0.006 | 1.706 | 0.932x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.005 | 17.324 | 1.102x | ✅; 3/3 rounds |
| nyc | day | 0.006 | 0.005 | 1.611 | 1.115x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.005 | 0.688 | 1.156x | ✅; 3/3 rounds |
| nyc | zone | 1.138 | 1.014 | 1.756 | 1.122x | ✅; 3/3 rounds |
| nyc | all_zones | 23.213 | 23.101 | 26.252 | 0.980x | ✅; 3/3 rounds |
| 10000000 | group_sum | 66.372 | 65.102 | 69.895 | 1.017x | ✅; 3/3 rounds |
| 10000000 | group_full | 93.593 | 93.398 | 103.942 | 1.008x | ✅; 3/3 rounds |
| 10000000 | filtered_group | 62.774 | 61.570 | 74.326 | 1.020x | ✅; 3/3 rounds |
| 10000000 | unordered_control | 31.986 | 31.461 | 35.703 | 1.017x | ✅; 3/3 rounds |
| 10000000 | prefix_control | 0.004 | 0.004 | 8.082 | 1.000x | ✅; 3/3 rounds |
| 100000000 | group_sum | 666.399 | 659.386 | 777.340 | 1.011x | ✅; 2/3 rounds |
| 100000000 | group_full | 940.498 | 966.894 | 1137.992 | 0.973x | ✅; 2/3 rounds |
| 100000000 | filtered_group | 631.336 | 624.164 | 871.063 | 0.998x | ✅; 3/3 rounds |
| 100000000 | unordered_control | 324.387 | 329.990 | 436.699 | 0.979x | ✅; 3/3 rounds |
| 100000000 | prefix_control | 0.007 | 0.008 | 114.434 | 0.841x | ✅; 3/3 rounds |

## Prior stress matrix

| Fixture | Query | 0.3.14 ms | 0.3.15 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 13.651 | 18.565 | 28.976 | 0.735x | ✅; 3/3 rounds |
| wide5003 | group_full | 15.627 | 25.779 | 29.270 | 1.050x | ✅; 2/3 rounds |
| wide5003 | filtered_group | 13.759 | 10.119 | 17.857 | 0.956x | ✅; 2/3 rounds |
| wide5003 | unordered_control | 3.004 | 3.127 | 6.749 | 0.954x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.006 | 0.006 | 2.223 | 0.918x | ✅; 3/3 rounds |
| collision19 | group_sum | 8.610 | 16.212 | 19.603 | 0.680x | ✅; 2/3 rounds |
| collision19 | group_full | 11.462 | 17.525 | 19.232 | 0.634x | ✅; 2/3 rounds |
| collision19 | filtered_group | 6.931 | 9.584 | 12.271 | 0.721x | ✅; 2/3 rounds |
| collision19 | unordered_control | 3.235 | 3.766 | 3.823 | 0.790x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.006 | 0.006 | 2.130 | 0.918x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 43.732 | 48.444 | 91.025 | 0.955x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 57.696 | 51.946 | 143.248 | 0.955x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 41.008 | 40.050 | 102.699 | 0.986x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 3.394 | 2.979 | 4.223 | 1.139x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.006 | 0.006 | 1.781 | 0.966x | ✅; 3/3 rounds |

## Key-pattern matrix

| Fixture | Query | 0.3.14 ms | 0.3.15 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| fibonacci19 | group_sum | 7.947 | 7.745 | 10.982 | 1.026x | ✅; 3/3 rounds |
| fibonacci19 | group_full | 9.976 | 10.151 | 14.589 | 0.983x | ✅; 3/3 rounds |
| fibonacci19 | filtered_group | 6.615 | 6.480 | 10.339 | 1.023x | ✅; 3/3 rounds |
| fibonacci19 | unordered_control | 2.890 | 2.817 | 3.751 | 1.026x | ✅; 3/3 rounds |
| fibonacci19 | prefix_control | 0.006 | 0.006 | 1.683 | 0.983x | ✅; 3/3 rounds |
| power19 | group_sum | 8.075 | 8.006 | 11.365 | 1.018x | ✅; 3/3 rounds |
| power19 | group_full | 10.238 | 10.314 | 15.144 | 0.993x | ✅; 3/3 rounds |
| power19 | filtered_group | 6.742 | 6.524 | 10.605 | 1.003x | ✅; 3/3 rounds |
| power19 | unordered_control | 2.959 | 2.900 | 3.814 | 1.020x | ✅; 3/3 rounds |
| power19 | prefix_control | 0.006 | 0.006 | 1.700 | 0.983x | ✅; 3/3 rounds |

## Irregular signed-key matrix

| Fixture | Query | 0.3.14 ms | 0.3.15 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| irregular5003 | group_sum | 28.301 | 25.207 | 24.190 | 1.051x | ❌; 1/3 rounds |
| irregular5003 | group_full | 31.135 | 28.742 | 35.939 | 1.043x | ✅; 3/3 rounds |
| irregular5003 | filtered_group | 19.052 | 14.966 | 21.727 | 1.234x | ✅; 3/3 rounds |
| irregular5003 | unordered_control | 8.476 | 3.984 | 5.162 | 2.169x | ✅; 3/3 rounds |
| irregular5003 | prefix_control | 0.007 | 0.006 | 2.274 | 1.014x | ✅; 3/3 rounds |

## Correctness, durable retry and resource lifetime

All 76 Rust tests pass in debug/release, formatting and both Clippy configurations. The existing eight-reader positional oracle now verifies actual handle reuse. A new 130-segment test verifies the 128-idle-file ceiling, fresh full scrubs, pinned snapshot correctness through compaction, release of 32 retired segment caches, and queries after the Archive owner is dropped. A second new test warms the cache, detects payload corruption and truncation, restores the fixture, verifies it and checks cold reopen.

The final CLI/bridge match 4,000 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping and 600 each for key patterns, medium, dense, sparse and scan cases. Signed wide shared SUM/AVG JSON remains exact after confirmed retry/reopen. An additional untimed bridge suite checks 104 manual Python integer oracles, including 96 requests across eight clients, exact beyond-i64 sums, handle metrics, fresh scrub behavior, warmed corruption rejection, cache invalidation and known receipts after reopen. These concurrent correctness requests are not a new requests/s benchmark.

The same current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 forced process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL checks. Snapshot retirement and cached descriptors remain process-local; they do not change durable publication. Process kills and injected failures do not qualify physical power loss.

The cache consumes extra idle handles and memory bookkeeping. Concurrent misses still open independent files, and active handle admission is unchanged. Beyond 128 retained files, other reads use the ordinary path. Only DuckDB is freshly competed; the last multi-server network matrix remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Cold I/O, server requests/s, distributed scale, universal superiority and production readiness are unqualified.

## Reproduce and inspect

Run checks_045.py, build_source_adapter_045.py, time_045.py, run_045.py, report_045.py, docs_045.py and package_045.py serially with pinned local dependencies. Trials have their own immutable sources, binaries, build-harness snapshots and work orders. Restore trial core sources in an isolated checkout before rebuilding them. Never overwrite completed reports or archives, and never overlap compilation, qualification or packaging with timed database work. Release 0.3.15 uses experiment identifier 045.

- [Complete gates and all scores](benchmarks/reader-045-audit.json)
- [Fragmented final pairs](benchmarks/reader-045-irregular-pairs.json)
- [Fragmented profiles](benchmarks/reader-045-irregular-profiles.json)
- [Small sparse final pairs](benchmarks/reader-045-final-pairs.json)
- [Wide sparse final pairs](benchmarks/reader-045-wide-pairs.json)
- [Tiny queries](benchmarks/reader-045-tiny-guard-pairs.json)
- [Single-segment scan guards](benchmarks/reader-045-scan-guard-pairs.json)
- [High-cardinality guards](benchmarks/reader-045-highcard-guard-pairs.json)
- [Dense guards](benchmarks/reader-045-dense-guard-pairs.json)
- [10M-row guards](benchmarks/reader-045-10m-guard-pairs.json)
- [100M-row guards](benchmarks/reader-045-100m-guard-pairs.json)
- [Actual bridge concurrency/reuse/corruption oracles](benchmarks/reader-045-verification.json)
- [Unselected offset-only trial](benchmarks/reader-045-offset-unselected.json)
- [Offset-only source and binary proof](benchmarks/trial-045-owned-offset-read/proof.json)
- [Selected cache trial](benchmarks/trial-045-bounded-owned-handles/proof.json)
- [Selection and every trial ratio](benchmarks/reader-045-selection.json)
- [Build provenance](benchmarks/rust-checks-045.json)
- [Final timed work order](benchmarks/reader-045-run-order.json)
- [Qualification work order](benchmarks/correctness-045-run-order.json)
- [All historical results and unsuccessful evidence](BENCHMARK_HISTORY.md)
