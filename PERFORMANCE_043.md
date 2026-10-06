# 0.3.13: fused dense GROUP SUM and AVG

Dense grouping now validates each selected key, counts its rows and updates a shared exact i128 SUM in one pass when the query needs a single SUM/AVG column and no MIN/MAX reduction. Repeated SUM and AVG projections share that state. This avoids filling the intermediate slot vector and revisiting selected rows; its existing reserved capacity remains. Multi-reduction queries, sparse grouping, storage formats, readers, publication, ingestion and source checkpoints are unchanged.

The released 0.3.12 ten-million-row GROUP SUM loss was profiled before editing. Its aggregation stage took about 27 ms of an 83 ms instrumented query. The preserved development trial reduced aggregation from 25.153 to 18.388 ms with similar page-read times. These trial results motivated the change; the final version was separately rebuilt and independently timed below.

Fresh comparisons retain 108 engine/fixture/round cases, 60 query shapes and 5,940 samples. There are 23,030 additional uninstrumented paired samples, including 10M and 100M rows, and 480 instrumented samples excluded from competitive totals. Matrix cases use three rotated orders, three warmups, eleven samples and one thread. Rust samples time ArchiveSnapshot::query; DuckDB samples include Python execute/fetchall. Native storage layouts differ. Builds, setup, checks and scrubs are untimed. Workloads run serially on this shared Windows computer.

DuckDB scores: matched 30 wins / 0 losses; prior stress 15 / 0; key patterns 10 / 0; irregular keys 3 / 2. Every shape and round count is shown below.

The released 0.3.12 matrix measured 56 wins and four losses over these same 60 shapes. The current matrix has two additional wins: 10M-row GROUP SUM and NYC all_zones. Both queries use the changed dense shared-SUM path. Stage profiles and 21 alternating pairs specifically validate the 10M improvement; the NYC win is supported by the three rotated matrix rounds and is retained with that narrower evidence. Older raw measurements remain visible and are not replaced.

## Final alternating controls

Before/after times are medians of pair medians. The paired ratio is the median candidate/baseline ratio within each pair; these summaries can differ under desktop variance. Lower ratios are faster. Most controls use 21 pairs of eleven samples per binary; tiny queries use 21 pairs of 101, and the 100M-row control uses seven pairs of five. Every repeated result matches and every final archive is scrubbed.

| Control | Rows | Query | 0.3.12 ms | 0.3.13 ms | Paired candidate / baseline |
|---|---:|---|---:|---:|---:|
| final-pairs | 10,000,000 | group_sum | 73.7303 | 66.4232 | 0.8978 |
| final-pairs | 10,000,000 | group_full | 93.9971 | 94.1299 | 0.9995 |
| final-pairs | 10,000,000 | filtered_group | 64.9898 | 62.8989 | 0.9652 |
| dense5003-guard-pairs | 1,000,000 | group_sum | 8.0831 | 7.5162 | 0.9299 |
| dense5003-guard-pairs | 1,000,000 | group_full | 10.9348 | 10.9199 | 0.9993 |
| dense5003-guard-pairs | 1,000,000 | filtered_group | 7.1589 | 6.8425 | 0.9519 |
| sparse-guard-pairs | 1,000,000 | group_sum | 8.4928 | 8.5338 | 1.0000 |
| sparse-guard-pairs | 1,000,000 | group_full | 10.5301 | 10.5924 | 1.0032 |
| sparse-guard-pairs | 1,000,000 | filtered_group | 7.0460 | 7.0678 | 1.0109 |
| wide-guard-pairs | 1,000,000 | group_sum | 12.3203 | 12.2612 | 0.9941 |
| wide-guard-pairs | 1,000,000 | group_full | 16.3835 | 15.5339 | 0.9807 |
| wide-guard-pairs | 1,000,000 | filtered_group | 9.8544 | 10.0693 | 0.9993 |
| irregular-guard-pairs | 1,000,000 | group_sum | 20.5219 | 20.6916 | 1.0030 |
| irregular-guard-pairs | 1,000,000 | group_full | 22.8727 | 22.9071 | 0.9998 |
| irregular-guard-pairs | 1,000,000 | filtered_group | 14.1115 | 14.1022 | 0.9951 |
| irregular-guard-pairs | 1,000,000 | unordered_control | 7.7405 | 7.7964 | 1.0002 |
| highcard-guard-pairs | 1,000,000 | group_sum | 40.5718 | 40.8691 | 1.0013 |
| highcard-guard-pairs | 1,000,000 | group_full | 49.5758 | 49.5967 | 1.0012 |
| scan-guard-pairs | 1,000,000 | unordered | 2.9684 | 3.0353 | 1.0199 |
| scan-guard-pairs | 1,000,000 | sparse | 4.7631 | 4.7732 | 0.9983 |
| scan-guard-pairs | 1,000,000 | multi | 4.0005 | 4.0512 | 1.0065 |
| scan-guard-pairs | 1,000,000 | dense_group_guard | 8.9777 | 8.9858 | 1.0084 |
| tiny-guard-pairs | 1,000 | group_sum | 0.1163 | 0.1156 | 0.9983 |
| tiny-guard-pairs | 1,000 | group_full | 0.1267 | 0.1300 | 1.0180 |
| tiny-guard-pairs | 1,000 | filtered_group | 0.1102 | 0.1105 | 1.0074 |
| large-pairs | 100,000,000 | group_sum | 733.9704 | 666.3070 | 0.9069 |
| large-pairs | 100,000,000 | group_full | 939.9810 | 932.0049 | 0.9902 |

## Stage diagnosis, excluded from competitive results

| Rows | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |
|---:|---|---:|---:|---:|
| 10,000,000 | group_sum | 47.212 / 46.252 | 1.688 / 1.691 | 24.709 / 18.218 |
| 10,000,000 | group_full | 46.866 / 46.887 | 1.696 / 1.694 | 44.605 / 44.737 |
| 10,000,000 | filtered_group | 46.819 / 46.637 | 6.378 / 6.919 | 12.718 / 9.332 |
| 100,000,000 | group_sum | 475.083 / 467.199 | 16.677 / 16.158 | 251.516 / 183.131 |

## Matched matrix

| Fixture | Query | 0.3.12 ms | 0.3.13 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 7.095 | 6.388 | 7.541 | 1.097x | ✅; 3/3 rounds |
| dense97 | group_full | 9.228 | 9.079 | 11.166 | 1.028x | ✅; 3/3 rounds |
| dense97 | filtered_group | 6.263 | 6.026 | 7.993 | 1.039x | ✅; 3/3 rounds |
| dense97 | unordered_control | 2.936 | 3.025 | 3.742 | 0.971x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.005 | 0.006 | 1.688 | 0.932x | ✅; 3/3 rounds |
| sparse19 | group_sum | 8.519 | 8.670 | 11.137 | 0.979x | ✅; 3/3 rounds |
| sparse19 | group_full | 10.328 | 10.578 | 15.073 | 0.969x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 7.004 | 6.915 | 10.690 | 0.990x | ✅; 3/3 rounds |
| sparse19 | unordered_control | 2.986 | 2.975 | 3.752 | 0.983x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.005 | 1.701 | 1.038x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 8.201 | 7.609 | 18.617 | 1.073x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 10.890 | 10.949 | 27.449 | 0.995x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 7.225 | 6.871 | 17.263 | 1.048x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 2.942 | 3.037 | 3.808 | 0.969x | ✅; 3/3 rounds |
| cardinality5003 | prefix_control | 0.005 | 0.006 | 1.723 | 0.949x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.004 | 17.471 | 1.205x | ✅; 3/3 rounds |
| nyc | day | 0.005 | 0.005 | 1.661 | 1.122x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.004 | 0.687 | 1.136x | ✅; 3/3 rounds |
| nyc | zone | 1.127 | 1.124 | 1.801 | 1.003x | ✅; 3/3 rounds |
| nyc | all_zones | 24.971 | 23.197 | 25.916 | 1.078x | ✅; 3/3 rounds |
| 10000000 | group_sum | 73.302 | 67.113 | 70.599 | 1.092x | ✅; 3/3 rounds |
| 10000000 | group_full | 94.654 | 95.027 | 105.548 | 0.992x | ✅; 3/3 rounds |
| 10000000 | filtered_group | 65.821 | 63.159 | 75.469 | 1.039x | ✅; 3/3 rounds |
| 10000000 | unordered_control | 31.525 | 32.662 | 36.228 | 0.975x | ✅; 3/3 rounds |
| 10000000 | prefix_control | 0.004 | 0.004 | 8.254 | 1.027x | ✅; 3/3 rounds |
| 100000000 | group_sum | 773.883 | 662.409 | 786.094 | 1.133x | ✅; 3/3 rounds |
| 100000000 | group_full | 948.497 | 937.943 | 1182.450 | 1.010x | ✅; 3/3 rounds |
| 100000000 | filtered_group | 673.826 | 633.760 | 834.655 | 1.063x | ✅; 3/3 rounds |
| 100000000 | unordered_control | 320.908 | 334.286 | 354.803 | 0.981x | ✅; 2/3 rounds |
| 100000000 | prefix_control | 0.008 | 0.008 | 73.128 | 1.000x | ✅; 3/3 rounds |

## Prior stress matrix

| Fixture | Query | 0.3.12 ms | 0.3.13 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 12.440 | 13.950 | 18.619 | 0.888x | ✅; 3/3 rounds |
| wide5003 | group_full | 14.552 | 14.813 | 27.036 | 1.017x | ✅; 3/3 rounds |
| wide5003 | filtered_group | 9.772 | 9.849 | 16.892 | 0.992x | ✅; 3/3 rounds |
| wide5003 | unordered_control | 2.922 | 2.967 | 3.833 | 0.985x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.006 | 0.006 | 1.690 | 1.036x | ✅; 3/3 rounds |
| collision19 | group_sum | 8.634 | 8.466 | 11.133 | 0.999x | ✅; 3/3 rounds |
| collision19 | group_full | 10.533 | 10.617 | 15.010 | 0.992x | ✅; 3/3 rounds |
| collision19 | filtered_group | 7.288 | 6.900 | 10.444 | 1.056x | ✅; 3/3 rounds |
| collision19 | unordered_control | 2.927 | 2.962 | 3.788 | 0.979x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.005 | 0.006 | 1.708 | 1.000x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 40.655 | 40.780 | 90.036 | 0.994x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 49.342 | 50.504 | 130.511 | 0.972x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 34.434 | 35.391 | 92.458 | 0.977x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 2.883 | 2.997 | 3.757 | 0.970x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.005 | 0.006 | 1.680 | 0.947x | ✅; 3/3 rounds |

## Prior key-pattern matrix

| Fixture | Query | 0.3.12 ms | 0.3.13 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| fibonacci19 | group_sum | 8.482 | 8.663 | 11.012 | 0.979x | ✅; 3/3 rounds |
| fibonacci19 | group_full | 10.487 | 10.430 | 14.783 | 1.024x | ✅; 3/3 rounds |
| fibonacci19 | filtered_group | 7.062 | 7.050 | 10.441 | 1.004x | ✅; 3/3 rounds |
| fibonacci19 | unordered_control | 3.049 | 2.933 | 3.728 | 1.005x | ✅; 3/3 rounds |
| fibonacci19 | prefix_control | 0.006 | 0.005 | 1.672 | 1.055x | ✅; 3/3 rounds |
| power19 | group_sum | 8.454 | 8.533 | 11.092 | 0.981x | ✅; 3/3 rounds |
| power19 | group_full | 10.515 | 10.706 | 14.980 | 0.990x | ✅; 3/3 rounds |
| power19 | filtered_group | 7.004 | 7.157 | 10.534 | 0.984x | ✅; 3/3 rounds |
| power19 | unordered_control | 2.910 | 2.963 | 3.799 | 0.970x | ✅; 3/3 rounds |
| power19 | prefix_control | 0.006 | 0.006 | 1.707 | 1.035x | ✅; 3/3 rounds |

## Irregular signed-key matrix

| Fixture | Query | 0.3.12 ms | 0.3.13 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| irregular5003 | group_sum | 20.511 | 20.602 | 17.169 | 1.004x | ❌; 0/3 rounds |
| irregular5003 | group_full | 23.037 | 22.846 | 25.600 | 0.999x | ✅; 3/3 rounds |
| irregular5003 | filtered_group | 13.976 | 14.061 | 15.650 | 0.983x | ✅; 3/3 rounds |
| irregular5003 | unordered_control | 5.969 | 5.792 | 3.810 | 1.034x | ❌; 0/3 rounds |
| irregular5003 | prefix_control | 0.006 | 0.005 | 1.688 | 1.075x | ✅; 3/3 rounds |

## Correctness, durability and limits

All 73 Rust tests pass in debug and release, formatting and both Clippy configurations. A new independent BTreeMap oracle verifies shared SUM/AVG, exact filtered counts, empty selections, 4,097 rows, signed boundary domains and beyond-i64 outputs. Metadata-bound failures are checked on both the fused and preceding reduction paths. Source hashes prove that only Cargo versions and dense reduction code/tests differ from preserved 0.3.12; sparse helpers, storage, readers, writers, source contract and SQL parsing are unchanged.

The frozen final binaries match 3,400 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping, 600 sparse key patterns, 600 medium groups, 600 focused dense/shared-SUM cases and 600 scans. Two independent 411-row/137-group signed-boundary fixtures verify exact beyond-i64 integer JSON, shared AVG, repeated SUM, confirmed retry and reopen through the actual dense bridge plan. Existing sparse and medium wide-JSON checks remain. All current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet workflow with 42 SQL checks. Injected faults and process kills do not qualify physical power loss.

The optimization adds no per-query allocation. The previous reserved intermediate capacity remains, and mixed-reduction queries continue using the preceding path. Broad timing shifts on unchanged sparse/scan/mixed paths cannot be attributed to this change. Every loss, guard and development trial remains visible. Only DuckDB is freshly competed; the last multi-server network comparison remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Network requests/s, cold I/O, distributed scale and production readiness remain unqualified.

## Reproduce and inspect

Run checks_043.py, build_source_adapter_043.py, time_043.py, run_043.py, report_043.py, docs_043.py and package_043.py serially with the pinned local Python dependencies. Completed outputs and release archives are immutable. Controls reuse retained fixtures; matrix scripts can seed independently. Never overlap compilation, tests or packaging with timed database work. Release 0.3.13 uses experiment identifier 043.

- [Complete gates and scores](benchmarks/dense-043-audit.json)
- [10M-row final pairs](benchmarks/dense-043-final-pairs.json)
- [100M-row final pairs](benchmarks/dense-043-large-pairs.json)
- [10M-row final profiles](benchmarks/dense-043-final-profiles.json)
- [100M-row final profiles](benchmarks/dense-043-large-profiles.json)
- [Dense 5,003-key guard](benchmarks/dense-043-dense5003-guard-pairs.json)
- [Sparse guard](benchmarks/dense-043-sparse-guard-pairs.json)
- [Wide sparse guard](benchmarks/dense-043-wide-guard-pairs.json)
- [Irregular signed-key guard](benchmarks/dense-043-irregular-guard-pairs.json)
- [High-cardinality guard](benchmarks/dense-043-highcard-guard-pairs.json)
- [Scan guard](benchmarks/dense-043-scan-guard-pairs.json)
- [Tiny-query guard](benchmarks/dense-043-tiny-guard-pairs.json)
- [Shared-SUM SQL and signed wide JSON qualification](benchmarks/dense-043-differential.json)
- [Released baseline profiles](benchmarks/dense-043-baseline-profiles.json)
- [Preserved development trial source and build](benchmarks/trial-043-fused-shared-sum/proof.json)
- [Trial 10M pairs](benchmarks/dense-043-trial-10m-pairs.json)
- [Trial stage profiles](benchmarks/dense-043-trial-10m-profiles.json)
- [Trial dense guard](benchmarks/dense-043-trial-dense5003-pairs.json)
- [Trial sparse guard](benchmarks/dense-043-trial-sparse-pairs.json)
- [Build provenance](benchmarks/rust-checks-043.json)
- [Timed work order](benchmarks/dense-043-run-order.json)
- [Qualification work order](benchmarks/correctness-043-run-order.json)
- [All previous results and unsuccessful evidence](BENCHMARK_HISTORY.md)
