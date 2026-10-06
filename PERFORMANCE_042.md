# 0.3.12: reuse-triggered sparse GROUP BY acceleration

A wider tagged lookup cache accelerates repeatedly used sparse keys after the small cache has been abandoned. Promotion requires at least 50% repeated keys in a selected block of at least 64 rows, at most 8,192 distinct keys, and another nonempty block. The optional 16,384-slot table occupies 384 KiB on this 64-bit computer. Queries get one promotion attempt; key growth or poor hit rate releases it. Every hit checks the exact signed key. The existing randomized HashMap remains authoritative, and exact i128 typed reductions are unchanged.

The released 0.3.11 wide5003 loss was concentrated in hash mapping: initial stage profiles put roughly 16.3 ms of a 22.2 ms GROUP SUM query in aggregation. The first larger-cache trial improved this fixture but allocated its table after the final block of a tiny query. That trial regressed the 1,000-row/129-key guard by 75–79%. Its source, binary and complete timings remain preserved. The selected implementation defers allocation until another block actually needs it. Separate trial measurements recovered the tiny-query guard, and the final version is independently rebuilt and remeasured below.

Fresh comparisons retain 108 engine/fixture/round cases, 60 shapes and 5,940 samples. The previous 55 shapes are retained; five added shapes use 5,003 irregular signed i64 keys, including both extremes, on one million rows. There are 20,118 additional uninstrumented paired samples, including a tiny-query guard, and 1,078 instrumented samples excluded from competitive totals. Matrix cases use three rotated orders, three warmups, eleven samples and one thread. Rust samples time ArchiveSnapshot::query; DuckDB samples include Python execute/fetchall. Storage layouts differ. Builds, setup, result assertions and scrubs are untimed; all workloads run serially on this shared Windows computer.

DuckDB scores: matched 28 wins / 2 losses; prior stress 15 / 0; key patterns 10 / 0; irregular keys 3 / 2. Every per-shape win/loss and round count is retained below.

## Final alternating controls

Before/after medians are pooled across pair medians; the paired ratio is the median of candidate/baseline within each pair. These two summaries can differ during shared-desktop variance. Lower ratios are faster. All outputs match exactly.

| Control | Query | 0.3.11 ms | 0.3.12 ms | Paired candidate / baseline |
|---|---|---:|---:|---:|
| final-pairs | group_sum | 27.7043 | 16.8338 | 0.6160 |
| final-pairs | group_full | 27.1084 | 17.2127 | 0.6269 |
| final-pairs | filtered_group | 15.2225 | 10.4654 | 0.6815 |
| highcard-guard-pairs | group_sum | 48.9108 | 50.6347 | 0.9862 |
| highcard-guard-pairs | group_full | 50.6807 | 52.0838 | 1.0061 |
| sparse-guard-pairs | group_sum | 9.9195 | 9.1157 | 0.9620 |
| sparse-guard-pairs | group_full | 11.7674 | 11.4572 | 0.9819 |
| sparse-guard-pairs | filtered_group | 9.4965 | 9.4765 | 0.9979 |
| scan-guard-pairs | unordered | 3.6727 | 3.6468 | 0.9969 |
| scan-guard-pairs | sparse | 5.5940 | 5.4307 | 0.9708 |
| scan-guard-pairs | multi | 4.0575 | 4.0157 | 0.9986 |
| scan-guard-pairs | dense_group_guard | 9.3485 | 9.2757 | 0.9939 |
| tiny-guard-pairs | group_sum | 0.1174 | 0.1162 | 0.9947 |
| tiny-guard-pairs | group_full | 0.1268 | 0.1298 | 1.0161 |
| tiny-guard-pairs | filtered_group | 0.1114 | 0.1109 | 0.9964 |
| irregular-pairs | group_sum | 51.4460 | 37.2159 | 0.8036 |
| irregular-pairs | group_full | 50.0567 | 39.0661 | 0.8123 |
| irregular-pairs | filtered_group | 24.7674 | 21.0367 | 0.8530 |
| irregular-pairs | unordered_control | 10.9134 | 10.7006 | 0.9922 |

## Stage diagnosis, excluded from competitive results

| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |
|---|---|---:|---:|---:|
| wide5003 | group_sum | 5.555 / 5.407 | 0.186 / 0.185 | 18.099 / 7.891 |
| wide5003 | group_full | 6.138 / 6.707 | 0.208 / 0.232 | 22.467 / 13.674 |
| wide5003 | filtered_group | 7.839 / 7.824 | 0.978 / 0.966 | 14.007 / 6.281 |
| irregular5003 | group_sum | 7.918 / 8.214 | 0.226 / 0.228 | 20.277 / 16.913 |
| irregular5003 | group_full | 7.049 / 7.072 | 0.209 / 0.203 | 21.677 / 17.341 |
| irregular5003 | filtered_group | 6.225 / 6.320 | 0.676 / 0.646 | 9.220 / 6.046 |
| irregular5003 | unordered_control | 5.351 / 5.278 | 0.845 / 0.861 | 0.275 / 0.277 |

The irregular-key rotated matrix showed GROUP SUM slower than baseline, alongside an untouched scan slowdown. Follow-up alternating pairs on the same archive measured grouping 15–20% faster than baseline and the scan within about 1%. Stage profiles show reduced aggregation cost with similar page-read times. These follow-ups support a grouping improvement while retaining the original rotated results and its two DuckDB losses; they do not replace them.


## Matched matrix

| Fixture | Query | 0.3.11 ms | 0.3.12 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 7.518 | 7.331 | 7.605 | 1.023x | ✅; 2/3 rounds |
| dense97 | group_full | 9.365 | 9.352 | 11.648 | 1.007x | ✅; 3/3 rounds |
| dense97 | filtered_group | 6.393 | 6.314 | 8.282 | 1.013x | ✅; 3/3 rounds |
| dense97 | unordered_control | 3.159 | 3.126 | 3.822 | 1.000x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.006 | 0.006 | 1.711 | 1.000x | ✅; 3/3 rounds |
| sparse19 | group_sum | 9.071 | 9.154 | 11.382 | 0.991x | ✅; 3/3 rounds |
| sparse19 | group_full | 11.434 | 10.957 | 15.109 | 1.059x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 7.359 | 7.319 | 10.757 | 1.014x | ✅; 3/3 rounds |
| sparse19 | unordered_control | 3.058 | 3.093 | 3.920 | 1.011x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.006 | 1.712 | 0.983x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 8.449 | 8.575 | 19.026 | 0.993x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 11.396 | 11.349 | 27.552 | 1.001x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 7.574 | 7.521 | 17.532 | 1.010x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 3.145 | 3.145 | 3.960 | 1.000x | ✅; 3/3 rounds |
| cardinality5003 | prefix_control | 0.006 | 0.006 | 1.750 | 0.949x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.005 | 17.729 | 1.060x | ✅; 3/3 rounds |
| nyc | day | 0.006 | 0.005 | 1.685 | 1.056x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.005 | 0.718 | 1.064x | ✅; 3/3 rounds |
| nyc | zone | 1.127 | 1.173 | 1.808 | 0.964x | ✅; 3/3 rounds |
| nyc | all_zones | 26.588 | 26.234 | 26.070 | 1.013x | ❌; 0/3 rounds |
| 10000000 | group_sum | 75.845 | 75.462 | 71.571 | 1.005x | ❌; 0/3 rounds |
| 10000000 | group_full | 96.306 | 95.861 | 106.950 | 1.005x | ✅; 3/3 rounds |
| 10000000 | filtered_group | 68.102 | 67.605 | 75.871 | 1.015x | ✅; 3/3 rounds |
| 10000000 | unordered_control | 32.893 | 33.330 | 36.343 | 0.989x | ✅; 3/3 rounds |
| 10000000 | prefix_control | 0.004 | 0.004 | 8.391 | 1.027x | ✅; 3/3 rounds |
| 100000000 | group_sum | 1238.966 | 817.370 | 981.388 | 1.147x | ✅; 2/3 rounds |
| 100000000 | group_full | 1492.472 | 1076.457 | 1523.810 | 1.386x | ✅; 3/3 rounds |
| 100000000 | filtered_group | 922.685 | 831.738 | 1048.459 | 1.332x | ✅; 3/3 rounds |
| 100000000 | unordered_control | 557.347 | 379.974 | 428.632 | 1.150x | ✅; 2/3 rounds |
| 100000000 | prefix_control | 0.008 | 0.007 | 78.550 | 1.052x | ✅; 3/3 rounds |

## Prior stress matrix

| Fixture | Query | 0.3.11 ms | 0.3.12 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 24.744 | 19.015 | 20.319 | 1.525x | ✅; 2/3 rounds |
| wide5003 | group_full | 30.639 | 20.381 | 32.471 | 1.576x | ✅; 3/3 rounds |
| wide5003 | filtered_group | 18.786 | 11.746 | 19.560 | 1.517x | ✅; 3/3 rounds |
| wide5003 | unordered_control | 3.929 | 3.807 | 4.566 | 1.006x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.007 | 0.006 | 2.419 | 1.111x | ✅; 3/3 rounds |
| collision19 | group_sum | 10.787 | 10.663 | 12.846 | 1.011x | ✅; 2/3 rounds |
| collision19 | group_full | 13.088 | 12.262 | 16.948 | 1.064x | ✅; 3/3 rounds |
| collision19 | filtered_group | 9.806 | 9.029 | 12.374 | 1.086x | ✅; 3/3 rounds |
| collision19 | unordered_control | 4.439 | 3.750 | 4.372 | 1.160x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.008 | 0.007 | 1.891 | 1.100x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 46.664 | 62.741 | 98.859 | 0.743x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 65.787 | 58.999 | 155.900 | 1.115x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 42.718 | 42.331 | 110.264 | 1.009x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 3.320 | 3.501 | 4.076 | 0.994x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.006 | 0.006 | 1.819 | 0.953x | ✅; 3/3 rounds |

## Prior key-pattern matrix

| Fixture | Query | 0.3.11 ms | 0.3.12 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| fibonacci19 | group_sum | 9.628 | 9.376 | 11.590 | 1.073x | ✅; 3/3 rounds |
| fibonacci19 | group_full | 11.576 | 11.909 | 15.314 | 0.972x | ✅; 3/3 rounds |
| fibonacci19 | filtered_group | 7.914 | 7.724 | 10.952 | 1.025x | ✅; 3/3 rounds |
| fibonacci19 | unordered_control | 3.176 | 3.148 | 4.274 | 1.030x | ✅; 3/3 rounds |
| fibonacci19 | prefix_control | 0.006 | 0.006 | 1.872 | 0.966x | ✅; 3/3 rounds |
| power19 | group_sum | 9.435 | 9.339 | 11.554 | 0.998x | ✅; 3/3 rounds |
| power19 | group_full | 11.360 | 11.186 | 15.338 | 1.030x | ✅; 3/3 rounds |
| power19 | filtered_group | 7.584 | 7.412 | 11.016 | 1.023x | ✅; 3/3 rounds |
| power19 | unordered_control | 3.172 | 3.086 | 3.923 | 1.002x | ✅; 3/3 rounds |
| power19 | prefix_control | 0.006 | 0.006 | 1.695 | 1.036x | ✅; 3/3 rounds |

## Irregular signed-key matrix

| Fixture | Query | 0.3.11 ms | 0.3.12 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| irregular5003 | group_sum | 26.249 | 30.437 | 21.379 | 1.006x | ❌; 0/3 rounds |
| irregular5003 | group_full | 29.221 | 33.052 | 33.776 | 0.884x | ✅; 2/3 rounds |
| irregular5003 | filtered_group | 19.305 | 18.530 | 20.018 | 1.175x | ✅; 3/3 rounds |
| irregular5003 | unordered_control | 6.713 | 8.169 | 4.823 | 1.040x | ❌; 0/3 rounds |
| irregular5003 | prefix_control | 0.006 | 0.007 | 2.091 | 1.000x | ✅; 3/3 rounds |

## Correctness, durability and limits

All 72 Rust tests pass in debug/release, formatting and both Clippy configurations. New tests cover deferred promotion, real seed-specific collisions, release after 8,193 keys, signed extremes, exact beyond-i64 sums and all typed grouped reductions against an independent BTreeMap. Unchanged readers, publication, dense grouping, live ingestion, source and SQL code are checked byte-for-byte against the preserved release; only Cargo versions and the sparse helper/tests change.

The final binaries match 2,800 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping, 600 key patterns, 600 medium/irregular/late-growth/high-cardinality and 600 scans. Medium signed groups also emit exact beyond-i64 integer JSON through the actual bridge after confirmed retry and reopen. Current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet workflow with 42 SQL checks. Process/injected I/O tests do not qualify physical power loss.

Promotion trades an optional 384 KiB allocation for less repeated hash work. The hit-rate gate, key budget and one-attempt policy bound the cache, but random seeds and constructed collisions still vary latency. All guard results, unsuccessful trial evidence and broad matrix shifts are visible. Changes on untouched dense/scan/prefix paths are measurements, without attribution to this cache. Only DuckDB is freshly competed; the last multi-server network comparison remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Network capacity, cold I/O, distributed scale and production readiness are unqualified.

The irregular-fixture harness initially created a directory before Engine.__init__ created it again. This stopped setup before any database query. A subsequent seed request exceeded the retained test bridge request limits; seeding now uses 10,000-row batches, and wide JSON tests use three 5,003-row batches. Both failures, source snapshots, logs and run-order entries are preserved. The repaired runner resumed only unfinished scopes; all five completed matrices remained unchanged.

## Reproduce and inspect

Run checks_042.py, build_source_adapter_042.py, time_042.py, follow_up_042.py, run_042.py, report_042.py, docs_042.py and package_042.py serially with the pinned local Python dependencies. Completed outputs and archives must remain immutable. Controls reuse retained fixtures; matrix scripts can seed fixtures independently. Never overlap compilation, testing or packaging with timed database work. Release 0.3.12 uses experiment identifier 042.

- [Complete gates and scores](benchmarks/cache-042-audit.json)
- [Final wide-key pairs](benchmarks/cache-042-final-pairs.json)
- [Tiny-query guard](benchmarks/cache-042-tiny-guard-pairs.json)
- [High-cardinality guard](benchmarks/cache-042-highcard-guard-pairs.json)
- [Small sparse guards](benchmarks/cache-042-sparse-guard-pairs.json)
- [Scan and dense guards](benchmarks/cache-042-scan-guard-pairs.json)
- [Final stage profiles](benchmarks/cache-042-final-profiles.json)
- [Original released-binary profiles](benchmarks/cache-042-baseline-wide-profiles.json)
- [Rejected eager trial](benchmarks/trial-042-reuse-gated-large/proof.json)
- [Rejected tiny-query regression](benchmarks/cache-042-trial-eager-tiny-pairs.json)
- [Deferred trial source and build](benchmarks/trial-042-deferred-large/proof.json)
- [Deferred trial wide-key pairs](benchmarks/cache-042-deferred-wide-pairs.json)
- [Deferred trial tiny guard](benchmarks/cache-042-deferred-tiny-pairs.json)
- [Irregular signed-key raw matrix](benchmarks/group-042-irregular-comparison.json)
- [Irregular-key alternating pairs](benchmarks/cache-042-irregular-pairs.json)
- [Irregular-key stage profiles](benchmarks/cache-042-irregular-profiles.json)
- [Follow-up timing order](benchmarks/cache-042-follow-up-run-order.json)
- [Medium-cardinality SQL oracles](benchmarks/medium-042-differential.json)
- [Build provenance](benchmarks/rust-checks-042.json)
- [Timed work order](benchmarks/cache-042-run-order.json)
- [Qualification order](benchmarks/correctness-042-run-order.json)
- [Preserved benchmark setup failure and repair](benchmarks/cache-042-setup-repair.json)
- [Preserved seed request limit failure and repair](benchmarks/cache-042-batch-repair.json)
- [Previous results](BENCHMARK_HISTORY.md)
