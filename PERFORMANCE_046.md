# 0.3.16: smaller exact tags for medium sparse groups

The promoted sparse key cache now stores an exact signed key and a checked u32 group index plus one. Zero in the index field marks an empty entry, so key zero and both i64 boundaries remain ordinary valid keys. The authoritative randomized HashMap, 16,384 cache slots, 8,192-key ceiling, hit-rate fallback, deferred promotion, counts and exact i128 reductions retain their preceding behavior.

On this 64-bit Windows build, each entry is 16 bytes rather than the preceding 24-byte Option tuple. The promoted payload table is **256 KiB instead of 384 KiB**, a one-third reduction. Group-index encoding uses a checked conversion and a compile-time result-budget bound. This is query-local memory, not a reduction in persisted archive size or total process memory. The 0.3.15 reader cache and its active/idle handle policy remain unchanged.

The development trial measured about 11.4% faster irregular SUM and 10.6% faster full grouping in alternating pairs. Before those timings, the policy required irregular SUM ratio below 0.95 and every unprofiled guard below 1.05; the trial passed both. Two earlier build attempts are preserved: a missing Debug derive prevented compilation, then an existing footprint test retained the old 384 KiB expectation. The repaired expectation verifies the new budget, with SQL oracles retained. The candidate below is independently rebuilt and remeasured.

Fresh DuckDB matrix: **60 wins / 0 losses** over 60 shapes; released 0.3.15 measured 59 wins and one loss. All 108 engine/fixture/round cases and 5,940 samples remain visible. Separate uninstrumented controls retain 23,030 samples; 1,078 instrumented samples are excluded from competitive totals. The development trial adds 20,118 uninstrumented and 616 excluded instrumented samples.

Closest competitive result: irregular5003/group_sum, candidate 16.8626 ms versus DuckDB 16.9165 ms; 2/3 rounds. The relative median gap is 0.32%. A small median edge on this desktop is a near tie, not evidence of a universal ranking.

Separate 21-pair closest-case repeat: ✅ win; Kestrel 16.7110 ms vs DuckDB 17.1132 ms, paired candidate/DuckDB ratio 0.9794, Kestrel faster in 19/21 pairs. Its 462 samples use one persistent process per engine and a single-query history; they remain separate from the 60-shape score. This repeat is retained regardless of outcome.

These are warm local queries on one shared Windows computer. The matrix rotates three engine orders with three warmups, eleven samples and one thread. Rust timers measure ArchiveSnapshot::query; DuckDB includes Python execute/fetchall. Native storage layouts and interfaces differ. Builds, setup, qualification and full scrubs are untimed, and timed workloads run serially. No new network requests/s or general database-service qualification is claimed.

## Final alternating controls

Times are medians of pair medians. The paired ratio is the median candidate/baseline ratio within each pair; desktop variance can make those summaries differ. Smaller ratios are faster. There are 21 pairs of eleven samples per binary, except tiny queries (21 pairs of 101) and 100M rows (seven pairs of five). Every repeated result matches and final archives are fully scrubbed.

| Control | Rows | Query | 0.3.15 ms | 0.3.16 ms | Paired candidate / baseline |
|---|---:|---|---:|---:|---:|
| final-pairs | 1,000,000 | group_sum | 7.7104 | 7.7285 | 0.9996 |
| final-pairs | 1,000,000 | group_full | 10.5238 | 10.2590 | 0.9772 |
| final-pairs | 1,000,000 | filtered_group | 7.2867 | 7.2917 | 1.0148 |
| wide-pairs | 1,000,000 | group_sum | 15.9062 | 15.2322 | 0.9505 |
| wide-pairs | 1,000,000 | group_full | 14.7387 | 14.1471 | 0.9406 |
| wide-pairs | 1,000,000 | filtered_group | 12.4970 | 12.0670 | 0.9222 |
| irregular-pairs | 1,000,000 | group_sum | 19.7876 | 17.7426 | 0.8969 |
| irregular-pairs | 1,000,000 | group_full | 26.3488 | 24.1454 | 0.9003 |
| irregular-pairs | 1,000,000 | filtered_group | 11.1634 | 10.7456 | 0.9658 |
| irregular-pairs | 1,000,000 | unordered_control | 4.7961 | 4.7191 | 0.9918 |
| highcard-guard-pairs | 1,000,000 | group_sum | 40.4620 | 40.3105 | 0.9931 |
| highcard-guard-pairs | 1,000,000 | group_full | 49.9631 | 49.8211 | 0.9956 |
| dense-guard-pairs | 1,000,000 | group_sum | 7.3648 | 7.3143 | 0.9922 |
| dense-guard-pairs | 1,000,000 | group_full | 10.8435 | 10.8562 | 1.0039 |
| dense-guard-pairs | 1,000,000 | filtered_group | 6.7333 | 6.7692 | 1.0008 |
| scan-guard-pairs | 1,000,000 | unordered | 2.8530 | 2.8580 | 1.0018 |
| scan-guard-pairs | 1,000,000 | sparse | 4.6291 | 4.6784 | 1.0132 |
| scan-guard-pairs | 1,000,000 | multi | 3.8523 | 3.9133 | 1.0086 |
| scan-guard-pairs | 1,000,000 | dense_group_guard | 8.9310 | 8.9506 | 1.0016 |
| tiny-guard-pairs | 1,000 | group_sum | 0.0601 | 0.0621 | 1.0201 |
| tiny-guard-pairs | 1,000 | group_full | 0.0761 | 0.0782 | 0.9925 |
| tiny-guard-pairs | 1,000 | filtered_group | 0.0587 | 0.0583 | 0.9950 |
| 10m-guard-pairs | 10,000,000 | group_sum | 67.0487 | 65.7398 | 0.9739 |
| 10m-guard-pairs | 10,000,000 | group_full | 94.4489 | 94.4841 | 1.0011 |
| 10m-guard-pairs | 10,000,000 | filtered_group | 61.2379 | 61.6547 | 1.0079 |
| 100m-guard-pairs | 100,000,000 | group_sum | 662.3991 | 659.2941 | 0.9961 |
| 100m-guard-pairs | 100,000,000 | group_full | 929.1237 | 940.3324 | 1.0209 |

Every slower control is retained. The largest is 100m-guard-pairs/group_full at 100,000,000 rows: paired ratio 1.0209, or 2.09% slower in this run.

## Stage diagnosis, excluded from competitive results

| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |
|---|---|---:|---:|---:|
| sparse19 | group_sum | 4.305 / 4.208 | 0.165 / 0.163 | 3.389 / 3.256 |
| sparse19 | group_full | 4.409 / 4.572 | 0.167 / 0.168 | 5.651 / 5.512 |
| sparse19 | filtered_group | 4.131 / 4.218 | 0.628 / 0.633 | 1.690 / 1.666 |
| irregular5003 | group_sum | 3.639 / 3.655 | 0.170 / 0.173 | 14.443 / 12.066 |
| irregular5003 | group_full | 3.688 / 3.686 | 0.169 / 0.172 | 16.174 / 14.082 |
| irregular5003 | filtered_group | 3.630 / 3.632 | 0.634 / 0.636 | 5.837 / 5.492 |
| irregular5003 | unordered_control | 2.687 / 2.684 | 0.819 / 0.816 | 0.268 / 0.267 |

## Matched matrix

| Fixture | Query | 0.3.15 ms | 0.3.16 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 6.253 | 6.326 | 7.553 | 0.989x | ✅; 3/3 rounds |
| dense97 | group_full | 8.981 | 8.993 | 11.314 | 0.986x | ✅; 3/3 rounds |
| dense97 | filtered_group | 5.789 | 5.819 | 8.022 | 0.995x | ✅; 3/3 rounds |
| dense97 | unordered_control | 2.917 | 2.788 | 3.750 | 1.013x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.006 | 0.006 | 1.694 | 1.017x | ✅; 3/3 rounds |
| sparse19 | group_sum | 7.799 | 7.638 | 11.314 | 1.022x | ✅; 3/3 rounds |
| sparse19 | group_full | 10.068 | 9.860 | 14.739 | 1.021x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 6.497 | 6.600 | 10.502 | 0.984x | ✅; 3/3 rounds |
| sparse19 | unordered_control | 2.944 | 2.949 | 3.827 | 0.968x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.006 | 1.708 | 1.036x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 7.353 | 7.592 | 18.584 | 0.966x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 10.868 | 10.803 | 27.031 | 0.997x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 7.103 | 6.818 | 17.463 | 1.042x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 2.926 | 2.942 | 3.741 | 0.995x | ✅; 3/3 rounds |
| cardinality5003 | prefix_control | 0.006 | 0.006 | 1.719 | 1.000x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.005 | 17.519 | 1.000x | ✅; 3/3 rounds |
| nyc | day | 0.006 | 0.005 | 1.691 | 1.077x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.005 | 0.686 | 1.022x | ✅; 3/3 rounds |
| nyc | zone | 1.025 | 0.987 | 1.755 | 1.030x | ✅; 3/3 rounds |
| nyc | all_zones | 21.856 | 23.125 | 26.159 | 0.946x | ✅; 3/3 rounds |
| 10000000 | group_sum | 68.769 | 66.410 | 70.990 | 1.045x | ✅; 3/3 rounds |
| 10000000 | group_full | 95.648 | 94.674 | 106.403 | 1.010x | ✅; 3/3 rounds |
| 10000000 | filtered_group | 64.980 | 62.796 | 78.985 | 1.033x | ✅; 3/3 rounds |
| 10000000 | unordered_control | 32.508 | 32.086 | 37.179 | 1.013x | ✅; 3/3 rounds |
| 10000000 | prefix_control | 0.004 | 0.004 | 8.441 | 0.974x | ✅; 3/3 rounds |
| 100000000 | group_sum | 669.073 | 668.084 | 792.120 | 0.978x | ✅; 3/3 rounds |
| 100000000 | group_full | 931.713 | 950.047 | 1128.446 | 0.981x | ✅; 2/3 rounds |
| 100000000 | filtered_group | 620.022 | 643.295 | 909.858 | 0.964x | ✅; 2/3 rounds |
| 100000000 | unordered_control | 315.214 | 316.997 | 430.117 | 0.985x | ✅; 2/3 rounds |
| 100000000 | prefix_control | 0.008 | 0.008 | 81.561 | 0.864x | ✅; 3/3 rounds |

## Prior stress matrix

| Fixture | Query | 0.3.15 ms | 0.3.16 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 11.746 | 11.163 | 18.316 | 1.048x | ✅; 3/3 rounds |
| wide5003 | group_full | 13.808 | 13.523 | 26.951 | 1.023x | ✅; 3/3 rounds |
| wide5003 | filtered_group | 9.613 | 9.430 | 17.064 | 1.036x | ✅; 3/3 rounds |
| wide5003 | unordered_control | 2.887 | 2.873 | 3.750 | 1.005x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.006 | 0.006 | 1.688 | 1.000x | ✅; 3/3 rounds |
| collision19 | group_sum | 7.629 | 7.695 | 11.057 | 0.984x | ✅; 3/3 rounds |
| collision19 | group_full | 10.076 | 9.889 | 14.608 | 1.024x | ✅; 3/3 rounds |
| collision19 | filtered_group | 6.622 | 6.343 | 10.289 | 1.047x | ✅; 3/3 rounds |
| collision19 | unordered_control | 2.893 | 2.894 | 3.748 | 1.005x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.006 | 0.006 | 1.659 | 1.089x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 40.667 | 40.242 | 91.846 | 0.994x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 50.629 | 49.026 | 129.643 | 0.999x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 34.577 | 34.882 | 94.491 | 0.991x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 2.809 | 2.911 | 3.817 | 0.966x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.006 | 0.006 | 1.678 | 0.982x | ✅; 3/3 rounds |

## Key-pattern matrix

| Fixture | Query | 0.3.15 ms | 0.3.16 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| fibonacci19 | group_sum | 7.750 | 7.664 | 11.187 | 1.011x | ✅; 3/3 rounds |
| fibonacci19 | group_full | 10.092 | 9.965 | 14.600 | 1.016x | ✅; 3/3 rounds |
| fibonacci19 | filtered_group | 6.626 | 6.732 | 10.513 | 0.984x | ✅; 3/3 rounds |
| fibonacci19 | unordered_control | 2.806 | 2.860 | 3.862 | 0.976x | ✅; 3/3 rounds |
| fibonacci19 | prefix_control | 0.006 | 0.006 | 1.776 | 1.034x | ✅; 3/3 rounds |
| power19 | group_sum | 7.859 | 7.609 | 11.100 | 1.003x | ✅; 3/3 rounds |
| power19 | group_full | 10.069 | 9.750 | 14.798 | 1.035x | ✅; 3/3 rounds |
| power19 | filtered_group | 6.415 | 6.352 | 10.417 | 1.007x | ✅; 3/3 rounds |
| power19 | unordered_control | 2.779 | 2.791 | 3.783 | 0.996x | ✅; 3/3 rounds |
| power19 | prefix_control | 0.006 | 0.006 | 1.681 | 1.017x | ✅; 3/3 rounds |

## Irregular signed-key matrix

| Fixture | Query | 0.3.15 ms | 0.3.16 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| irregular5003 | group_sum | 18.884 | 16.863 | 16.916 | 1.115x | ✅; 2/3 rounds |
| irregular5003 | group_full | 21.247 | 18.837 | 25.479 | 1.119x | ✅; 3/3 rounds |
| irregular5003 | filtered_group | 10.910 | 10.625 | 15.642 | 1.027x | ✅; 3/3 rounds |
| irregular5003 | unordered_control | 2.879 | 2.841 | 3.818 | 1.041x | ✅; 3/3 rounds |
| irregular5003 | prefix_control | 0.005 | 0.005 | 1.690 | 0.978x | ✅; 3/3 rounds |

## Correctness and durability

All 77 Rust tests pass in debug/release, formatting and both Clippy configurations. The new manual BTreeMap oracle starts with group key zero, forces real tagged-cache collisions, exercises both signed key boundaries and beyond-i64 sums with AVG, and verifies the 256 KiB table. Existing promotion/demotion, group-budget and wide-reduction oracles remain.

The final CLI/bridge match 4,000 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping and 600 each for key patterns, medium, dense, sparse and scan cases. Exact signed wide shared SUM/AVG JSON survives confirmed retry/reopen. Another 104 manual integer bridge oracles include 96 requests across eight clients, handle reuse, fresh scrub behavior, warmed corruption rejection and receipt-preserving cold reopen. Those concurrent correctness requests are untimed.

Current binaries also pass 56 publication cuts, 22 catalog corruption rejections, 32 forced process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL checks. Reader ownership, snapshot retirement, serialized formats and durable writer/source policy retain exact preceding source identity. Process kills and injected failures do not qualify physical power loss.

Only DuckDB is freshly competed. The last multi-server network matrix remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Cold I/O, server requests/s, distributed scale, universal superiority and production readiness remain unqualified. Smaller cache payloads do not imply that every query is faster.

## Reproduce and inspect

Run checks_046.py, build_source_adapter_046.py, time_046.py, run_046.py, report_046.py, docs_046.py and package_046.py serially with pinned local dependencies. Trial sources, binaries, exact build harnesses, failures and work orders are preserved. Restore frozen trial sources in an isolated checkout before rebuilding. Never overwrite completed evidence or overlap compilation/qualification/packaging with timed database workloads. Release 0.3.16 uses experiment identifier 046.

- [Complete gates and all scores](benchmarks/packed-046-audit.json)
- [Separate closest-case Kestrel/DuckDB pairs](benchmarks/packed-046-closest-duck-pairs.json)
- [Final irregular pairs](benchmarks/packed-046-irregular-pairs.json)
- [Final profiles](benchmarks/packed-046-irregular-profiles.json)
- [Small sparse final pairs](benchmarks/packed-046-final-pairs.json)
- [Wide sparse final pairs](benchmarks/packed-046-wide-pairs.json)
- [Tiny guards](benchmarks/packed-046-tiny-guard-pairs.json)
- [Scan guards](benchmarks/packed-046-scan-guard-pairs.json)
- [High-cardinality guards](benchmarks/packed-046-highcard-guard-pairs.json)
- [Dense guards](benchmarks/packed-046-dense-guard-pairs.json)
- [10M guards](benchmarks/packed-046-10m-guard-pairs.json)
- [100M guards](benchmarks/packed-046-100m-guard-pairs.json)
- [Predeclared policy](benchmarks/packed-046-trial-policy.json)
- [Selection and every trial ratio](benchmarks/packed-046-selection.json)
- [Frozen trial source/binary](benchmarks/trial-046-packed-medium-tags-corrected/proof.json)
- [Initial compile failure](benchmarks/trial-046-packed-medium-tags/failure.json)
- [Old footprint expectation failure](benchmarks/trial-046-packed-medium-tags-ready/failure.json)
- [Build repairs](benchmarks/packed-046-build-repairs.json)
- [Current SQL oracles](benchmarks/medium-046-differential.json)
- [Current bridge concurrency/reuse/corruption](benchmarks/reader-046-verification.json)
- [Final build provenance](benchmarks/rust-checks-046.json)
- [Timed work order](benchmarks/packed-046-run-order.json)
- [Qualification work order](benchmarks/correctness-046-run-order.json)
- [All history and unsuccessful evidence](BENCHMARK_HISTORY.md)
