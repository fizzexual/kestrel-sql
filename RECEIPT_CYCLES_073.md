# Growing receipt checkpoint benchmark 073

The separate receipt-page model passes all logical-history checks and all four declared large-history goals, but **fails adoption: 11 of 26 guards and six of 30 A/A calibration checks fail. Supported KestrelSQL 0.3.16 is unchanged.** This measures receipt metadata persistence, not SQL/data-segment/service performance. The candidate remains development-only and is not advanced to engine integration.

A/B are identical CAT4 metadata controls with the released borrowed receipt serializer and bounded 32-catalog rule. C uses the qualified [072 page protocol](RECEIPT_PAGES_072.md). Every case starts from an unchanged real generation-129 checkpoint with 126/50,126/99,126 receipts, then commits 64 actual new IDs (56 ordinary, eight contiguous source intervals) in two complete checkpoint/delta cycles. CAT4 performs 31 deltas then a full reset, twice; pages update the tail/root on each commit. Segment references are held identical and opaque: **no data segment is written or queried**. The common instrumented file helper is not the entire released Archive IO path.

Six rounds use every A/B/C permutation once per history, balanced variant/size positions and 3/3 A/B relative order. All source/binary/input/plan/policy/oracle/harness hashes were frozen before timers. One owned child at a time; no compilation, audit, packaging or Git ran during the cohort. Timed cohort: 2026-10-07T12:58:54.596362+00:00 → 2026-10-07T13:01:50.072127+00:00. Every case, tail and failure is retained; no case was rerun.

## Before/after charged publication time

Each displayed time is the independent median of six **64-publication sums**, in milliseconds. The C/A and B/A columns are the medians of six **matched per-round ratios**; they are not obtained by dividing display medians. The striking 99K A/B display difference is a reason to inspect calibration and individual rounds, not choose the favorable denominator. Migration and recovery are separately measured below.

| Initial receipts | CAT4 A display ms | CAT4 B display ms | Pages C display ms | Matched C/A | Matched B/A |
|---:|---:|---:|---:|---:|---:|
| 126 | 122.7588 | 98.9093 | 201.0709 | 2.112984 | 1.019651 |
| 50,126 | 343.9870 | 339.9154 | 320.3772 | 0.892041 | 1.046259 |
| 99,126 | 2734.8204 | 495.6590 | 704.5525 | 0.603617 | 0.871749 |

- ✅50,126: matched charged publication time is 10.8% lower (C/A 0.892041); total A/A 1.046259 passes. Four of six rounds favor C, two are slower. This scoped metadata result does not override p50/migration/tail-control failures.
- ⚠️99,126: descriptive C/A 0.603617 passes the numerical speed goal, but total A/A 0.871749 fails calibration. Four rounds favor C; the first two are slower. No qualified 39.6% causal improvement is claimed.
- ❌126: total C/A2.112984; C is slower in all six rounds. Publication p50 also regresses across all histories.

- 126 C/A charged publication totals by round: 1.249063, 2.067258, 1.303077, 2.535835, 2.192012, 2.158710.
- 50,126 C/A charged publication totals by round: 1.013538, 1.199862, 0.427928, 0.731353, 0.968802, 0.815281.
- 99,126 C/A charged publication totals by round: 1.460972, 1.101850, 0.324400, 0.229918, 0.092978, 0.882834.

## Latency, migration and recovery tradeoffs

All values below are matched C/A ratios, lower is better. P50 uses all 64 publications, not a separately measured ordinary-only subset. Recovery is a fresh model open after dropping writer state, three opens at each of publications 31/32/63/64; OS cache may be warm. Migration includes input parse/validation, encoding and **every** initial file sync.

| Initial receipts | Publication p50 | Publication p99 | Maximum | Migration | Recovery p99 | Retained directory bytes |
|---:|---:|---:|---:|---:|---:|---:|
| 126 | 2.147662 | 1.917343 | 1.882885 | 1.389385 | 0.824027 | 11.334865 |
| 50,126 | 2.387633 | 0.244880 | 0.225726 | 2.048555 | 0.977224 | 0.561795 |
| 99,126 | 2.509046 | 0.170467 | 0.167912 | 1.407529 | 0.967531 | 0.464024 |

❌P50 and migration fail at every history. Pages require 128 synced files across 64 publications versus64 for CAT4; initialization syncs 2/99/195 files versus one. Small-history total, p99/max/source-p99 and retained bytes also fail. Recovery and peak-memory guards pass across all histories. Large p99/max reductions remain descriptive where their A/A controls fail. Source-p99 was a candidate guard, but was not in the declared identity metric list; its 50K B/A drift1.232944 must be included before making any future source-tail causal claim.

## Storage accounting: retained evidence versus live metadata

✅Both large retained-directory goals pass: C/A 0.561795 at 50K and 0.464024 at 99K. These directories deliberately keep **superseded** catalogs/pages as benchmark evidence. They are not compacted/reclaimed live-store space. Current reachable metadata is larger for pages:

| Initial receipts | Retained CAT4 A B | Retained pages C B | Final reachable CAT4 B | Final reachable pages B | Reachable C/A |
|---:|---:|---:|---:|---:|---:|
| 126 | 173,413 | 1,965,613 | 33,350 | 36,516 | 1.094933 |
| 50,126 | 24,845,811 | 13,958,260 | 8,234,336 | 9,048,633 | 1.098890 |
| 99,126 | 48,991,269 | 22,733,143 | 16,282,822 | 17,892,114 | 1.098834 |

The roughly 10% larger current page metadata matches the entry/root overhead seen in 072. No actual reclamation/pinned-reader behavior is tested. All retained bytes include migration and every subsequently published file; totals exactly match native staged bytes.

## Correctness and calibration

- ✅22 debug and 22 release tests, format and strict Clippy pass. Tests retain the 18 page/retry/source/error/corruption cases plus four CAT4 cycle/source/retry/recovery checks.
- ✅16 independent native-control fixture checks: eight valid complete histories match expected receipts/sources and eight deliberately invalid fixtures are rejected.
- ✅All 54 cases complete: 3,456 publications, 432 source intervals and 648 recoveries preserve exact original/new ID/digest/row/generation/source history. Old ordinary/source retries return original generations and conflicting content adds no files.
- ✅Independent Python directly decodes every file in six canonical seed/mode stores (875 files), checks every logical edit/root/page/delta/checkpoint, and matches every full-file SHA in all 6,420 fixtures to those validated equivalents. All recovery hashes/positions, stage totals, byte/sync counts, memory queries and balanced order pass. This is canonical decoding plus exact replica hashing, not direct JSON decoding of every duplicate.
- ❌All 4 goals pass ; 11 guards and 6 calibration checks fail. Candidate is rejected; no threshold was rounded, relaxed or changed.

Failed declared A/A metrics (interval 0.90–1.10):

- 126: ❌ max_ms.
- 50,126: ❌ p99_ms, max_ms.
- 99,126: ❌ total_ms, p99_ms, migration_ms.

Small maximum B/A 0.899250 narrowly misses 0.90 and remains failed. 50K p99/max fail; 99K total/p99/migration fail. Every raw observation remains visible in [paired results and fixed gates](benchmarks/receipt-cycles-073/model-audit.json), [frozen policy](benchmarks/receipt-cycles-073/policy.json), [cohort plan](benchmarks/receipt-cycles-073/cohort-policy.json), [case logs](benchmarks/receipt-cycles-073/model-results.json), [full file inventory](benchmarks/receipt-cycles-073/fixture-inventory.json) and [stage/reachability profile](benchmarks/receipt-cycles-073/stage-profile.json).

There are 18 publications above 500ms. The largest retained event is 20-r2-99000-baseline_a, publication 32, 2439.1840ms: sync_all observation 2380.8492ms (97.61%). This identifies the measured stage, not a physical-device/OS cause or power-loss guarantee. Aggregate stage fractions are not individual causal proof.

## Preservation, limits and next work

The first assembler stopped on an exact-source matcher, the next formatter caught Windows default-encoding corruption in a copied Unicode regression test, and the first native attempt failed strict lint after 22+22 passing tests. Every derivative/source/log/fixture is preserved. The fixes happened before policy/binary/cohort freezing; no test or gate was removed. The final build is SHA 54163abd769744e2b1bd8602bd7a87e1d6794fc92375fbe4d5fb133eb62df608.

Only duplicate 071 working frames were reclaimed to make disk space: 648 files, 4,478,367,888 logical bytes. Before native PowerShell removal of exactly work/perf-071/fixtures, every byte/hash/ZIP member and all 116 private server digests were freshly verified. The four complete original 071 ZIPs, inputs, raw logs, code/binary/policy/reports remain unchanged. [Exact plan](benchmarks/receipt-cycles-073/fixture-reclamation-plan.json) and [result](benchmarks/receipt-cycles-073/fixture-reclamation-result.json) preserve the evidence. Reproduce 071 by extracting its original four archives into a fresh directory. No 073 full store is reclaimed.

The next unimplemented hypothesis is a separately specified hybrid: cheap bounded deltas for normal commits, immutable pages only at checkpoint roots. That targets the measured p50/small-store overhead; neither its benefit nor engine safety is established. Read [design](benchmarks/receipt-cycles-073/DESIGN.md), [reproduction](benchmarks/receipt-cycles-073/REPRODUCE.md) and [next work](benchmarks/receipt-cycles-073/NEXT_WORK.md).

Seven controlled kills belong to previous 072 qualification, not new 073 kill tests. Current models do not qualify SQL/data segments, full old-format migration, exclusive engine ownership, actual compaction/pinned-reader/reclaim, service concurrency or physical power loss. DuckDB/PostgreSQL/other-engine standings are unchanged. No universal/Facebook-scale/production/PostgreSQL-replacement claim. Supported 0.3.16 and the frozen morning report remain unchanged; English only, this computer only, no deployment/messages to others.

Private complete development evidence:

- [kestrel-sql-development-073-receipt-cycle-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-073-receipt-cycle-evidence.zip).
- [kestrel-sql-development-073-receipt-cycle-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-073-receipt-cycle-evidence.zip.sha256).

All server digests match. All 116 older assets and 20 engine tags/releases remain unchanged. The ZIP contains the report before these upload-link paragraphs. No engine release/promotion.

The first post-publication verifier stopped on a stale `pre-072` manifest filename. Its [failure log](benchmarks/receipt-cycles-073-finalization/verification-first-failure.log) and [completion provenance](benchmarks/receipt-cycles-073-finalization/completion-provenance.json) are retained separately. The [completion runner](benchmarks/receipt-cycles-073-finalization/finalize_verification.py) verifies the original runner and frozen 073 manifest hashes, replaces exactly that filename in memory, then executes the complete original verifier. Run `python finalize_verification.py --verify <work/perf-073 absolute path>`. The published ZIP and its original script/report, frozen observations, policy, source and binary remain unchanged; no build or timed case was repeated. These finalization files and upload links are additive repository records after the ZIP was frozen.
