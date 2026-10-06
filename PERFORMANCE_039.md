# 0.3.9: wider bounded grouping and typed sparse states

Compact integer groups now use direct-address arrays for up to 65,536 slots, while keeping the conservative 8 MiB query-local budget. Above the original 4,096-slot range, the slot count must also fit the archive row count. Wide domains use a standard randomized HashMap from key to slot and the same typed reductions. A query-local tagged cache holds 256 key/slot entries (6 KiB on this host), verifies exact keys on every hit and is released after 128 distinct keys or a block of at least 64 selected rows with fewer than half cache hits. Disabled-cache blocks use a separate plain-hash kernel with cache checks compiled out. SUM/AVG and repeated reductions share accumulators. The 100,000-result group limit remains.

Fresh comparisons contain 81 sequential engine/fixture/round cases, 45 query shapes and 4,455 timed samples. Each shape has three rotated engine orders, three warmups and eleven samples. Tables show the median of run medians and the median paired before/after ratio. Both engines use one thread and warm caches. Rust timers cover ArchiveSnapshot::query; DuckDB timers include Python execute/fetchall, with native compression and a 256 MB buffer limit. Setup, JSON framing, assertions and scrubs are outside Rust timers. These are descriptive shared-desktop measurements.

The matched 30-shape matrix has 22 median wins and 8 losses against DuckDB. The additional 15-shape stress matrix has 11 wins and 4 losses. Per-round outcomes and every loss remain below.

## Matched matrix

| Fixture | Query | 0.3.8 ms | 0.3.9 ms | DuckDB ms | Paired improvement | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 9.091 | 8.448 | 8.105 | 1.05x | ❌; 1/3 rounds |
| dense97 | group_full | 10.388 | 10.035 | 12.067 | 0.99x | ✅; 3/3 rounds |
| dense97 | filtered_group | 6.983 | 7.480 | 8.649 | 0.94x | ✅; 3/3 rounds |
| dense97 | unordered_control | 3.485 | 3.597 | 4.025 | 0.93x | ✅; 2/3 rounds |
| dense97 | prefix_control | 0.006 | 0.006 | 1.847 | 0.98x | ✅; 3/3 rounds |
| sparse19 | group_sum | 48.632 | 18.323 | 28.972 | 2.46x | ✅; 3/3 rounds |
| sparse19 | group_full | 72.401 | 24.806 | 37.785 | 2.77x | ✅; 3/3 rounds |
| sparse19 | filtered_group | 32.922 | 16.686 | 19.188 | 1.62x | ✅; 2/3 rounds |
| sparse19 | unordered_control | 7.369 | 7.678 | 10.319 | 0.96x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.012 | 0.008 | 5.027 | 1.08x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 64.322 | 12.912 | 26.821 | 4.98x | ✅; 3/3 rounds |
| cardinality5003 | group_full | 106.959 | 17.105 | 33.517 | 6.25x | ✅; 3/3 rounds |
| cardinality5003 | filtered_group | 33.361 | 10.134 | 21.067 | 3.14x | ✅; 3/3 rounds |
| cardinality5003 | unordered_control | 4.304 | 4.514 | 4.722 | 1.02x | ✅; 2/3 rounds |
| cardinality5003 | prefix_control | 0.007 | 0.007 | 2.139 | 1.00x | ✅; 3/3 rounds |
| nyc | month | 0.007 | 0.005 | 23.690 | 1.18x | ✅; 3/3 rounds |
| nyc | day | 0.007 | 0.006 | 3.235 | 1.11x | ✅; 3/3 rounds |
| nyc | hour | 0.006 | 0.005 | 1.221 | 1.15x | ✅; 3/3 rounds |
| nyc | zone | 1.722 | 1.720 | 2.494 | 1.00x | ✅; 2/3 rounds |
| nyc | all_zones | 38.015 | 38.656 | 34.912 | 0.87x | ❌; 0/3 rounds |
| 10000000 | group_sum | 97.418 | 104.193 | 97.213 | 0.92x | ❌; 1/3 rounds |
| 10000000 | group_full | 122.043 | 136.188 | 155.559 | 0.90x | ✅; 1/3 rounds |
| 10000000 | filtered_group | 81.019 | 110.046 | 95.743 | 0.89x | ❌; 2/3 rounds |
| 10000000 | unordered_control | 40.507 | 52.231 | 46.575 | 0.79x | ❌; 1/3 rounds |
| 10000000 | prefix_control | 0.005 | 0.008 | 11.310 | 0.85x | ✅; 3/3 rounds |
| 100000000 | group_sum | 788.174 | 1166.708 | 1282.576 | 0.77x | ✅; 2/3 rounds |
| 100000000 | group_full | 1077.264 | 1508.973 | 1502.424 | 0.77x | ❌; 1/3 rounds |
| 100000000 | filtered_group | 773.897 | 1241.257 | 1128.066 | 0.62x | ❌; 2/3 rounds |
| 100000000 | unordered_control | 349.036 | 519.691 | 442.048 | 0.66x | ❌; 1/3 rounds |
| 100000000 | prefix_control | 0.007 | 0.009 | 90.131 | 0.80x | ✅; 3/3 rounds |

## Additional wide/collision/high-cardinality matrix

| Fixture | Query | 0.3.8 ms | 0.3.9 ms | DuckDB ms | Paired improvement | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| wide5003 | group_sum | 34.981 | 23.033 | 20.003 | 1.50x | ❌; 0/3 rounds |
| wide5003 | group_full | 52.035 | 25.538 | 29.265 | 2.00x | ✅; 3/3 rounds |
| wide5003 | filtered_group | 23.877 | 16.224 | 18.334 | 1.49x | ✅; 3/3 rounds |
| wide5003 | unordered_control | 3.323 | 3.525 | 4.128 | 0.95x | ✅; 3/3 rounds |
| wide5003 | prefix_control | 0.007 | 0.007 | 1.842 | 1.03x | ✅; 3/3 rounds |
| collision19 | group_sum | 22.987 | 20.049 | 11.863 | 1.18x | ❌; 0/3 rounds |
| collision19 | group_full | 33.199 | 22.147 | 15.904 | 1.53x | ❌; 0/3 rounds |
| collision19 | filtered_group | 15.945 | 14.142 | 11.309 | 1.16x | ❌; 0/3 rounds |
| collision19 | unordered_control | 3.451 | 3.519 | 4.029 | 0.96x | ✅; 3/3 rounds |
| collision19 | prefix_control | 0.006 | 0.006 | 1.822 | 1.07x | ✅; 3/3 rounds |
| cardinality70001 | group_sum | 132.483 | 47.927 | 99.465 | 2.76x | ✅; 3/3 rounds |
| cardinality70001 | group_full | 199.586 | 62.694 | 148.556 | 3.18x | ✅; 3/3 rounds |
| cardinality70001 | filtered_group | 95.648 | 40.927 | 110.044 | 2.33x | ✅; 3/3 rounds |
| cardinality70001 | unordered_control | 3.200 | 3.586 | 4.305 | 0.89x | ✅; 3/3 rounds |
| cardinality70001 | prefix_control | 0.006 | 0.006 | 1.801 | 0.98x | ✅; 3/3 rounds |

## Short controls against released 0.3.8

21 alternating engine pairs; three warmups and eleven timed samples per query; exact-byte independent fixture copies; setup/copy/scrub outside timers; no overlapping heavy work. A ratio above 1 means the final candidate was slower.

| Fixture | Query | Baseline ms | Final ms | Paired final/baseline |
|---|---|---:|---:|---:|
| dense97 | group_full | 9.610 | 9.715 | 1.015 |
| dense97 | unordered_control | 3.150 | 3.382 | 1.073 |
| dense97 | prefix_control | 0.006 | 0.005 | 0.982 |
| sparse19 | group_full | 32.985 | 11.635 | 0.352 |
| cardinality5003 | group_full | 49.823 | 11.607 | 0.234 |
| nyc | zone | 1.181 | 1.195 | 0.999 |
| nyc | all_zones | 26.215 | 26.458 | 1.011 |
| nyc | day | 0.005 | 0.005 | 1.038 |

## Cache versus the preserved uncached 0.3.9 trial

11 alternating engine pairs; three warmups and eleven timed samples per query; exact-byte independent fixture copies; setup/copy/scrub outside timers; no overlapping heavy work. A ratio above 1 means the final candidate was slower.

| Fixture | Query | Baseline ms | Final ms | Paired final/baseline |
|---|---|---:|---:|---:|
| dense97 | group_full | 9.464 | 9.430 | 1.000 |
| dense97 | unordered_control | 3.247 | 3.250 | 1.001 |
| sparse19 | group_sum | 18.709 | 9.177 | 0.485 |
| sparse19 | group_full | 20.666 | 11.202 | 0.541 |
| wide5003 | group_full | 24.910 | 24.718 | 0.991 |
| collision19 | group_sum | 18.835 | 18.673 | 0.989 |
| collision19 | group_full | 20.909 | 20.750 | 0.999 |

## Large controls on the same 100M-row archive

Seven alternating pairs per query; same immutable archive opened sequentially, five timed samples and three warmups per call; open/close/assertions and final scrubs outside timers; no copies or overlapping heavy work. A ratio above 1 means the final candidate was slower.

| Fixture | Query | Baseline ms | Final ms | Paired final/baseline |
|---|---|---:|---:|---:|
| 100M | group_full | 951.982 | 954.434 | 1.000 |
| 100M | unordered_control | 333.462 | 350.733 | 1.053 |

The original rotated 100M-row full-grouping slowdown did not repeat in seven short alternating pairs. The unordered scan control remains about 5-7% slower in paired 1M/100M checks and is a known regression. These observations are preserved even though the ungrouped scan helpers are byte-identical in source. Shared-desktop variation is substantial; unchanged algorithm text is not evidence of unchanged measured latency.

## Correctness and recovery

All 69 Rust tests pass in debug/release, with formatting and default/fault-feature Clippy. New tests cover larger compact domains, signed edges, holes, exact wide sums and duplicate SUM/AVG outputs, tagged-cache collisions and cardinality release, and accepting known keys at the 100,000-group limit. One thousand seeded SQL queries match both DuckDB and SQLite: 500 general archive cases and 500 expanded/signed-sparse group cases over eight overlapping sorted runs. Both group modes also pass reopen, known-receipt replay and full scrubs.

The current CLI/bridge pass exact positive/negative i128 sparse sums through JSON, invalid-query continuity, replay/reopen and CRC scrub. Current binaries pass 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent forced kills, 14 source failures, eight source kills and the 30,000-row/300-interval Parquet demo with 42 SQL oracles. Storage/publication/live/source and ungrouped scan helpers are unchanged. These are process/IO failure checks, not physical power-loss qualification.

The uncached typed trial and its 1,485 timed samples, source and binary hashes are preserved. Its expanded-domain gain passed, while low-cardinality sparse grouping still lost to DuckDB and motivated the bounded cache. The first cached candidate, its 4,455 comparison samples, 5,390 paired samples, 68-test build and exact source/probe are also preserved. Its 4-7% cache penalty on colliding/wider keys motivated block specialization and cache usefulness detection. The initial profile-runner result-envelope error is recorded. Earlier releases, failed experiments, service failures and all original timing samples remain unchanged.

The authoritative sparse map keeps Rust's default randomized hashing. Cache misses and collisions always return to that map; the cache cannot alias keys. [Rust HashMap documentation](https://doc.rust-lang.org/std/collections/struct.HashMap.html) describes its default randomized protection and the tradeoffs of replacing the hasher. This experiment changes state layout and reuses confirmed key lookups.

No new requests/s, cold-I/O, sustained mixed-write, distributed-scale or production readiness claim follows from these read-query measurements. The previous multi-server matrix is [0.3.1](PERFORMANCE_031.md).

## Reproduce and inspect

Run serially: `python benchmarks/checks_039.py`, `python benchmarks/build_source_adapter_039.py`, then `group_compare_039.py` for each scope with fresh output names. Small and extended scopes can regenerate integer fixtures; `--reuse-small-fixtures` reuses this computer's retained 0.3.8 datasets. Large/NYC paths are configurable with `--scale-root` and `--nyc-root`. Use the pinned local DuckDB installation. Never overlap compilation, tests, packaging or other heavy work with query timing. Completed outputs and release packages refuse replacement.

- [All qualified summaries and limits](benchmarks/group-039-audit.json)
- [Matched 1M-row samples](benchmarks/group-039-typed-comparison.json)
- [NYC samples](benchmarks/group-039-nyc-comparison.json)
- [10M/100M-row samples](benchmarks/group-039-large-comparison.json)
- [Collision/wide/70,001-key samples](benchmarks/group-039-extended-comparison.json)
- [Short paired controls](benchmarks/group-039-paired-controls.json)
- [100M-row same-archive controls](benchmarks/group-039-large-pairs.json)
- [Cache pairs and original trial](benchmarks/group-039-cache-pairs.json)
- [Original uncached trial samples](benchmarks/group-039-typed-trial-comparison.json)
- [Initial stage profiles](benchmarks/group-039-baseline-profiles.json)
- [Preserved first-cache trial and regressions](benchmarks/trial-039-first-cache/trial-audit.json)
- [Final stage profiles](benchmarks/group-039-final-profiles.json)
- [Expanded/sparse SQL oracle cases](benchmarks/group-039-differential.json)
- [Serial builds](benchmarks/rust-checks-039.json)
- [Serial timed scopes](benchmarks/group-039-run-order.json)
- [Correctness/recovery order](benchmarks/correctness-039-run-order.json)
- [Complete historical index](BENCHMARK_HISTORY.md)
