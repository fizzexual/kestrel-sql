# 0.3.11: seeded sparse-group cache indexing

The 256-slot tagged GROUP BY cache now indexes the upper bits of a wrapping multiplication with an odd multiplier derived once per query from the existing randomized HashMap state. This spreads low-bit-aligned keys across slots. Every hit still checks the exact signed key; misses use the unchanged authoritative randomized HashMap. The 128-key limit, low-hit-rate fallback, typed i128 reductions, result limit, dense grouping, storage and writer policy remain intact.

The historical collision19 keys occupied only two old cache slots. Initial instrumented profiles placed most cost in aggregation. A fixed golden-ratio multiplier can itself collapse a Fibonacci-spaced key pattern, so the candidate uses a per-query seed. Unit tests deliberately invert the actual odd multiplier to generate real collisions, then verify exact counts/sums, fallback and cache release. This cache is not a cryptographic hash or a promise of collision-free execution. [Rust documents randomized HashMap state](https://doc.rust-lang.org/std/collections/hash_map/struct.RandomState.html) and [hash_one](https://doc.rust-lang.org/std/hash/trait.BuildHasher.html#method.hash_one); these are established techniques, without a novelty claim.

Fresh comparisons retain 99 sequential engine/fixture/round cases, 55 shapes and 5,445 query samples, plus 4,620 uninstrumented paired controls. The matched and prior stress shapes remain comparable with 0.3.10; ten added shapes exercise Fibonacci spacing and power-of-two spacing. Three rotated orders, three warmups and eleven samples are used for every matrix shape. All queries use one thread and warm caches on this shared Windows computer. Rust samples time ArchiveSnapshot::query; DuckDB samples include Python execute/fetchall with native compression and a 256 MB buffer limit. Build/setup, assertions and scrubs are untimed. Instrumented samples are excluded from competitive totals.

Matched score: 28 wins / 2 losses against DuckDB; prior extra shapes: 14 / 1; new key patterns: 10 / 0. These describe this run; every loss and round count follows.

## Final collision19 pairs against 0.3.10

Twenty-one alternating same-archive pairs, eleven samples per variant per pair. Each process closes before the next opens. Ratios above 1 mean slower. A ratio of paired medians can differ from the ratio of the displayed times. Raw samples retain variation from changing cache seeds and the shared desktop; actual seed values are not exposed or fixed by the harness.

| Query | 0.3.10 ms | 0.3.11 ms | Paired final/baseline |
|---|---:|---:|---:|
| group_sum | 18.115 | 8.972 | 0.4943 |
| group_full | 20.500 | 11.169 | 0.5383 |
| filtered_group | 12.838 | 7.969 | 0.6134 |

## Ordinary sparse19 guard pairs

Twenty-one alternating same-archive pairs, eleven samples per variant per pair. Each process closes before the next opens. Ratios above 1 mean slower. A ratio of paired medians can differ from the ratio of the displayed times. Raw samples retain variation from changing cache seeds and the shared desktop; actual seed values are not exposed or fixed by the harness.

| Query | 0.3.10 ms | 0.3.11 ms | Paired final/baseline |
|---|---:|---:|---:|
| group_sum | 11.527 | 11.112 | 1.0189 |
| group_full | 14.652 | 15.117 | 1.0311 |
| filtered_group | 8.142 | 8.407 | 1.0378 |

## Unchanged scan and dense-group guards

Twenty-one alternating same-archive pairs, eleven samples per variant per pair. Each process closes before the next opens. Ratios above 1 mean slower. A ratio of paired medians can differ from the ratio of the displayed times. Raw samples retain variation from changing cache seeds and the shared desktop; actual seed values are not exposed or fixed by the harness.

| Query | 0.3.10 ms | 0.3.11 ms | Paired final/baseline |
|---|---:|---:|---:|
| unordered | 2.984 | 2.995 | 0.9893 |
| sparse | 4.763 | 4.767 | 0.9954 |
| multi | 4.048 | 4.067 | 1.0100 |
| dense_group_guard | 9.135 | 9.159 | 1.0008 |

## Instrumented collision19 stages

Seven alternating profiled pairs; excluded from competitive totals.

| Query | Read before/after ms | Select before/after ms | Aggregate before/after ms |
|---|---:|---:|---:|
| group_sum | 4.586 / 4.500 | 0.168 / 0.168 | 13.352 / 4.249 |
| group_full | 4.750 / 4.437 | 0.169 / 0.169 | 15.518 / 6.228 |
| filtered_group | 4.539 / 4.385 | 0.631 / 0.635 | 6.604 / 2.161 |

## Matched matrix

| Fixture | Query | 0.3.10 ms | 0.3.11 ms | DuckDB ms | Paired before/after | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 7.105 | 7.214 | 7.567 | 0.980x | ✅; 3/3 rounds |
| dense97 | group_full | 9.046 | 9.251 | 11.382 | 0.978x | ✅; 3/3 rounds |
| dense97 | filtered_group | 6.301 | 6.476 | 8.133 | 0.973x | ✅; 3/3 rounds |
| dense97 | unordered_control | 3.052 | 3.098 | 3.861 | 0.985x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.006 | 0.006 | 1.701 | 0.984x | ✅; 3/3 rounds |
| sparse19 | group_sum | 9.312 | 10.238 | 11.467 | 0.950x | ✅; 3/3 rounds |
| sparse19 | group_full | 11.997 | 12.085 | 14.943 | 1.007x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 9.214 | 7.386 | 10.627 | 1.120x | ✅; 3/3 rounds |
| sparse19 | unordered_control | 3.389 | 3.089 | 3.813 | 1.097x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.006 | 1.698 | 1.034x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 8.346 | 9.481 | 19.738 | 0.880x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 11.150 | 12.532 | 28.263 | 0.974x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 7.304 | 8.158 | 17.486 | 0.983x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 3.019 | 3.282 | 3.822 | 0.986x | ✅; 3/3 rounds |
| cardinality5003 | prefix_control | 0.006 | 0.006 | 1.742 | 1.050x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.005 | 17.670 | 1.156x | ✅; 3/3 rounds |
| nyc | day | 0.006 | 0.005 | 1.646 | 1.118x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.004 | 0.704 | 1.091x | ✅; 3/3 rounds |
| nyc | zone | 1.152 | 1.106 | 1.773 | 1.042x | ✅; 3/3 rounds |
| nyc | all_zones | 25.703 | 25.926 | 25.854 | 0.979x | ❌; 1/3 rounds |
| 10000000 | group_sum | 74.453 | 74.723 | 70.574 | 0.999x | ❌; 0/3 rounds |
| 10000000 | group_full | 96.755 | 94.840 | 105.802 | 1.000x | ✅; 2/3 rounds |
| 10000000 | filtered_group | 67.281 | 66.096 | 75.452 | 1.003x | ✅; 3/3 rounds |
| 10000000 | unordered_control | 32.369 | 32.387 | 36.209 | 0.999x | ✅; 3/3 rounds |
| 10000000 | prefix_control | 0.004 | 0.004 | 8.320 | 1.027x | ✅; 3/3 rounds |
| 100000000 | group_sum | 743.389 | 745.435 | 801.431 | 0.991x | ✅; 3/3 rounds |
| 100000000 | group_full | 947.378 | 967.814 | 1134.955 | 0.979x | ✅; 3/3 rounds |
| 100000000 | filtered_group | 659.916 | 667.124 | 841.214 | 0.989x | ✅; 3/3 rounds |
| 100000000 | unordered_control | 325.012 | 323.446 | 365.299 | 1.007x | ✅; 3/3 rounds |
| 100000000 | prefix_control | 0.007 | 0.008 | 74.248 | 1.000x | ✅; 3/3 rounds |

## Prior additional stress matrix

| Fixture | Query | 0.3.10 ms | 0.3.11 ms | DuckDB ms | Paired before/after | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 21.572 | 21.861 | 18.440 | 0.990x | ❌; 0/3 rounds |
| wide5003 | group_full | 24.118 | 24.414 | 27.432 | 0.984x | ✅; 3/3 rounds |
| wide5003 | filtered_group | 15.005 | 14.786 | 17.233 | 1.006x | ✅; 3/3 rounds |
| wide5003 | unordered_control | 2.987 | 3.001 | 3.776 | 1.009x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.006 | 0.006 | 1.670 | 1.017x | ✅; 3/3 rounds |
| collision19 | group_sum | 18.346 | 8.829 | 11.144 | 2.078x | ✅; 3/3 rounds |
| collision19 | group_full | 19.751 | 10.878 | 14.915 | 1.829x | ✅; 3/3 rounds |
| collision19 | filtered_group | 11.951 | 7.218 | 10.591 | 1.656x | ✅; 3/3 rounds |
| collision19 | unordered_control | 3.072 | 2.990 | 3.733 | 1.025x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.006 | 0.006 | 1.668 | 1.033x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 41.183 | 41.269 | 91.301 | 0.987x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 51.451 | 50.889 | 131.199 | 1.011x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 35.435 | 35.350 | 93.370 | 0.999x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 2.952 | 2.934 | 3.815 | 0.980x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.006 | 0.005 | 1.718 | 1.035x | ✅; 3/3 rounds |

## New key-pattern matrix

| Fixture | Query | 0.3.10 ms | 0.3.11 ms | DuckDB ms | Paired before/after | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| fibonacci19 | group_sum | 8.751 | 8.934 | 11.371 | 0.984x | ✅; 3/3 rounds |
| fibonacci19 | group_full | 10.947 | 10.948 | 14.932 | 1.000x | ✅; 3/3 rounds |
| fibonacci19 | filtered_group | 7.114 | 7.166 | 10.503 | 0.993x | ✅; 3/3 rounds |
| fibonacci19 | unordered_control | 2.916 | 3.098 | 3.795 | 0.979x | ✅; 3/3 rounds |
| fibonacci19 | prefix_control | 0.006 | 0.006 | 1.693 | 1.000x | ✅; 3/3 rounds |
| power19 | group_sum | 18.034 | 9.164 | 11.349 | 1.963x | ✅; 3/3 rounds |
| power19 | group_full | 20.433 | 11.256 | 14.770 | 1.815x | ✅; 3/3 rounds |
| power19 | filtered_group | 12.016 | 7.208 | 10.523 | 1.645x | ✅; 3/3 rounds |
| power19 | unordered_control | 2.991 | 3.004 | 3.844 | 0.996x | ✅; 3/3 rounds |
| power19 | prefix_control | 0.006 | 0.006 | 1.710 | 1.000x | ✅; 3/3 rounds |

## Correctness and remaining scope

All 70 Rust tests pass in debug/release, formatting and both Clippy configurations. Collision tests construct real collisions for each actual seed rather than relying on the previous hash formula. The final CLI/bridge match 2,200 SQL cases against each DuckDB and SQLite: 500 general archive, 500 expanded/signed-sparse grouping, 600 scans and 600 new low-bit/Fibonacci/signed-power/over-cache-limit cases. Reopen, confirmed retry, CRC scrubs and exact signed i128 JSON pass.

The initial report audit rejected four equal adjacent Windows timestamps after all nine qualification suites passed. Blocking subprocess execution was already serial. The repaired no-overlap check accepts equal boundary timestamps; the original harness, diagnostic and raw timestamps remain visible.

Current binaries pass 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet workflow with 42 DuckDB SQL checks. Process/injected I/O checks do not qualify physical power loss.

Randomly chosen cache multipliers can still collide, including deliberately constructed keys; fallback bounds cache memory and preserves correctness, without guaranteeing the fastest latency. Broad matrix shifts on unchanged dense/scan/prefix paths are retained as measurements, not attributed to this cache change. Only DuckDB was freshly competed. The last six-engine network matrix is [0.3.1](PERFORMANCE_031.md); its mixed-write losses remain. No new network capacity, cold-I/O, distributed-scale or production qualification is established.

## Reproduce and inspect

Run serially with pinned local Python dependencies: checks_041.py, build_source_adapter_041.py, time_041.py, run_041.py, report_041.py, docs_041.py and package_041.py. Never overlap timed database work with compilation, tests or packaging. Matrix helpers reuse retained fixtures or generate fresh small/key-pattern fixtures; controls require retained local datasets and refuse completed-output replacement. Release 0.3.11 uses internal experiment identifier 041.

- [Complete gates and scores](benchmarks/cache-041-audit.json)
- [Final collision pairs](benchmarks/cache-041-final-pairs.json)
- [Sparse guards](benchmarks/cache-041-sparse-guard-pairs.json)
- [Scan/dense guards](benchmarks/cache-041-scan-guard-pairs.json)
- [Final stage profiles](benchmarks/cache-041-final-profiles.json)
- [Initial unchanged-binary stage diagnosis](benchmarks/cache-041-baseline-profiles.json)
- [Preserved trial source/build](benchmarks/trial-041-seeded-multiply/proof.json)
- [Trial pairs](benchmarks/cache-041-trial-pairs.json)
- [Trial stage profiles](benchmarks/cache-041-trial-profiles.json)
- [Trial guards](benchmarks/cache-041-trial-guard-pairs.json)
- [Matched 1M shapes](benchmarks/group-041-typed-comparison.json)
- [NYC shapes](benchmarks/group-041-nyc-comparison.json)
- [10M/100M shapes](benchmarks/group-041-large-comparison.json)
- [Prior extra stress shapes](benchmarks/group-041-extended-comparison.json)
- [New key patterns](benchmarks/group-041-patterns-comparison.json)
- [New SQL oracles](benchmarks/cache-041-differential.json)
- [Build provenance](benchmarks/rust-checks-041.json)
- [Timed work order](benchmarks/cache-041-run-order.json)
- [Correctness/recovery order](benchmarks/correctness-041-run-order.json)
- [Preserved report-clock gate failure and repair](benchmarks/report-041-repair.json)
- [Original failing report harness](benchmarks/report-041-before-clock-repair.py)
- [Previous results](BENCHMARK_HISTORY.md)
