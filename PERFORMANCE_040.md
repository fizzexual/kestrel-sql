# 0.3.10: direct first-filter selection

Streaming scans now generate row positions directly from the first predicate not already enforced by sorted bounds. Later predicates retain those positions. This removes a full range fill and avoids indirect value reads on the first comparison. All six integer operators, signed values, filter order, partial blocks and independently sorted overlapping segments keep their SQL meaning. Group states, prefix queries, readers, storage/publication formats, live/source contracts and default policy are unchanged.

The 0.3.9 unordered-scan regression motivated stage profiling. The separate-function `inline(never)` trial produced no reliable gain and is retained. The direct-selection trial reduced the selection stage; final binaries were rebuilt and measured again. [Rust documents inline attributes as compiler hints](https://doc.rust-lang.org/reference/attributes/codegen.html#the-inline-attribute); outlining and operator fusion are established techniques, with no novelty claim.

Fresh comparisons retain 81 sequential engine/fixture/round cases, 45 shapes and 4,455 samples, plus 2,842 uninstrumented paired control samples. Three rotated engine orders, three warmups and eleven samples are used for every matrix shape. All queries use one thread and warm caches on this shared Windows computer. Rust samples cover ArchiveSnapshot::query, excluding framing/assertions; DuckDB samples include Python execute/fetchall, use native compression and a 256 MB buffer limit. Full scrubs and setup are untimed. Stage timings are instrumented and excluded from competitive totals.

The matched matrix has 29 median DuckDB wins and 1 loss; the extra stress matrix has 11 wins and 4 losses. Every round count and loss is retained below. These scores describe this run, not universal performance.

## Final 1M-row pairs against 0.3.9

Alternating same-archive pairs; each engine opens and closes sequentially. A final/baseline ratio above 1 means slower. Paired ratios and ratios of displayed median times can differ.

| Query | Baseline ms | 0.3.10 ms | Paired final/baseline |
|---|---:|---:|---:|
| unordered | 3.154 | 2.893 | 0.9139 |
| sparse | 4.884 | 4.722 | 0.9709 |
| multi | 4.106 | 3.941 | 0.9568 |
| dense_group_guard | 8.973 | 8.976 | 0.9967 |

## Final 100M-row unordered pairs against 0.3.9

Alternating same-archive pairs; each engine opens and closes sequentially. A final/baseline ratio above 1 means slower. Paired ratios and ratios of displayed median times can differ.

| Query | Baseline ms | 0.3.10 ms | Paired final/baseline |
|---|---:|---:|---:|
| unordered | 340.939 | 318.823 | 0.9392 |

## Checks against pre-regression 0.3.8

Alternating same-archive pairs; each engine opens and closes sequentially. A final/baseline ratio above 1 means slower. Paired ratios and ratios of displayed median times can differ.

| Query | Baseline ms | 0.3.10 ms | Paired final/baseline |
|---|---:|---:|---:|
| unordered | 2.951 | 2.910 | 0.9910 |
| multi | 3.947 | 3.947 | 1.0062 |

## Instrumented 1M-row stage checks

Median stage times from seven alternating profiled pairs; these samples are excluded from competitive timing totals.

| Query | Read 0.3.9 ms | Read 0.3.10 ms | Select 0.3.9 ms | Select 0.3.10 ms | Aggregate 0.3.9 ms | Aggregate 0.3.10 ms |
|---|---:|---:|---:|---:|---:|---:|
| unordered | 2.004 | 1.995 | 0.839 | 0.623 | 0.264 | 0.266 |
| sparse | 4.261 | 4.267 | 0.638 | 0.513 | 0.054 | 0.054 |
| multi | 3.305 | 3.589 | 0.607 | 0.488 | 0.259 | 0.265 |
| dense_group_guard | 5.124 | 4.987 | 0.175 | 0.174 | 4.703 | 4.706 |

## Matched matrix

| Fixture | Query | 0.3.9 ms | 0.3.10 ms | DuckDB ms | Paired before/after | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 7.046 | 7.106 | 7.569 | 0.997x | ✅; 3/3 rounds |
| dense97 | group_full | 9.301 | 9.389 | 11.344 | 0.991x | ✅; 3/3 rounds |
| dense97 | filtered_group | 6.402 | 6.292 | 8.057 | 1.004x | ✅; 3/3 rounds |
| dense97 | unordered_control | 3.150 | 2.913 | 3.789 | 1.074x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.006 | 0.006 | 1.685 | 1.000x | ✅; 3/3 rounds |
| sparse19 | group_sum | 8.662 | 8.656 | 11.168 | 0.995x | ✅; 3/3 rounds |
| sparse19 | group_full | 11.643 | 10.673 | 14.941 | 1.083x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 7.251 | 6.876 | 10.396 | 1.055x | ✅; 3/3 rounds |
| sparse19 | unordered_control | 3.160 | 3.068 | 3.923 | 1.039x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.005 | 1.702 | 1.055x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 8.141 | 8.386 | 18.607 | 0.971x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 11.042 | 10.958 | 27.555 | 0.993x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 7.644 | 7.267 | 17.070 | 1.031x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 3.165 | 3.032 | 3.783 | 1.046x | ✅; 3/3 rounds |
| cardinality5003 | prefix_control | 0.006 | 0.006 | 1.722 | 0.982x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.005 | 17.366 | 1.200x | ✅; 3/3 rounds |
| nyc | day | 0.006 | 0.005 | 1.648 | 1.098x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.005 | 0.695 | 1.136x | ✅; 3/3 rounds |
| nyc | zone | 1.181 | 1.144 | 1.768 | 1.023x | ✅; 3/3 rounds |
| nyc | all_zones | 25.495 | 25.024 | 25.420 | 1.010x | ✅; 3/3 rounds |
| 10000000 | group_sum | 73.613 | 75.008 | 70.067 | 0.985x | ❌; 0/3 rounds |
| 10000000 | group_full | 94.094 | 93.885 | 105.004 | 0.993x | ✅; 2/3 rounds |
| 10000000 | filtered_group | 68.343 | 65.389 | 74.902 | 1.042x | ✅; 3/3 rounds |
| 10000000 | unordered_control | 33.838 | 32.391 | 35.777 | 1.030x | ✅; 3/3 rounds |
| 10000000 | prefix_control | 0.004 | 0.004 | 8.183 | 1.026x | ✅; 3/3 rounds |
| 100000000 | group_sum | 733.429 | 729.341 | 780.093 | 1.000x | ✅; 3/3 rounds |
| 100000000 | group_full | 934.893 | 928.317 | 1117.239 | 1.011x | ✅; 3/3 rounds |
| 100000000 | filtered_group | 681.610 | 654.158 | 827.451 | 1.042x | ✅; 3/3 rounds |
| 100000000 | unordered_control | 346.693 | 323.574 | 352.769 | 1.062x | ✅; 3/3 rounds |
| 100000000 | prefix_control | 0.007 | 0.006 | 73.743 | 1.017x | ✅; 3/3 rounds |

## Additional stress matrix

| Fixture | Query | 0.3.9 ms | 0.3.10 ms | DuckDB ms | Paired before/after | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 21.480 | 21.428 | 18.380 | 1.008x | ❌; 0/3 rounds |
| wide5003 | group_full | 24.168 | 24.464 | 26.928 | 1.000x | ✅; 3/3 rounds |
| wide5003 | filtered_group | 14.613 | 14.655 | 16.981 | 1.002x | ✅; 3/3 rounds |
| wide5003 | unordered_control | 3.171 | 2.978 | 3.730 | 1.065x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.006 | 0.006 | 1.677 | 0.933x | ✅; 3/3 rounds |
| collision19 | group_sum | 18.040 | 17.893 | 10.944 | 1.001x | ❌; 0/3 rounds |
| collision19 | group_full | 19.795 | 19.939 | 14.532 | 0.993x | ❌; 0/3 rounds |
| collision19 | filtered_group | 11.926 | 11.597 | 10.507 | 1.028x | ❌; 0/3 rounds |
| collision19 | unordered_control | 3.134 | 2.935 | 3.748 | 1.068x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.006 | 0.005 | 1.665 | 1.091x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 40.671 | 41.026 | 91.107 | 0.995x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 50.448 | 51.803 | 130.801 | 0.974x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 34.776 | 36.050 | 93.530 | 0.983x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 3.135 | 2.906 | 3.783 | 1.086x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.006 | 0.006 | 1.689 | 1.018x | ✅; 3/3 rounds |

## Correctness, recovery and limitations

All 70 Rust tests pass in debug/release, with formatting and default/fault-feature Clippy. The added public-API regression test compares 180 signed-edge/filter-order/partial-block queries with the independent RAM engine, then repeats all 180 after reopening. The final CLI/bridge also match 1,600 SQL cases against each DuckDB and SQLite: 500 general archive queries, 500 expanded/signed-sparse groups and 600 scan/selectivity cases. Reopen, confirmed retries, full CRC scrubs and exact positive/negative i128 JSON outputs pass.

Current binaries pass 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent process kills, 14 source fault points, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL oracles. These checks cover process and injected I/O failures; they do not qualify physical power loss. Storage and writer policy are unchanged.

The unchanged unfiltered-group controls are used to detect broad code-generation effects; their measured ratios remain evidence, even when they fluctuate. Profiling alone is not an end-to-end speed claim. No new network capacity, sustained mixed-write latency, cold-I/O, distributed-scale or production readiness is established. Older service failures remain in the history. The previous multi-server comparison is [0.3.1](PERFORMANCE_031.md).

## Reproduce and inspect

Run serially with the pinned local Python dependencies: `checks_040.py`, `build_source_adapter_040.py`, `time_040.py`, `run_040.py`, `report_040.py`, `docs_040.py`, then `package_040.py`. Never overlap build, test, packaging or any heavy job with timed workloads. Matrix helpers accept configurable large/NYC fixture roots and can regenerate small fixtures. Controls require local retained datasets and refuse completed-output replacement. Current release is 0.3.10; 040 is the internal experiment/evidence identifier.

- [All current summaries and gates](benchmarks/scan-040-audit.json)
- [Final paired controls](benchmarks/scan-040-final-pairs.json)
- [Final 100M-row controls](benchmarks/scan-040-final-large-pairs.json)
- [Pre-regression 0.3.8 controls](benchmarks/scan-040-anchor038-pairs.json)
- [Final stage profiles](benchmarks/scan-040-final-profiles.json)
- [Initial stage diagnosis](benchmarks/scan-040-stage-profiles.json)
- [Rejected outlining trial](benchmarks/trial-040-noinline/proof.json)
- [Rejected trial timings](benchmarks/scan-040-noinline-pairs.json)
- [Direct-selection trial](benchmarks/trial-040-fused-first/proof.json)
- [Initial direct-selection 100M-row pairs](benchmarks/scan-040-fused-first-large-pairs.json)
- [1M-row full matrix](benchmarks/group-040-typed-comparison.json)
- [NYC full matrix](benchmarks/group-040-nyc-comparison.json)
- [10M/100M-row full matrix](benchmarks/group-040-large-comparison.json)
- [Wide/collision/high-cardinality matrix](benchmarks/group-040-extended-comparison.json)
- [New scan SQL oracle cases](benchmarks/scan-040-differential.json)
- [Build order and hashes](benchmarks/rust-checks-040.json)
- [Timed work order](benchmarks/scan-040-run-order.json)
- [Correctness and recovery order](benchmarks/correctness-040-run-order.json)
- [Complete historical index](BENCHMARK_HISTORY.md)
