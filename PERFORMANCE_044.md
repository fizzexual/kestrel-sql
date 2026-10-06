# 0.3.14: adaptive sparse SUM kernels and fewer cache writes

Exact tagged cache hits now retain their existing key/slot entry; only misses populate or replace it. At a block entered with the small cache active, a single shared SUM/AVG column can update exact counts and its typed i128 sum during key lookup. Repeated SUM/AVG projections share state. Larger-cache and plain-hash modes retain the preceding two-pass mapper; mixed reductions retain their preceding arrays. The selected block finishes its kernel before growth or collision fallback changes the next block. Cache budgets, seeded tags, randomized authoritative HashMap, dense grouping, readers, storage and writers are unchanged. Existing reserved slot capacity remains; no extra query allocation is introduced.

Profiles of released 0.3.13 put about 13 ms of a 21 ms irregular-key SUM query in aggregation. Skipping redundant cache stores improved the first trial. A general enum-based fused loop then regressed wide SUM about 9% and high-cardinality SUM about 8.5%; its complete source, binary and timings are preserved. Moving the typed vector outside dispatch helped small groups but still failed to improve irregular SUM and slowed high-cardinality SUM about 3.8%. The selected trial limits fusion to the small-cache kernel and keeps the earlier wider mapper. It passes the trial guards, then is independently rebuilt and remeasured below.

Fresh comparisons retain 108 engine/fixture/round cases, 60 shapes and 5,940 samples. Additional uninstrumented controls retain 23,030 samples; 924 instrumented samples are excluded from competitive totals. Matrix cases use three rotated orders, three warmups, eleven samples and one thread. Rust timers measure ArchiveSnapshot::query; DuckDB timers include Python execute/fetchall. Native storage layouts differ. Builds, setup, result checks and scrubs are untimed, and workloads run serially on this shared Windows computer.

DuckDB scores: matched 30 wins / 0 losses; prior stress 15 / 0; patterns 10 / 0; irregular keys 3 / 2. The released 0.3.13 matrix measured 58 wins and two losses; older measurements remain preserved.

## Final alternating controls

Before/after times are medians of pair medians. The paired ratio is the median candidate/baseline ratio within each pair; these summaries can differ during desktop variance. Lower ratios are faster. Controls use 21 pairs of eleven samples per binary, except tiny queries (21 pairs of 101) and 100M rows (seven pairs of five). Every repeated result matches, and final archives are scrubbed.

| Control | Rows | Query | 0.3.13 ms | 0.3.14 ms | Paired candidate / baseline |
|---|---:|---|---:|---:|---:|
| final-pairs | 1,000,000 | group_sum | 8.5662 | 8.0128 | 0.9307 |
| final-pairs | 1,000,000 | group_full | 10.6736 | 10.3449 | 0.9565 |
| final-pairs | 1,000,000 | filtered_group | 7.0433 | 6.7216 | 0.9535 |
| wide-pairs | 1,000,000 | group_sum | 12.4751 | 12.1789 | 0.9540 |
| wide-pairs | 1,000,000 | group_full | 14.9833 | 14.4894 | 0.9798 |
| wide-pairs | 1,000,000 | filtered_group | 10.1285 | 9.7414 | 0.9741 |
| irregular-pairs | 1,000,000 | group_sum | 20.7696 | 20.7920 | 0.9800 |
| irregular-pairs | 1,000,000 | group_full | 24.3562 | 24.2156 | 0.9968 |
| irregular-pairs | 1,000,000 | filtered_group | 14.9955 | 14.7163 | 0.9816 |
| irregular-pairs | 1,000,000 | unordered_control | 7.7957 | 7.7791 | 0.9926 |
| highcard-guard-pairs | 1,000,000 | group_sum | 41.2103 | 41.5370 | 1.0073 |
| highcard-guard-pairs | 1,000,000 | group_full | 51.1538 | 51.2703 | 0.9951 |
| dense-guard-pairs | 1,000,000 | group_sum | 7.6061 | 7.6919 | 1.0027 |
| dense-guard-pairs | 1,000,000 | group_full | 11.2557 | 11.1119 | 0.9825 |
| dense-guard-pairs | 1,000,000 | filtered_group | 7.0085 | 6.9010 | 0.9908 |
| scan-guard-pairs | 1,000,000 | unordered | 3.0865 | 2.9979 | 0.9755 |
| scan-guard-pairs | 1,000,000 | sparse | 4.8439 | 4.8470 | 0.9949 |
| scan-guard-pairs | 1,000,000 | multi | 4.0695 | 4.0668 | 1.0011 |
| scan-guard-pairs | 1,000,000 | dense_group_guard | 9.3220 | 9.2661 | 0.9997 |
| tiny-guard-pairs | 1,000 | group_sum | 0.1164 | 0.1142 | 0.9844 |
| tiny-guard-pairs | 1,000 | group_full | 0.1284 | 0.1338 | 1.0422 |
| tiny-guard-pairs | 1,000 | filtered_group | 0.1098 | 0.1098 | 1.0063 |
| 10m-guard-pairs | 10,000,000 | group_sum | 67.5568 | 66.4475 | 0.9896 |
| 10m-guard-pairs | 10,000,000 | group_full | 93.7053 | 93.7839 | 0.9984 |
| 10m-guard-pairs | 10,000,000 | filtered_group | 63.1219 | 62.4602 | 0.9913 |
| 100m-guard-pairs | 100,000,000 | group_sum | 667.5880 | 658.5151 | 0.9876 |
| 100m-guard-pairs | 100,000,000 | group_full | 940.8125 | 934.3084 | 0.9906 |

Observed slower controls are retained in the table and audit. The largest is tiny-guard-pairs/group_full at 1,000 rows: paired ratio 1.0422 (4.22% slower in this run). The candidate does not improve every query; these desktop measurements do not establish whether small timing shifts persist across machines.

## Stage diagnosis, excluded from competitive results

| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |
|---|---|---:|---:|---:|
| sparse19 | group_sum | 4.363 / 4.315 | 0.168 / 0.166 | 3.988 / 3.392 |
| sparse19 | group_full | 4.362 / 4.382 | 0.165 / 0.165 | 5.932 / 5.581 |
| sparse19 | filtered_group | 4.293 / 4.253 | 0.699 / 0.634 | 2.012 / 1.695 |
| irregular5003 | group_sum | 5.920 / 5.867 | 0.181 / 0.179 | 12.994 / 12.732 |
| irregular5003 | group_full | 5.904 / 5.946 | 0.179 / 0.181 | 15.089 / 14.697 |
| irregular5003 | filtered_group | 5.917 / 5.885 | 0.714 / 0.644 | 6.038 / 5.795 |

## Matched matrix

| Fixture | Query | 0.3.13 ms | 0.3.14 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 6.294 | 6.412 | 7.529 | 0.986x | ✅; 3/3 rounds |
| dense97 | group_full | 9.131 | 9.166 | 11.337 | 0.996x | ✅; 3/3 rounds |
| dense97 | filtered_group | 5.988 | 5.822 | 8.023 | 1.030x | ✅; 3/3 rounds |
| dense97 | unordered_control | 3.104 | 2.984 | 3.755 | 1.015x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.006 | 0.006 | 1.679 | 1.018x | ✅; 3/3 rounds |
| sparse19 | group_sum | 8.495 | 8.115 | 11.201 | 1.047x | ✅; 3/3 rounds |
| sparse19 | group_full | 10.375 | 10.231 | 14.777 | 1.023x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 6.907 | 6.653 | 10.470 | 1.040x | ✅; 3/3 rounds |
| sparse19 | unordered_control | 3.034 | 2.944 | 3.792 | 1.040x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.006 | 1.698 | 1.019x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 7.557 | 7.642 | 18.674 | 0.991x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 10.898 | 10.889 | 27.486 | 1.004x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 6.856 | 6.799 | 17.270 | 1.003x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 2.997 | 2.932 | 3.870 | 1.029x | ✅; 3/3 rounds |
| cardinality5003 | prefix_control | 0.006 | 0.006 | 1.715 | 1.000x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.005 | 17.422 | 1.156x | ✅; 3/3 rounds |
| nyc | day | 0.005 | 0.005 | 1.614 | 1.078x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.004 | 0.695 | 1.095x | ✅; 3/3 rounds |
| nyc | zone | 1.115 | 1.103 | 1.759 | 1.013x | ✅; 3/3 rounds |
| nyc | all_zones | 22.700 | 22.528 | 25.715 | 1.032x | ✅; 3/3 rounds |
| 10000000 | group_sum | 67.210 | 66.615 | 70.813 | 1.008x | ✅; 3/3 rounds |
| 10000000 | group_full | 95.936 | 95.692 | 106.225 | 1.003x | ✅; 3/3 rounds |
| 10000000 | filtered_group | 63.749 | 63.356 | 75.583 | 1.007x | ✅; 3/3 rounds |
| 10000000 | unordered_control | 32.930 | 31.718 | 35.796 | 1.009x | ✅; 3/3 rounds |
| 10000000 | prefix_control | 0.004 | 0.004 | 8.267 | 1.027x | ✅; 3/3 rounds |
| 100000000 | group_sum | 677.119 | 664.237 | 794.605 | 1.013x | ✅; 3/3 rounds |
| 100000000 | group_full | 948.949 | 957.717 | 1139.406 | 0.991x | ✅; 3/3 rounds |
| 100000000 | filtered_group | 636.780 | 625.501 | 838.633 | 1.018x | ✅; 3/3 rounds |
| 100000000 | unordered_control | 328.007 | 323.691 | 357.964 | 1.013x | ✅; 2/3 rounds |
| 100000000 | prefix_control | 0.007 | 0.008 | 74.226 | 0.949x | ✅; 3/3 rounds |

## Prior stress matrix

| Fixture | Query | 0.3.13 ms | 0.3.14 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 13.718 | 13.220 | 20.142 | 1.057x | ✅; 3/3 rounds |
| wide5003 | group_full | 16.521 | 15.483 | 28.735 | 1.044x | ✅; 3/3 rounds |
| wide5003 | filtered_group | 12.240 | 10.362 | 17.771 | 1.181x | ✅; 3/3 rounds |
| wide5003 | unordered_control | 3.236 | 3.301 | 4.080 | 1.008x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.006 | 0.006 | 1.839 | 1.017x | ✅; 3/3 rounds |
| collision19 | group_sum | 8.441 | 7.839 | 11.138 | 1.079x | ✅; 3/3 rounds |
| collision19 | group_full | 10.817 | 10.133 | 14.813 | 1.067x | ✅; 3/3 rounds |
| collision19 | filtered_group | 7.196 | 6.740 | 10.391 | 1.068x | ✅; 3/3 rounds |
| collision19 | unordered_control | 2.989 | 2.939 | 3.748 | 1.018x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.006 | 0.006 | 1.668 | 1.018x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 40.735 | 41.120 | 91.091 | 0.992x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 50.584 | 52.025 | 131.896 | 0.959x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 34.500 | 34.586 | 94.421 | 0.996x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 3.067 | 2.924 | 3.833 | 1.051x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.006 | 0.005 | 1.707 | 1.018x | ✅; 3/3 rounds |

## Key-pattern matrix

| Fixture | Query | 0.3.13 ms | 0.3.14 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| fibonacci19 | group_sum | 8.642 | 8.048 | 11.249 | 1.074x | ✅; 3/3 rounds |
| fibonacci19 | group_full | 11.564 | 10.359 | 14.800 | 1.001x | ✅; 3/3 rounds |
| fibonacci19 | filtered_group | 7.212 | 6.683 | 10.283 | 1.072x | ✅; 3/3 rounds |
| fibonacci19 | unordered_control | 2.948 | 2.916 | 3.756 | 1.010x | ✅; 3/3 rounds |
| fibonacci19 | prefix_control | 0.006 | 0.006 | 1.666 | 1.018x | ✅; 3/3 rounds |
| power19 | group_sum | 8.646 | 7.955 | 11.263 | 1.116x | ✅; 3/3 rounds |
| power19 | group_full | 10.882 | 10.513 | 14.992 | 1.034x | ✅; 3/3 rounds |
| power19 | filtered_group | 7.064 | 6.637 | 10.463 | 1.072x | ✅; 3/3 rounds |
| power19 | unordered_control | 2.997 | 2.910 | 3.744 | 1.030x | ✅; 3/3 rounds |
| power19 | prefix_control | 0.006 | 0.006 | 1.680 | 1.018x | ✅; 3/3 rounds |

## Irregular signed-key matrix

| Fixture | Query | 0.3.13 ms | 0.3.14 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| irregular5003 | group_sum | 20.950 | 20.651 | 17.429 | 1.017x | ❌; 0/3 rounds |
| irregular5003 | group_full | 23.084 | 22.945 | 25.777 | 1.017x | ✅; 3/3 rounds |
| irregular5003 | filtered_group | 14.131 | 13.803 | 15.490 | 1.020x | ✅; 3/3 rounds |
| irregular5003 | unordered_control | 5.872 | 5.707 | 3.811 | 1.032x | ❌; 0/3 rounds |
| irregular5003 | prefix_control | 0.005 | 0.005 | 1.687 | 0.981x | ✅; 3/3 rounds |

## Correctness, durable retry and limits

All 74 Rust tests pass in debug/release, formatting and both Clippy configurations. The new independent BTreeMap oracle verifies filtered wide counts, exact i128 SUM/AVG and repeated SUM across small, constructed-collision, large and plain-hash cache modes. It includes 25,015 rows per mode, signed extremes, empty selections and cache/fallback transitions. The final binaries match 4,000 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping and 600 each for key patterns, medium groups, dense shared sums, focused sparse shared sums and scans. Actual dense and sparse bridge plans emit exact signed beyond-i64 sums after confirmed retry and reopen, including AVG and repeated SUM.

The current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 forced process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL checks. Source hashes verify unchanged readers, writers, formats, dense kernels, source contract and parsing. Injected failures and process kills do not qualify physical power loss.

The initial full build passed its 74 debug/release tests but Clippy rejected a parity expression in the new test. Its logs and original source are preserved. The equivalent is_multiple_of expression changes test code only; all full checks were rerun. Restricted PowerShell and a subsequent parameter-set error initially blocked preservation of the log directory without replacing it. Native absolute-path checks and Move-Item then preserved the directory; the workflow note is linked below.

The selected kernel adds code specialization and preserves an intermediate vector reservation. Existing cache seeds and collisions still vary lookup cost; every guard and unsuccessful trial remains visible. Timing shifts on unchanged dense/scan/prefix paths cannot be attributed to this sparse change. Only DuckDB is freshly competed; the last multi-server network comparison remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Network requests/s, cold I/O, distributed scale and production readiness remain unqualified.

## Reproduce and inspect

Run checks_044.py, build_source_adapter_044.py, time_044.py, run_044.py, report_044.py, docs_044.py and package_044.py serially with pinned local dependencies. Completed outputs and release archives are immutable. Controls reuse retained fixtures; matrices can seed independently. Never overlap compilation, tests or packaging with timed database work. Release 0.3.14 uses experiment identifier 044.

- [Complete gates and scores](benchmarks/sparse-044-audit.json)
- [Small sparse final pairs](benchmarks/sparse-044-final-pairs.json)
- [Wide sparse final pairs](benchmarks/sparse-044-wide-pairs.json)
- [Irregular signed-key pairs](benchmarks/sparse-044-irregular-pairs.json)
- [High-cardinality guard](benchmarks/sparse-044-highcard-guard-pairs.json)
- [Dense guard](benchmarks/sparse-044-dense-guard-pairs.json)
- [Scan guard](benchmarks/sparse-044-scan-guard-pairs.json)
- [Tiny-query guard](benchmarks/sparse-044-tiny-guard-pairs.json)
- [10M-row guard](benchmarks/sparse-044-10m-guard-pairs.json)
- [100M-row guard](benchmarks/sparse-044-100m-guard-pairs.json)
- [Final small-cache profiles](benchmarks/sparse-044-final-profiles.json)
- [Final irregular-key profiles](benchmarks/sparse-044-irregular-profiles.json)
- [Released baseline profiles](benchmarks/irregular-044-baseline-profiles.json)
- [Focused sparse SQL/wide JSON qualification](benchmarks/sparse-044-differential.json)
- [First write-on-miss trial](benchmarks/trial-044-write-on-miss/proof.json)
- [Rejected enum-based fusion](benchmarks/sparse-044-rejected-enum-fusion.json)
- [Unselected broad typed fusion](benchmarks/sparse-044-rejected-wide-typed-fusion.json)
- [Selected adaptive trial](benchmarks/trial-044-small-cache-shared-sum/proof.json)
- [Trial selection and every ratio](benchmarks/sparse-044-selection.json)
- [Preserved Clippy failure and workflow repair](benchmarks/sparse-044-clippy-repair.json)
- [Build provenance](benchmarks/rust-checks-044.json)
- [Final timed work order](benchmarks/sparse-044-run-order.json)
- [Qualification work order](benchmarks/correctness-044-run-order.json)
- [All previous results and unsuccessful evidence](BENCHMARK_HISTORY.md)
