# Catalog encoder profiles 065 and 066

**The independent 066 replication passes all 43 checks.** Reusing the JSON output buffer reduces paired encoding time by **21.1% / 22.8%** on the two large fixed checkpoints. **The original 065 cohort still fails one calibration check** and remains preserved. These are exact-byte CPU/allocation models on released **0.3.16**, with no engine change, SQL performance qualification or new supported release. [064 compaction failure](COMPACTION_064.md), [063 batching results](BATCHING_063.md), [all benchmark history](BENCHMARK_HISTORY.md).

The released checkpoint serializer already borrows committed/new receipt maps; it does not clone the entire ledger during encoding. Local locked serde_json **1.0.151** source starts `to_vec` with a 128-byte vector. [The library source](https://docs.rs/serde_json/1.0.151/src/serde_json/ser.rs.html) and [writer API](https://docs.rs/serde_json/1.0.151/serde_json/fn.to_writer.html) support comparing output-buffer strategies while retaining the same serializer. Allocation-aware capacity traces here count changes to vector capacity; they are not allocator call counts or measured bytes copied.

Three original released-core checkpoints are copied from the preserved 064 baseline-A stores. They contain **250 / 50,250 / 99,250 receipts** and **42,419 / 8,243,311 / 16,291,871 JSON bytes**. Their original envelopes, CRCs and SHA-256 values are checked before extraction. The typed `CatalogOutput`, borrowed `CombinedBatches` serializer and `BatchRecord` definitions are extracted byte-for-byte from released source. Removing the final receipt into the added map reconstructs the original checkpoint's committed-then-added order, preserving every original stored byte. Parsing does not replace the engine's recovery validator; this is solely an encoder model. [Input/source provenance](benchmarks/encoder-profiles-065-066/065/input-provenance.json), [extracted serializer](benchmarks/encoder-profiles-065-066/065/released_encoder_models.rs), [build](benchmarks/encoder-profiles-065-066/065/build.json).

All labels use **one identical frozen executable** and the same released serde dependencies. A and B use the same baseline mode. `reserve_exact` allocates a fresh vector with the known fixed output length on every iteration; this oracle-sized reservation is an idealized model, not a deployable prediction strategy. `reuse` starts with an empty vector for each case and retains its capacity between encodes. Its first allocation is inside the first timer. Every case serializes the same input 33 times, including that cold first encode, without warmups. Loading/deserialization, exact output comparison and dropping the output are outside timers. No database publication, sync, query, network request or throughput is measured.

The 065 cohort has four Latin-square rounds: **48 serial cases / 1,584 encodes**. Both models pass their eight large-input goals and twenty guards, but identical B/A first-encode time at 99,250 receipts is **1.100009428487**, beyond the declared **1.10** limit. Rounding it to 1.1000 does not turn the failure into a pass. Its model advance decisions stay false. The separate 066 replication freezes **twelve rounds / 144 fresh cases / 4,752 encodes**, using the same executable, inputs, methods and thresholds. It replaces no original case. [Original policy/audit](benchmarks/encoder-profiles-065-066/065/audit.json), [replication policy](benchmarks/encoder-profiles-065-066/066/policy.json), [replication provenance](benchmarks/encoder-profiles-065-066/066/replication-provenance.json), [replication audit](benchmarks/encoder-profiles-065-066/066/audit.json).

The replication policy's human aggregation sentence accidentally retains the word “four.” Its case list, twelve-round declaration, reason and hash-recorded auditor were generated before timing and specify all twelve matched rounds. A separate note records the text error before final results/ratio analysis, leaving raw policy, source, case order and thresholds unchanged. Reproduction and this report use the frozen twelve-round code, and keep this documentation defect visible. [Aggregation text note](benchmarks/encoder-profiles-065-066/066/aggregation-text-note.json).

| Cohort | Actual receipts | Label | Total 33 encodes ms | p50 ms | p99 ms | First encode ms | Peak working set MiB |
|---|---:|---|---:|---:|---:|---:|---:|
| 065 | 250 | baseline_a | 2.1486 | 0.05845 | 0.11173 | 0.10575 | 4.031 |
| 065 | 250 | baseline_b | 2.0974 | 0.05870 | 0.09593 | 0.09720 | 4.029 |
| 065 | 250 | reserve_exact | 1.9668 | 0.05770 | 0.07420 | 0.07640 | 4.025 |
| 065 | 250 | reuse | 1.9986 | 0.05745 | 0.09351 | 0.09975 | 4.029 |
| 065 | 50,250 | baseline_a | 532.8927 | 15.99610 | 18.89708 | 16.86390 | 28.928 |
| 065 | 50,250 | baseline_b | 545.6419 | 15.86110 | 21.16159 | 16.57930 | 28.945 |
| 065 | 50,250 | reserve_exact | 487.6192 | 14.12055 | 19.53308 | 15.50565 | 27.742 |
| 065 | 50,250 | reuse | 436.8669 | 12.81655 | 16.87503 | 16.01995 | 28.900 |
| 065 | 99,250 | baseline_a | 1089.9104 | 32.93830 | 38.57851 | 30.76410 | 52.770 |
| 065 | 99,250 | baseline_b | 1085.3428 | 32.77165 | 38.48441 | 34.24385 | 52.766 |
| 065 | 99,250 | reserve_exact | 922.8817 | 27.29320 | 34.11191 | 28.58375 | 51.234 |
| 065 | 99,250 | reuse | 852.7264 | 25.40710 | 31.39714 | 33.00765 | 52.719 |
| 066 | 250 | baseline_a | 2.1113 | 0.06145 | 0.09848 | 0.10770 | 4.033 |
| 066 | 250 | baseline_b | 2.1505 | 0.06150 | 0.10097 | 0.10695 | 4.031 |
| 066 | 250 | reserve_exact | 2.0229 | 0.06010 | 0.08063 | 0.08190 | 4.021 |
| 066 | 250 | reuse | 2.0166 | 0.05950 | 0.09368 | 0.10825 | 4.031 |
| 066 | 50,250 | baseline_a | 565.5374 | 16.83070 | 21.31681 | 17.49080 | 28.949 |
| 066 | 50,250 | baseline_b | 552.0297 | 16.51410 | 19.58573 | 17.60570 | 28.938 |
| 066 | 50,250 | reserve_exact | 482.1811 | 14.33530 | 17.59199 | 14.57145 | 27.742 |
| 066 | 50,250 | reuse | 442.0077 | 13.23925 | 17.60244 | 17.77410 | 28.881 |
| 066 | 99,250 | baseline_a | 1136.1617 | 33.74420 | 39.66181 | 34.33670 | 52.770 |
| 066 | 99,250 | baseline_b | 1128.3340 | 33.38000 | 39.41003 | 33.87465 | 52.770 |
| 066 | 99,250 | reserve_exact | 950.4299 | 28.28845 | 34.68533 | 28.61245 | 51.234 |
| 066 | 99,250 | reuse | 872.9216 | 25.87575 | 33.65126 | 34.98775 | 52.701 |

Ratios below are medians of within-round ratios, not ratios of the displayed medians. Type 7 p99 includes all 33 samples, including the first encode. Warm-only medians are diagnostic and do not replace the primary metrics. First-encode and peak-memory guards accompany throughput-free CPU timing; full-process peak includes input parsing and verification.

| Cohort | Actual receipts | Comparison | Total ratio | p50 ratio | p99 ratio | First ratio | Peak working-set ratio |
|---|---:|---|---:|---:|---:|---:|---:|
| 065 | 250 | identity_b_a | 0.988475 | 1.003686 | 0.934293 | 0.999170 | 0.999031 |
| 065 | 250 | reserve_exact_a | 0.929938 | 0.980726 | 0.728872 | 0.798781 | 0.998547 |
| 065 | 250 | reuse_a | 0.922137 | 0.969203 | 0.872221 | 0.986194 | 0.999516 |
| 065 | 250 | reserve_exact_b_diagnostic | 0.943385 | 0.975304 | 0.785996 | 0.795753 | 0.998063 |
| 065 | 250 | reuse_b_diagnostic | 0.945886 | 0.975041 | 0.994868 | 1.022351 | 0.999516 |
| 065 | 50,250 | identity_b_a | 1.001861 | 0.991446 | 1.050282 | 0.931193 | 1.000540 |
| 065 | 50,250 | reserve_exact_a | 0.877582 | 0.853574 | 0.891957 | 0.936214 | 0.958949 |
| 065 | 50,250 | reuse_a | 0.834195 | 0.813503 | 0.943643 | 0.962107 | 0.998785 |
| 065 | 50,250 | reserve_exact_b_diagnostic | 0.893698 | 0.893254 | 0.861104 | 0.992978 | 0.958367 |
| 065 | 50,250 | reuse_b_diagnostic | 0.828707 | 0.817726 | 0.903127 | 0.969420 | 0.998246 |
| 065 | 99,250 | identity_b_a | 1.010909 | 0.997305 | 0.998688 | 1.100009 | 0.999926 |
| 065 | 99,250 | reserve_exact_a | 0.857919 | 0.836479 | 0.824136 | 0.913170 | 0.970908 |
| 065 | 99,250 | reuse_a | 0.799674 | 0.787017 | 0.791441 | 1.065718 | 0.999038 |
| 065 | 99,250 | reserve_exact_b_diagnostic | 0.848693 | 0.838761 | 0.875299 | 0.849073 | 0.970980 |
| 065 | 99,250 | reuse_b_diagnostic | 0.780529 | 0.785767 | 0.796034 | 0.949385 | 0.999149 |
| 066 | 250 | identity_b_a | 1.011604 | 1.005101 | 0.999608 | 0.993036 | 0.999516 |
| 066 | 250 | reserve_exact_a | 0.942303 | 0.976983 | 0.794529 | 0.747532 | 0.997577 |
| 066 | 250 | reuse_a | 0.948543 | 0.979521 | 0.960609 | 1.014443 | 0.999516 |
| 066 | 250 | reserve_exact_b_diagnostic | 0.939367 | 0.956608 | 0.787793 | 0.737949 | 0.997093 |
| 066 | 250 | reuse_b_diagnostic | 0.951368 | 0.964838 | 0.939996 | 1.007175 | 0.999517 |
| 066 | 50,250 | identity_b_a | 0.985611 | 0.995305 | 0.986678 | 1.001288 | 1.000000 |
| 066 | 50,250 | reserve_exact_a | 0.861335 | 0.855666 | 0.826098 | 0.849349 | 0.958305 |
| 066 | 50,250 | reuse_a | 0.788827 | 0.785717 | 0.811294 | 1.054939 | 0.997908 |
| 066 | 50,250 | reserve_exact_b_diagnostic | 0.877978 | 0.869026 | 0.877346 | 0.839739 | 0.958626 |
| 066 | 50,250 | reuse_b_diagnostic | 0.802541 | 0.791755 | 0.877413 | 0.986327 | 0.997908 |
| 066 | 99,250 | identity_b_a | 0.988416 | 0.994062 | 0.959894 | 0.980725 | 1.000000 |
| 066 | 99,250 | reserve_exact_a | 0.837738 | 0.836780 | 0.829394 | 0.823498 | 0.970908 |
| 066 | 99,250 | reuse_a | 0.772018 | 0.765531 | 0.809994 | 1.036676 | 0.998705 |
| 066 | 99,250 | reserve_exact_b_diagnostic | 0.844908 | 0.849297 | 0.868544 | 0.845157 | 0.970908 |
| 066 | 99,250 | reuse_b_diagnostic | 0.785855 | 0.779593 | 0.862430 | 1.044234 | 0.998779 |

Each large checkpoint requires at least 10% lower total encoding time and p50. Every checkpoint permits at most 10% higher p99, first-encode time and full-process peak working set; the small checkpoint also permits at most 5% higher p50. All fifteen identical B/A ratios must stay in 0.90-1.10. Every own goal/guard plus every identity check must pass before the model justifies an engine buffer experiment. Model/B remains diagnostic. No threshold is changed after timing.

| Cohort | Goals passed | Guards passed | Identity checks passed | Justifies an engine experiment |
|---|---:|---:|---:|---|
| 065 | ✅ 8/8 | ✅ 20/20 | ❌ 14/15 | ❌ |
| 066 | ✅ 8/8 | ✅ 20/20 | ✅ 15/15 | ✅ |

For 066, reuse changes displayed p50 from **16.8307 to 13.2393 ms** at 50,250 receipts and **33.7442 to 25.8758 ms** at 99,250. Paired p50 ratios are **0.7857 / 0.7655**; paired total ratios **0.7888 / 0.7720**. First-encode ratios are **1.0549 / 1.0367**, so first encodes are slower despite faster repeated encoding. Peak working-set ratios stay near 1. `reserve_exact` has total ratios **0.8613 / 0.8377**, but uses an unavailable future-length oracle. These observations support a bounded engine experiment; they do not predict durable append p99 or requests/s.

The exact capacity diagnostics show:

| Receipts | Original 128-byte buffer growths | Final capacity bytes | Exact reservation growths | First reuse growths | Warm reuse growths |
|---:|---:|---:|---:|---:|---:|
| 250 | 9 | 65,536 | 0 | 14 | 0 |
| 50,250 | 16 | 8,388,608 | 0 | 21 | 0 |
| 99,250 | 17 | 16,777,216 | 0 | 22 | 0 |

These excluded diagnostics use a counting writer, while timers use ordinary vectors. In-place allocator growth could avoid copying; capacity events alone do not prove an allocation count or copying cost. The timed comparisons directly measure each encoder model with normal buffers.

Across both cohorts, **6,336 timed encodes** match **51,907,893,312 output bytes** exactly to the preserved original checkpoint bodies. A separate 48-case byte/JSON smoke covers quotes, backslashes, controls, Unicode and wide integers, followed by nine real-input smoke runs and three excluded capacity traces. The replication inherits those diagnostics and build without rerunning or counting them twice. All 192 process statuses, raw samples, capacities, peak working-set/commit counters and stderr files are preserved. [065 raw](benchmarks/encoder-profiles-065-066/065/raw/), [066 raw](benchmarks/encoder-profiles-065-066/066/raw/), [excluded diagnostics](benchmarks/encoder-profiles-065-066/065/diagnostics/).

No new database crash/retry suite is run here because no database engine is changed. Released-core and 064 correctness/recovery evidence stays separate; serializer byte equality is not durability qualification. A real buffer change must bound retained memory, avoid copying writer buffers into reader snapshots, handle growing/changing catalogs, pass byte-level oracles and full crash/source replay checks, then satisfy native/service performance guards. [Next work](benchmarks/encoder-profiles-065-066/066/NEXT_WORK.md), [reproduction](benchmarks/encoder-profiles-065-066/066/REPRODUCE.md).

All builds, capacity diagnostics, audits, cleanup and packaging run outside timers. Both cohorts' structured pre/post process checks record zero task-owned heavy/database processes. After all timing, two signed 064 Cargo debug caches are reclaimed: **753,764,494 file bytes**, with all measured frozen binaries, source, logs, native stores and prior private archives checked and retained. Release libraries remain. [Cache proof](benchmarks/encoder-profiles-065-066/066/cache-preflight.json), [resolved deletion plan](benchmarks/encoder-profiles-065-066/066/cache-plan.json), [result](benchmarks/encoder-profiles-065-066/066/cache-result.json).

No fresh DuckDB/PostgreSQL comparison, SQL speed claim, distributed-scale qualification or production-readiness claim is made. Supported 0.3.16, every historical asset and the issued morning report remain unchanged. Both raw cohorts and all exact inputs are preserved in the supplemental archive.

Private immutable [full encoder evidence and inputs](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-065-066-encoder-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-065-066-encoder-evidence.zip.sha256). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.
