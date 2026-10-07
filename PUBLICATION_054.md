# Extended native repeat 054 on unchanged CAT6 053

**Seven new pairs and all ten combined large-ledger pairs pass the separately predeclared follow-up criteria. This is native diagnostic evidence, not a supported engine upgrade.** The original [053 failed three-pair p50 guard](TRIAL_053.md) remains unchanged and visible. There is no source or binary edit between 053 and this repeat. Its subsequent [live service qualification fails](SERVICE_TRIAL_055.md).

## Fresh and combined results

The new series runs **14 fresh serial fixtures**, seven alternating pairs at **99,000 starting receipt IDs**, with **256 identified 100-row appends per fixture**. Candidate 053 runs first in four new pairs; baseline 050 first in three. Including the original three pairs, each variant runs first exactly five times. Every original and new pair contributes to the combined result. Original 0/50,000-ID controls retain their original three pairs; they are not mislabeled as newly rerun.

The unchanged native driver times only append, excluding setup, external allocations, every-32-append compact/reclaim, stats, cold reopen and full scrubs. Ratios are medians of within-round 053/050 ratios. Timings are milliseconds, summarized as medians of run values; their quotient differs from the paired ratio.

| Metric at 99,000 IDs | 050 median, all ten | 053 median, all ten | Combined paired ratio | Outcome |
|---|---:|---:|---:|---|
| 256-append total | 1371.3344 | 782.2765 | 0.596371 | ✅ Less time |
| Append p99 | 109.6804 | 38.7112 | 0.372025 | ✅ Lower |
| Append p50 | 1.207200 | 1.241875 | 1.032947 | ❌ Slower, within the 1.05 follow-up guard |
| Cold reopen | 223.2912 | 158.1626 | 0.714042 | ✅ Lower |

The new seven-pair p50 ratio is **1.022944** and combined ten-pair ratio **1.032947**. **Every one of the ten large-ledger p50 pairs is slower**; this is not a p50 fix. The new first pair worsens p50 by 11.88%. The new series has **8 candidate appends over 500 ms, four over one second**, versus 14/13 in its baseline. Candidate first-pair p99 is **1023.0267 ms**, baseline **1868.3938 ms**. Earlier zero->500 ms-free observations do not establish elimination of stalls.

Both the new seven-pair criteria and combined criteria use the same 0.90 total/p99, 1.05 p50, 1.10 maximum and 1.10 reopen bounds declared before this repeat. Their pass only permits separate service qualification. It does not overwrite the original failed gate, promote the engine, or establish sustained capacity. New and combined criteria, raw values and small/large catalog classification are preserved in [combined audit](benchmarks/publication-054-repeat/combined-audit.json).

## Correctness and maintenance

**3,584 fresh appends / 358,400 rows**, **42 cold duplicate retries** and **84,403,200 CRC-scrubbed bytes** pass. All 70 new paired frame comparisons preserve equal logical metadata and byte-identical segment frames/payloads. The initial 18 cases plus this repeat total **8,192 native samples, 819,200 rows, 96 cold retries and 149,433,600 CRC-scrubbed bytes**.

The same frozen CAT6 engine subsequently passes **88 debug Rust tests**, supplementing its earlier 88 release tests and all 14 external SQL/source/crash/migration gates. Debug compilation/tests occur after this native repeat finishes and before service timing. The initial 053 ZIP correctly records that debug had not yet been run at that earlier milestone.

Only checked Cargo debug caches from this task were reclaimed to make room. Exact absolute targets, Cargo markers, reparse checks and byte counts are recorded; source, released/frozen binaries, logs and every database fixture remain. No compiler, tests, audits, packaging or Git compression overlap timed workloads. Rebuildable debug cache paths are not benchmark data.

[Repeat policy and hashes](benchmarks/publication-054-repeat/policy.json), [predeclared follow-up criteria](benchmarks/publication-054-repeat/trial-policy.json), [all raw timings/statuses](benchmarks/publication-054-repeat/raw/), [native quantiles/stages](benchmarks/publication-054-repeat/native-audit.json), [full equivalence and paired ratios](benchmarks/publication-054-repeat/new-series-audit.json), [debug log](benchmarks/publication-054-repeat/debug-tests-053.txt), [debug qualification](benchmarks/publication-054-repeat/debug-qualification.json), [fixture SHA256 inventory](benchmarks/publication-054-repeat/fixture-inventory.json), [cache cleanup plan](benchmarks/publication-054-repeat/cache-cleanup-plan.json), [cleanup result](benchmarks/publication-054-repeat/cache-cleanup-result.json), [post-debug reclamation](benchmarks/publication-054-repeat/post-debug-cache-reclamation.json), [additional cleanup](benchmarks/publication-054-repeat/additional-cache-reclamation.json).

Full native database frames are included under `benchmarks/publication-054-repeat/local-native-fixtures/` in the supplemental ZIP. Verify its sidecar SHA256 and internal manifest before extracting into a fresh directory. The frozen 050 and 053 probes are preserved in their existing release assets; executed harness paths are retained verbatim. New reproduction must declare a fresh policy and use new output/fixture directories, not overwrite any prior result. Audit only after timing exits. This repeat adds no fresh DuckDB or other competitor result.

Private immutable [full evidence and database fixtures](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat6-054-repeat-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat6-054-repeat-evidence.zip.sha256). This distinct supplemental asset preserves the report before this final upload-link paragraph and does not replace any supported engine archive.
