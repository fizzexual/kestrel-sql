# Fresh recovery comparison077: large anchor gains, adoption guards still fail

The already qualified 076 reader reduces anchor-terminated recovery median latency by about 51–52% on 50K/99K original receipt histories in this fresh old/old/new metadata cohort. All four declared large anchor goals pass, with corresponding identical-control calibration and6/6 round wins at each size. **Four of 53 candidate guards and two of 60 A/A checks fail. No engine adoption or supported release change.** Earlier075 failed CAT4 comparison is preserved and is not superseded.

This cohort measures metadata restart/publication behavior only. It compares unchanged075 hybrid controls with the qualified 076 reader through the same bench075 entry point; all cases use hybrid protocol. There is no new DuckDB, PostgreSQL, SQL, network or requests/s comparison. The latest supported engine stays 0.3.16. [075 baseline and failed adoption](HYBRID_CYCLES_075.md), [076 changed-reader correctness](ANCHOR_REUSE_076.md), [earlier competitor evidence](SERVICE_047.md) and [adoption assessment](ADOPTION_STATUS.md) remain available.

## Fresh before/after recovery

Values below are medians of six per-case path medians. Ratios are medians of six matched per-round candidate/A ratios, **not division of displayed medians**. Each path has three same-process fresh opens per case; OS cache may be warm. Anchor after 31 terminates at the original anchor. After63 is a checkpoint plus 31 deltas, not anchor termination.

| Actual original receipts | Anchor31 p50 before → after (ms) | Matched C/A | A/A B/A | Anchor31 p99 before → after (ms) | Matched C/A | A/A B/A |
|---:|---:|---:|---:|---:|---:|---:|
| 126 | 4.667 → 4.236 | 0.944242 | 1.015856 | 5.311 → 4.860 | 0.904694 | 0.991711 |
| 50,126 | 120.183 → 57.862 | 0.484639 | 1.011437 | 123.266 → 62.138 | 0.493326 | 1.028139 |
| 99,126 | 238.603 → 114.638 | 0.481159 | 1.005975 | 246.723 → 119.984 | 0.486313 | 1.016872 |

Large anchor p50 goal<=0.80, p99 goal<=0.85; all corresponding A/A checks require 0.90..1.10. Both sizes pass all four goals and each metric favors candidate in 6/6 matched rounds. Small anchor paths are guarded<=1.10, not given a speed goal. Prior native probes showed the changed anchor-terminated path goes from 3 full body reads/2 parses to1/1, scoped to one open; checkpoint-terminated paths retain1/1. Magic/CRC/schema/receipt/source validation and publication bytes are unchanged.

| Actual receipts | Checkpoint32 p50 before → after (ms); ratio | Checkpoint+31 deltas63 p50 before → after (ms); ratio | Checkpoint64 p50 before → after (ms); ratio | All-open p99 before → after (ms); ratio |
|---:|---:|---:|---:|---:|
| 126 | 0.624 → 0.640; 1.019072 | 4.529 → 4.447; 0.985974 | 0.717 → 0.754; 1.042787 | 5.490 → 5.532; 1.065513 |
| 50,126 | 53.893 → 55.178; 1.038003 | 58.096 → 58.464; 1.004871 | 53.669 → 55.680; 1.050133 | 122.980 → 64.463; 0.529877 |
| 99,126 | 105.457 → 112.362; 1.058883 | 106.006 → 115.287; 1.079003 | 105.092 → 108.417; 1.014750 | 245.745 → 121.087; 0.502422 |

All 12 large-history checkpoint p50/p99 guards and their A/A checks pass. The small checkpoint+31 delta p99 guard fails at 1.102692. Small checkpoint32 p99 candidate/A looks lower, but its A/A 0.880569 fails calibration; it is not a qualified benefit. Full path metrics, raw samples and per-round ratios are in [model-audit.json](benchmarks/recovery-compare-077/model-audit.json).

## Publication behavior and preserved failures

| Actual receipts |64 publication sum before → after (ms); matched ratio | Publication p50 before → after (ms); matched ratio | Source p99 matched ratio; A/A | Retained bytes / current reachable bytes (each variant) |
|---:|---:|---:|---:|---:|
| 126 | 109.615 → 108.934; 1.011371 | 1.616 → 1.588; 1.012223 | 0.930018; 0.982770 | 61,051 / 34,596 |
| 50,126 | 187.637 → 181.348; 0.985611 | 1.819 → 1.700; 0.942803 | 1.046372; 1.036275 | 8,262,178 / 8,235,585 |
| 99,126 | 246.918 → 261.854; 1.061448 | 1.739 → 1.856; 1.062406 | 1.054559; 1.059560 | 16,310,654 / 16,284,071 |

Exact retained and current reachable bytes are identical across all variants. Both publish66 synchronized files over 64 commits, plus one synchronized migration;67 full history files retained per store,3 current files reachable at the final checkpoint. This reader change saves no metadata bytes or syncs. All source-p99, migration and memory guards pass;50K migration ratio1.345221 is near its1.35 limit. Full-process memory includes setup and validation, not recovery alone.

All failed policy checks, without excluding outliers or moving limits:

| Outcome | Actual receipts | Metric | Matched ratio | Declared limit |
|---|---:|---|---:|---|
| ❌ guard | 126 | checkpoint_delta63_p99_ms | 1.102691976 | <=1.1 |
| ❌ identity | 126 | max_ms | 0.899120542 | [0.9, 1.1] |
| ❌ identity | 126 | checkpoint32_p99_ms | 0.880569405 | [0.9, 1.1] |
| ❌ guard | 99,126 | p50_ms | 1.062405728 | <=1.05 |
| ❌ guard | 99,126 | p99_ms | 1.119724013 | <=1.1 |
| ❌ guard | 99,126 | max_ms | 1.185102163 | <=1.1 |

✅4/4 large anchor goals; ✅49/53 candidate guards; ✅58/60 identical-control checks. ❌Full comparison qualification fails. The 99K publication p50/p99/max failures have passing corresponding A/A calibration; they remain material measured regressions. No causal mechanism is established by this cohort even though publication/source/write code is unchanged. Small-store maximum and checkpoint32 p99 controls drift outside the declared interval. All individual observations remain included.

## Workload, correctness and retry/crash evidence

Fresh timed cohort: 2026-10-07T15:34:59.148958+00:00 through 2026-10-07T15:36:37.202919+00:00. Six balanced orders across three sizes,54 owned children,3,456 actual publications,432 source intervals,648 recovery opens. Original gen129 anchors contain 126, 50,126 and 99,126 receipts; each store adds 56 ordinary and8 source receipts across two complete32 publication cycles. All files retained. Every child was waited; post-timing native process inventory is empty. No compilation/tests/audit/package/Git ran concurrently with timers. No observed case rerun or disk stop occurred.

Before the freeze, six toy cases through the exact old/new bench075 entry point at 7/8/9 receipts passed full-file/ledger/recovery/source/sync checks. Those times are not controls. After timing, independent unchanged Python code fully decoded all 67 canonical files at each of three sizes (201 files), reconstructed exact logical edits and source positions, then full-SHA compared all 3,618 timed file instances across54 stores. All generations, receipt digests, source positions, retry/collision no-IO flags, native summaries, stage bounds, migration bytes, sync counts, input and binary hashes and balanced order pass. Current metadata files and all retained predecessor versions match byte-for-byte between old and new readers.

Durable retry/crash qualification is the separately completed 076 prerequisite: 49 debug+49 release tests;15 injected errors,15 controlled owned process kills,30 independent valid/bad-CRC corruption cases and exact retries/source resumptions pass.076 independently decoded 195 historical heads and its201 original publication-history files matched074. **Those native tests/cuts were not rerun in 077.** A process kill/error simulation is not physical-power-loss qualification. [Copied076 proof](benchmarks/recovery-compare-077/prerequisites/076-qualification-results.json) and [complete076 evidence](ANCHOR_REUSE_076.md) distinguish it from the 54 new timed cases.

## Measured stages and remaining work

No publication exceeded 500 ms in this fresh cohort. The largest publication was 28.3668 ms in 06-r0-99000-hybrid, sequence 32. This does not erase earlier multi-second stalls; those remain in 075 and older reports. Each current raw sample records encode/write/sync/rename and outer time. The residual includes batch/digest/source clone and other overhead, not a measured physical cause.

[Bottleneck profile](benchmarks/recovery-compare-077/bottleneck-profile.json) retains all stages,25 slowest publications/opens, per-size memory and per-round outcomes. Checkpoint recovery still validates one full old anchor and source ledger; large checkpoint medians remain about 55/110ms. Source publication still clones/validates the full ledger. Next inspect the measured99K publication regressions, then consider separately qualified incremental source validation or another structural change. No weaker validation, selected metric substitution, cold-cache claim or supported promotion follows from the anchor win.

## Preserved evidence and reproducibility

- [Frozen policy and gates](benchmarks/recovery-compare-077/policy.json), [exact order/source/input/binary freeze](benchmarks/recovery-compare-077/cohort-policy.json), [all 54 raw cases](benchmarks/recovery-compare-077/raw), [audit](benchmarks/recovery-compare-077/model-audit.json), [fixture inventory](benchmarks/recovery-compare-077/fixture-inventory.json).
- [Binary derivation](benchmarks/recovery-compare-077/binary-provenance.json), [unchanged full decoder proof](benchmarks/recovery-compare-077/source-finalization.json), [reproduction layout](benchmarks/recovery-compare-077/REPRODUCE.md), [next work](benchmarks/recovery-compare-077/NEXT_WORK.md).
- Three complete077 ZIP parts preserve every full timed/smoke/input fixture and all raw/source/binary/crate/proof files. Restore all parts together. Archive hashes/internal manifests and local/private-Git proofs are linked after finalization. [075 complete private release](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16); [076 complete private Git archive](benchmarks/kestrel-sql-development-076-anchor-reuse-evidence.zip).
- Only the completed 076 compiler cache (853 files,239,344,988 logicalbytes) was reclaimed after full archive and122 old release digest checks. All source/binary/crates/raw/fixtures/archives remain retained. The first cache verifier hash assertion stopped before deletion; raw Git--no-filters corrected it and the failure is preserved. No benchmark case rerun.

There is no new engine release, deployment, competitor score or production qualification. All historical baselines and unsuccessful trials stay visible; the morning report remains frozen.
