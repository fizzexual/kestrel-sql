# 0.3.8: bounded adaptive integer grouping

The archive chooses a direct-address aggregation table when the group-column extrema fit at most 4,096 slots and a conservative 8 MiB query-local budget. Wider domains use the original hash path. SUM and AVG of the same column share one exact i128 reduction; MIN/MAX use narrow arrays and membership/counts are shared. No storage format, publication synchronization, source-checkpoint contract or live-writer policy changed.

Fresh evidence: 54 sequential engine/fixture/round cases, 30 query shapes and 2,970 timed query samples. Each shape ran three rotated engine orders, three warmups and eleven samples. Tables show the median of the three run medians. Rust samples time the direct query API; DuckDB samples include its Python execute/fetch API. JSON framing, fixture creation, result checks and full CRC scrubs are outside Rust timers. Both use one thread and warm OS caches; DuckDB has a 256 MB buffer-manager limit and native compressed storage, while Kestrel reads uncompressed integer segments.

| Fixture | Query | 0.3.7 ms | 0.3.8 ms | DuckDB ms | Paired before/after | vs DuckDB |
|---|---|---:|---:|---:|---:|---|
| dense97 | group_sum | 25.187 | 8.695 | 8.829 | 2.90x | ✅; 3/3 rounds |
| dense97 | group_full | 40.060 | 11.953 | 15.275 | 3.35x | ✅; 3/3 rounds |
| dense97 | filtered_group | 16.897 | 8.291 | 10.876 | 2.08x | ✅; 3/3 rounds |
| dense97 | unordered_control | 3.567 | 4.121 | 4.658 | 0.93x | ✅; 3/3 rounds |
| dense97 | prefix_control | 0.006 | 0.009 | 2.194 | 0.68x | ✅; 3/3 rounds |
| sparse19 | group_sum | 25.682 | 25.370 | 13.844 | 1.01x | ❌; 0/3 rounds |
| sparse19 | group_full | 35.679 | 35.288 | 16.882 | 0.98x | ❌; 0/3 rounds |
| sparse19 | filtered_group | 18.802 | 17.090 | 12.510 | 1.11x | ❌; 0/3 rounds |
| sparse19 | unordered_control | 3.590 | 3.579 | 4.754 | 1.03x | ✅; 3/3 rounds |
| sparse19 | prefix_control | 0.006 | 0.006 | 2.073 | 1.08x | ✅; 3/3 rounds |
| cardinality5003 | group_sum | 47.361 | 46.054 | 31.253 | 1.00x | ❌; 0/3 rounds |
| cardinality5003 | group_full | 88.343 | 70.790 | 43.120 | 0.88x | ❌; 0/3 rounds |
| cardinality5003 | filtered_group | 33.157 | 35.807 | 23.966 | 1.07x | ❌; 0/3 rounds |
| cardinality5003 | unordered_control | 4.720 | 5.504 | 5.169 | 0.99x | ❌; 2/3 rounds |
| cardinality5003 | prefix_control | 0.007 | 0.007 | 2.500 | 0.93x | ✅; 3/3 rounds |
| nyc | month | 0.005 | 0.010 | 27.525 | 0.55x | ✅; 3/3 rounds |
| nyc | day | 0.006 | 0.007 | 4.537 | 0.87x | ✅; 3/3 rounds |
| nyc | hour | 0.005 | 0.010 | 1.596 | 0.58x | ✅; 3/3 rounds |
| nyc | zone | 1.833 | 2.707 | 4.119 | 0.68x | ✅; 2/3 rounds |
| nyc | all_zones | 118.073 | 42.434 | 50.420 | 2.99x | ✅; 2/3 rounds |
| 10000000 | group_sum | 336.769 | 141.651 | 103.608 | 2.56x | ❌; 1/3 rounds |
| 10000000 | group_full | 540.061 | 187.781 | 178.657 | 2.88x | ❌; 1/3 rounds |
| 10000000 | filtered_group | 233.647 | 112.301 | 125.753 | 2.05x | ✅; 2/3 rounds |
| 10000000 | unordered_control | 62.689 | 57.417 | 50.288 | 1.03x | ❌; 0/3 rounds |
| 10000000 | prefix_control | 0.005 | 0.007 | 10.800 | 1.21x | ✅; 3/3 rounds |
| 100000000 | group_sum | 3660.681 | 1153.757 | 1230.547 | 3.04x | ✅; 2/3 rounds |
| 100000000 | group_full | 5504.002 | 1693.750 | 1895.869 | 3.25x | ✅; 3/3 rounds |
| 100000000 | filtered_group | 2345.477 | 1124.481 | 1329.851 | 2.16x | ✅; 3/3 rounds |
| 100000000 | unordered_control | 528.335 | 552.189 | 516.199 | 0.87x | ❌; 0/3 rounds |
| 100000000 | prefix_control | 0.009 | 0.015 | 131.153 | 0.55x | ✅; 3/3 rounds |

Checkmarks describe these measured medians only. A narrow median win, mixed round results or microsecond prefix timing is not a general database ranking. Sparse and higher-cardinality losses are included.

## Short paired controls

Controls that appeared slower were repeated in 21 alternating pairs using exact-byte independent archive copies. Each pair contains eleven timed samples per engine. Candidate/baseline above 1 means slower; the raw original three-round outcomes remain visible.

| Fixture | Query | Before ms | After ms | Paired candidate/baseline |
|---|---|---:|---:|---:|
| dense97 | group_full | 50.360 | 15.398 | 0.309 |
| dense97 | unordered_control | 5.053 | 5.291 | 1.047 |
| dense97 | prefix_control | 0.006 | 0.007 | 1.014 |
| sparse19 | group_full | 49.848 | 47.941 | 0.990 |
| cardinality5003 | group_full | 83.353 | 79.598 | 0.972 |
| nyc | zone | 1.840 | 1.854 | 0.997 |
| nyc | all_zones | 123.278 | 40.764 | 0.325 |
| nyc | day | 0.008 | 0.007 | 0.907 |
| 100M; seven pairs | unordered_control | 663.694 | 590.719 | 0.972 |

## Correctness and recovery

All 63 Rust tests pass in debug and release, with formatting and default/fault-feature Clippy checks. New cases cover signed extrema, holes, empty/filtered groups, exact wide sums, output aliases/limits, pinned snapshots, compaction/reopen, metadata-bound rejection, allocation limits, hash fallback and the 100,000-group result budget. Five hundred seeded queries match both DuckDB and SQLite over eight overlapping sorted runs.

The current binaries also passed 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent forced kills, 14 source publication failures and eight source pipeline kills. Exact acknowledged receipts, output/source positions, retries and full scrubs are checked after reopen. The current Parquet source pipeline proof is linked below. These are live-filesystem process/IO-failure tests, not physical power failures.

A final boundary check found an existing CLI panic for SUM results outside the serde_json::Value integer range: both 0.3.7 and the first candidate failed positive and negative three-row extreme sums. The CLI and test bridge now serialize typed results directly, keeping exact i128 numeric tokens without changing dependency features. Wide archive/RAM CLI results, bridge error continuity and retry/reopen are tested. The affected final CLI/bridge differential and publication/kill checks were rerun. The timed group probe is byte-identical to the final build, and every query-library source file is unchanged by this framing fix; no heavy build overlapped timing.

## Preserved experiments and limits

The initial Cell-array candidate and its raw comparison are preserved. Its “sparse17” generator used `(i*17)%17`, so that fixture was actually a single-key group. Its audit explicitly corrects the label. The current sparse fixture uses 19 distinct widely spaced keys and independently checks distinct count. Initial lockfile-version, pinned-test lifetime, Clippy, sandbox-library, baseline-validator and adapter-LTO failures remain in the build/harness evidence.

This experiment measures core read queries. It establishes no new requests/s result or sustained mixed-write service envelope. Historical write stalls, durability boundaries, SQL/NULL/type limitations and missing distributed/production qualification remain. The last fresh multi-server matrix is still 0.3.1.

## Reproduce and inspect

Run serially on this computer: `python benchmarks/checks_038.py`, build the matched preserved probe with `python benchmarks/build_group_baseline_038.py`, then run `group_compare_038.py` once for each scope (`small`, `nyc`, `large`) with separate fresh output names. The large and NYC scopes reuse the retained locally generated datasets described in their reports. Install/use the pinned local DuckDB libraries. Never run build, test, packaging or other heavy jobs concurrently with query timing. The scripts refuse to overwrite completed comparison reports.

- [Current audit and every before/after value](benchmarks/group-038-audit.json)
- [Corrected 1M-row shapes and raw samples](benchmarks/group-038-typed-comparison.json)
- [10M/100M-row raw samples](benchmarks/group-038-large-comparison.json)
- [Real taxi-data raw samples](benchmarks/group-038-nyc-comparison.json)
- [Short paired controls](benchmarks/group-038-paired-controls.json)
- [100M-row paired unordered control](benchmarks/group-038-large-paired-control.json)
- [Separate stage profiles](benchmarks/group-038-profiles.json)
- [SQL differential checks](benchmarks/archive-038-verification.json)
- [Final CLI/bridge wide-JSON fix and preserved failures](benchmarks/wire-038-audit.json)
- [Final CLI differential rerun](benchmarks/archive-038-wire-verification.json)
- [Final bridge publication/corruption rerun](benchmarks/publication-038-wire-faults.json)
- [Final bridge forced-kill rerun](benchmarks/group-038-wire-recovery.json)
- [Publication/corruption proof](benchmarks/publication-038-faults.json)
- [Concurrent kills](benchmarks/group-038-recovery.json)
- [Source failures and kills](benchmarks/source-038-faults.json)
- [Current Parquet pipeline](portfolio/source-pipeline-038-results.json)
- [Serial correctness order](benchmarks/correctness-038-run-order.json)
- [Initial candidate and fixture correction](benchmarks/group-038-cell-trial-audit.json)
- [All earlier wins, losses and downloads](BENCHMARK_HISTORY.md)
